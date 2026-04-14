from __future__ import annotations

from dataclasses import dataclass
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..repositories import AuditRepository, IdentityRepository, MembershipRepository, TenantRepository, WorkforceRepository
from ..utils import utc_now
from .commercial_access import CommercialAccessService
from .idp import IdentityClaims
from .rbac import capabilities_for_role


@dataclass(slots=True)
class ActorMembership:
    tenant_id: str
    role_name: str
    status: str
    branch_id: str | None = None

    @property
    def capabilities(self) -> tuple[str, ...]:
        return capabilities_for_role(self.role_name)


@dataclass(slots=True)
class ActorContext:
    user_id: str
    email: str
    full_name: str
    is_platform_admin: bool
    tenant_memberships: list[ActorMembership]
    branch_memberships: list[ActorMembership]


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings, identity_provider):
        self._session = session
        self._settings = settings
        self._identity_provider = identity_provider
        self._identity_repo = IdentityRepository(session)
        self._tenant_repo = TenantRepository(session)
        self._membership_repo = MembershipRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._audit_repo = AuditRepository(session)
        self._commercial_access = CommercialAccessService(session)

    async def exchange_oidc_token(self, token: str):
        claims = self._identity_provider.validate_token(token)
        user = await self._identity_repo.upsert_user(
            external_subject=claims.external_subject,
            email=claims.email,
            full_name=claims.full_name,
            provider=claims.provider,
        )
        if claims.email in self._settings.platform_admin_emails:
            await self._identity_repo.ensure_platform_admin(user.id)
        await self._accept_pending_owner_invites(user.id, claims)
        await self._membership_repo.activate_pending_memberships(email=claims.email, user_id=user.id)
        await self._workforce_repo.bind_profiles_for_user(email=claims.email, user_id=user.id, full_name=claims.full_name)
        session_record = await self._identity_repo.create_session(
            user_id=user.id,
            ttl_minutes=self._settings.session_ttl_minutes,
        )
        await self._session.commit()
        return session_record

    async def get_actor_context(self, token: str) -> ActorContext:
        session_record = await self._identity_repo.get_app_session(token)
        if session_record is None or session_record.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        user = await self._identity_repo.get_user_by_id(session_record.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        if user.provider == "store_desktop_activation":
            await self._assert_runtime_commercial_access(user_id=user.id)
        await self._identity_repo.touch_session(session_record)
        tenant_memberships = [
            ActorMembership(
                tenant_id=membership.tenant_id,
                role_name=membership.role_name,
                status=membership.status,
            )
            for membership in await self._membership_repo.list_active_tenant_memberships(user.id)
        ]
        branch_memberships = [
            ActorMembership(
                tenant_id=membership.tenant_id,
                branch_id=membership.branch_id,
                role_name=membership.role_name,
                status=membership.status,
            )
            for membership in await self._membership_repo.list_active_branch_memberships(user.id)
        ]
        is_platform_admin = await self._identity_repo.is_platform_admin(user.id)
        await self._session.commit()
        return ActorContext(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_platform_admin=is_platform_admin,
            tenant_memberships=tenant_memberships,
            branch_memberships=branch_memberships,
        )

    async def sign_out(self, token: str) -> None:
        await self._identity_repo.delete_session(token)
        await self._session.commit()

    async def refresh_session(self, token: str):
        session_record = await self._identity_repo.get_app_session(token)
        if session_record is None or session_record.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        user = await self._identity_repo.get_user_by_id(session_record.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        if user.provider == "store_desktop_activation":
            await self._assert_runtime_commercial_access(user_id=user.id)
        refreshed_session = await self._identity_repo.rotate_session(
            session_record=session_record,
            ttl_minutes=self._settings.session_ttl_minutes,
        )
        await self._session.commit()
        return refreshed_session

    async def _assert_runtime_commercial_access(self, *, user_id: str) -> None:
        tenant_memberships = await self._membership_repo.list_active_tenant_memberships(user_id)
        branch_memberships = await self._membership_repo.list_active_branch_memberships(user_id)
        scoped_tenant_ids = {
            membership.tenant_id
            for membership in [*tenant_memberships, *branch_memberships]
        }
        for tenant_id in scoped_tenant_ids:
            await self._commercial_access.assert_runtime_session_allowed(tenant_id=tenant_id)

    async def _accept_pending_owner_invites(self, user_id: str, claims: IdentityClaims) -> None:
        pending_invites = await self._tenant_repo.list_pending_owner_invites(claims.email)
        for invite in pending_invites:
            await self._tenant_repo.accept_owner_invite(invite, accepted_by_user_id=user_id)
            existing_membership = await self._membership_repo.get_matching_tenant_membership(
                tenant_id=invite.tenant_id,
                email=claims.email,
                role_name="tenant_owner",
            )
            if existing_membership is None:
                await self._membership_repo.create_tenant_membership(
                    tenant_id=invite.tenant_id,
                    email=claims.email,
                    full_name=claims.full_name,
                    role_name="tenant_owner",
                    status="ACTIVE",
                    user_id=user_id,
                )
            else:
                existing_membership.status = "ACTIVE"
                existing_membership.user_id = user_id
            await self._audit_repo.record(
                tenant_id=invite.tenant_id,
                branch_id=None,
                actor_user_id=user_id,
                action="owner_invite.accepted",
                entity_type="owner_invite",
                entity_id=invite.id,
                payload={"email": claims.email},
            )
        await self._session.flush()


def assert_platform_admin(actor: ActorContext) -> None:
    if actor.is_platform_admin:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin access required")


def assert_tenant_capability(actor: ActorContext, *, tenant_id: str, capability: str) -> None:
    if actor.is_platform_admin:
        return
    for membership in actor.tenant_memberships:
        if membership.tenant_id == tenant_id and capability in membership.capabilities:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant capability required")


def assert_branch_capability(actor: ActorContext, *, tenant_id: str, branch_id: str, capability: str) -> None:
    if actor.is_platform_admin:
        return
    for membership in actor.tenant_memberships:
        if membership.tenant_id == tenant_id and capability in membership.capabilities:
            return
    for membership in actor.branch_memberships:
        if membership.tenant_id == tenant_id and membership.branch_id == branch_id and capability in membership.capabilities:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch capability required")


def assert_branch_any_capability(actor: ActorContext, *, tenant_id: str, branch_id: str, capabilities: tuple[str, ...]) -> None:
    if actor.is_platform_admin:
        return
    for membership in actor.tenant_memberships:
        if membership.tenant_id == tenant_id and any(capability in membership.capabilities for capability in capabilities):
            return
    for membership in actor.branch_memberships:
        branch_matches = branch_id == "" or membership.branch_id == branch_id
        if membership.tenant_id == tenant_id and branch_matches and any(capability in membership.capabilities for capability in capabilities):
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Scoped capability required")


def branch_has_capability(actor: ActorContext, *, tenant_id: str, branch_id: str, capability: str) -> bool:
    if actor.is_platform_admin:
        return True
    for membership in actor.tenant_memberships:
        if membership.tenant_id == tenant_id and capability in membership.capabilities:
            return True
    for membership in actor.branch_memberships:
        if membership.tenant_id == tenant_id and membership.branch_id == branch_id and capability in membership.capabilities:
            return True
    return False
