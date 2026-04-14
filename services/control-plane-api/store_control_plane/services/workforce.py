from __future__ import annotations

from datetime import timedelta
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, IdentityRepository, MembershipRepository, TenantRepository, WorkforceRepository
from ..utils import utc_now
from .commercial_access import CommercialAccessService
from .sync_runtime_auth import hash_sync_access_secret

STORE_DESKTOP_ACTIVATION_TTL_MINUTES = 15
STORE_DESKTOP_OFFLINE_UNLOCK_TTL_HOURS = 24
DEFAULT_RUNTIME_PROFILE_BY_SURFACE = {
    "store_desktop": "desktop_spoke",
    "store_mobile": "mobile_store_spoke",
    "inventory_tablet": "inventory_tablet_spoke",
    "customer_display": "customer_display",
}


def build_device_claim_code(installation_id: str) -> str:
    normalized = "".join(character for character in installation_id.upper() if character.isalnum())
    suffix = normalized[-8:] if normalized else "UNBOUND00"
    return f"STORE-{suffix}"


def resolve_device_runtime_profile(
    *,
    session_surface: str,
    is_branch_hub: bool,
    runtime_profile: str | None = None,
) -> str:
    if runtime_profile:
        return runtime_profile
    if is_branch_hub:
        return "branch_hub"
    return DEFAULT_RUNTIME_PROFILE_BY_SURFACE.get(session_surface, "desktop_spoke")


def serialize_device_claim(claim, device) -> dict[str, object]:
    return {
        "id": claim.id,
        "tenant_id": claim.tenant_id,
        "branch_id": claim.branch_id,
        "installation_id": claim.installation_id,
        "claim_code": claim.claim_code,
        "runtime_kind": claim.runtime_kind,
        "hostname": claim.hostname,
        "operating_system": claim.operating_system,
        "architecture": claim.architecture,
        "app_version": claim.app_version,
        "status": claim.status,
        "approved_device_id": claim.approved_device_id,
        "approved_device_code": device.device_code if device is not None else None,
        "created_at": claim.created_at.isoformat(),
        "last_seen_at": claim.last_seen_at.isoformat() if claim.last_seen_at is not None else None,
        "approved_at": claim.approved_at.isoformat() if claim.approved_at is not None else None,
    }


def normalize_store_desktop_activation_code(code: str) -> str:
    normalized = "".join(character for character in code.upper().strip() if character.isalnum())
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activation code is required")
    return normalized


def hash_store_desktop_activation_code(code: str) -> str:
    normalized = normalize_store_desktop_activation_code(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_store_desktop_activation_code() -> str:
    token = secrets.token_hex(6).upper()
    return f"{token[:4]}-{token[4:8]}-{token[8:12]}"


def hash_store_desktop_local_auth_token(token: str) -> str:
    normalized = token.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local auth token is required")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_store_desktop_local_auth_token() -> str:
    return secrets.token_urlsafe(32)


def build_runtime_user_subject(*, session_surface: str, staff_profile_id: str) -> str:
    return f"{session_surface}-activation:{staff_profile_id}"


class WorkforceService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._membership_repo = MembershipRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._audit_repo = AuditRepository(session)
        self._identity_repo = IdentityRepository(session)
        self._commercial_access = CommercialAccessService(session)

    async def _resolve_runtime_user_for_profile(self, *, profile, synthetic_subject: str, provider: str):
        existing_user = await self._identity_repo.get_user_by_email(profile.email)
        if existing_user is not None and existing_user.external_subject != synthetic_subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Staff profile email is already bound to an interactive user",
            )

        runtime_user = await self._identity_repo.ensure_runtime_user(
            email=profile.email,
            full_name=profile.full_name,
            synthetic_subject=synthetic_subject,
            provider=provider,
        )
        await self._membership_repo.activate_pending_memberships(email=profile.email, user_id=runtime_user.id)
        await self._workforce_repo.bind_profiles_for_user(
            email=profile.email,
            user_id=runtime_user.id,
            full_name=profile.full_name,
        )
        return runtime_user

    async def _assert_runtime_branch_membership(self, *, runtime_user_id: str, device) -> None:
        active_branch_memberships = await self._membership_repo.list_active_branch_memberships(runtime_user_id)
        if not any(
            membership.tenant_id == device.tenant_id and membership.branch_id == device.branch_id
            for membership in active_branch_memberships
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Activated staff profile is not assigned to this branch",
            )

    async def create_staff_profile(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        email: str,
        full_name: str,
        phone_number: str | None,
        primary_branch_id: str | None,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if primary_branch_id is not None:
            branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=primary_branch_id)
            if branch is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        profile = await self._workforce_repo.upsert_staff_profile(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            primary_branch_id=primary_branch_id,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=primary_branch_id,
            actor_user_id=actor_user_id,
            action="staff_profile.upserted",
            entity_type="staff_profile",
            entity_id=profile.id,
            payload={"email": profile.email},
        )
        await self._session.commit()
        return profile

    async def list_staff_profiles(self, tenant_id: str) -> list[dict[str, object]]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        profiles = await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        tenant_memberships = await self._membership_repo.list_tenant_memberships_for_tenant(tenant_id)
        branch_memberships = await self._membership_repo.list_branch_memberships_for_tenant(tenant_id)

        records: list[dict[str, object]] = []
        for profile in profiles:
            role_names = {
                membership.role_name
                for membership in tenant_memberships
                if membership.invite_email == profile.email
            }
            branch_ids = {
                membership.branch_id
                for membership in branch_memberships
                if membership.invite_email == profile.email
            }
            role_names.update(
                membership.role_name
                for membership in branch_memberships
                if membership.invite_email == profile.email
            )
            records.append(
                {
                    "id": profile.id,
                    "tenant_id": profile.tenant_id,
                    "user_id": profile.user_id,
                    "email": profile.email,
                    "full_name": profile.full_name,
                    "phone_number": profile.phone_number,
                    "primary_branch_id": profile.primary_branch_id,
                    "status": profile.status,
                    "role_names": sorted(role_names),
                    "branch_ids": sorted(branch_ids),
                }
            )
        return records

    async def register_device(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        assigned_staff_profile_id: str | None,
        installation_id: str | None,
        device_name: str,
        device_code: str,
        session_surface: str,
        runtime_profile: str | None = None,
        is_branch_hub: bool = False,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if assigned_staff_profile_id is not None:
            profile = await self._workforce_repo.get_staff_profile_by_id(
                tenant_id=tenant_id,
                staff_profile_id=assigned_staff_profile_id,
            )
            if profile is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
        if is_branch_hub:
            existing_hub = await self._workforce_repo.get_branch_hub_device(tenant_id=tenant_id, branch_id=branch_id)
            if existing_hub is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch hub already registered")
        existing_device = await self._workforce_repo.get_device_registration_by_code(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_code=device_code,
        )
        if existing_device is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device code already registered")
        if installation_id is not None:
            existing_installation = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=installation_id,
            )
            if existing_installation is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Installation already bound")
        resolved_runtime_profile = resolve_device_runtime_profile(
            session_surface=session_surface,
            is_branch_hub=is_branch_hub,
            runtime_profile=runtime_profile,
        )
        sync_access_secret = secrets.token_urlsafe(24) if is_branch_hub else None
        device = await self._workforce_repo.create_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            assigned_staff_profile_id=assigned_staff_profile_id,
            installation_id=installation_id,
            device_name=device_name,
            device_code=device_code,
            session_surface=session_surface,
            runtime_profile=resolved_runtime_profile,
            is_branch_hub=is_branch_hub,
            sync_secret_hash=hash_sync_access_secret(sync_access_secret) if sync_access_secret else None,
            sync_secret_issued_at=utc_now() if sync_access_secret else None,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="device.registered",
            entity_type="device_registration",
            entity_id=device.id,
            payload={
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
                "is_branch_hub": device.is_branch_hub,
                "installation_id": device.installation_id,
            },
        )
        await self._session.commit()
        return {
            "id": device.id,
            "tenant_id": device.tenant_id,
            "branch_id": device.branch_id,
            "device_name": device.device_name,
            "device_code": device.device_code,
            "session_surface": device.session_surface,
            "runtime_profile": device.runtime_profile,
            "is_branch_hub": device.is_branch_hub,
            "status": device.status,
            "assigned_staff_profile_id": device.assigned_staff_profile_id,
            "installation_id": device.installation_id,
            "sync_access_secret": sync_access_secret,
        }

    async def list_branch_devices(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        devices = await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        profiles = {
            profile.id: profile
            for profile in await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        }
        return [
            {
                "id": device.id,
                "tenant_id": device.tenant_id,
                "branch_id": device.branch_id,
                "device_name": device.device_name,
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
                "is_branch_hub": device.is_branch_hub,
                "status": device.status,
                "assigned_staff_profile_id": device.assigned_staff_profile_id,
                "assigned_staff_full_name": profiles.get(device.assigned_staff_profile_id).full_name
                if device.assigned_staff_profile_id and profiles.get(device.assigned_staff_profile_id)
                else None,
                "installation_id": device.installation_id,
            }
            for device in devices
        ]

    async def resolve_runtime_device_claim(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        installation_id: str,
        runtime_kind: str,
        hostname: str | None,
        operating_system: str | None,
        architecture: str | None,
        app_version: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        claim_code = build_device_claim_code(installation_id)
        seen_at = utc_now()
        claim = await self._workforce_repo.get_device_claim_by_installation_id(
            tenant_id=tenant_id,
            branch_id=branch_id,
            installation_id=installation_id,
        )
        if claim is None:
            claim = await self._workforce_repo.create_device_claim(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=installation_id,
                claim_code=claim_code,
                runtime_kind=runtime_kind,
                hostname=hostname,
                operating_system=operating_system,
                architecture=architecture,
                app_version=app_version,
                seen_at=seen_at,
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="runtime_device_claim.created",
                entity_type="device_claim",
                entity_id=claim.id,
                payload={"claim_code": claim.claim_code, "runtime_kind": claim.runtime_kind},
            )
        else:
            await self._workforce_repo.touch_device_claim(
                claim=claim,
                runtime_kind=runtime_kind,
                hostname=hostname,
                operating_system=operating_system,
                architecture=architecture,
                app_version=app_version,
                seen_at=seen_at,
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="runtime_device_claim.seen",
                entity_type="device_claim",
                entity_id=claim.id,
                payload={"claim_code": claim.claim_code, "status": claim.status},
            )

        bound_device = None
        if claim.approved_device_id is not None:
            bound_device = await self._workforce_repo.get_device_registration_by_id(device_id=claim.approved_device_id)
        elif claim.status == "APPROVED":
            bound_device = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=installation_id,
            )
            if bound_device is not None:
                await self._workforce_repo.approve_device_claim(
                    claim=claim,
                    approved_device_id=bound_device.id,
                    approved_by_user_id=claim.approved_by_user_id or actor_user_id,
                    approved_at=claim.approved_at or seen_at,
                )

        await self._session.commit()
        return {
            "claim_id": claim.id,
            "claim_code": claim.claim_code,
            "status": claim.status,
            "bound_device_id": bound_device.id if bound_device is not None else None,
            "bound_device_name": bound_device.device_name if bound_device is not None else None,
            "bound_device_code": bound_device.device_code if bound_device is not None else None,
        }

    async def list_branch_device_claims(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        claims = await self._workforce_repo.list_branch_device_claims(tenant_id=tenant_id, branch_id=branch_id)
        devices = {
            device.id: device
            for device in await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        }
        return [serialize_device_claim(claim, devices.get(claim.approved_device_id)) for claim in claims]

    async def approve_device_claim(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        claim_id: str,
        actor_user_id: str,
        assigned_staff_profile_id: str | None,
        device_name: str,
        device_code: str,
        session_surface: str,
        runtime_profile: str | None = None,
        is_branch_hub: bool = False,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        claim = await self._workforce_repo.get_device_claim_by_id(
            tenant_id=tenant_id,
            branch_id=branch_id,
            claim_id=claim_id,
        )
        if claim is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device claim not found")
        if assigned_staff_profile_id is not None:
            profile = await self._workforce_repo.get_staff_profile_by_id(
                tenant_id=tenant_id,
                staff_profile_id=assigned_staff_profile_id,
            )
            if profile is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

        device = None
        sync_access_secret: str | None = None
        if claim.approved_device_id is not None:
            device = await self._workforce_repo.get_device_registration_by_id(device_id=claim.approved_device_id)
        if device is None:
            device = await self._workforce_repo.get_device_registration_by_installation_id(
                tenant_id=tenant_id,
                branch_id=branch_id,
                installation_id=claim.installation_id,
            )
        if is_branch_hub:
            existing_hub = await self._workforce_repo.get_branch_hub_device(tenant_id=tenant_id, branch_id=branch_id)
            if existing_hub is not None and (device is None or existing_hub.id != device.id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch hub already registered")
            if device is not None and not device.is_branch_hub:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Existing approved device is not registered as branch hub",
                )
        if device is None:
            existing_code = await self._workforce_repo.get_device_registration_by_code(
                tenant_id=tenant_id,
                branch_id=branch_id,
                device_code=device_code,
            )
            if existing_code is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device code already registered")
            resolved_runtime_profile = resolve_device_runtime_profile(
                session_surface=session_surface,
                is_branch_hub=is_branch_hub,
                runtime_profile=runtime_profile,
            )
            sync_access_secret = secrets.token_urlsafe(24) if is_branch_hub else None
            device = await self._workforce_repo.create_device_registration(
                tenant_id=tenant_id,
                branch_id=branch_id,
                assigned_staff_profile_id=assigned_staff_profile_id,
                installation_id=claim.installation_id,
                device_name=device_name,
                device_code=device_code,
                session_surface=session_surface,
                runtime_profile=resolved_runtime_profile,
                is_branch_hub=is_branch_hub,
                sync_secret_hash=hash_sync_access_secret(sync_access_secret) if sync_access_secret else None,
                sync_secret_issued_at=utc_now() if sync_access_secret else None,
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=actor_user_id,
                action="device.registered",
                entity_type="device_registration",
                entity_id=device.id,
                payload={
                    "device_code": device.device_code,
                    "session_surface": device.session_surface,
                    "runtime_profile": device.runtime_profile,
                    "is_branch_hub": device.is_branch_hub,
                    "installation_id": device.installation_id,
                    "approved_from_claim": claim.id,
                },
            )

        approved_at = utc_now()
        await self._workforce_repo.approve_device_claim(
            claim=claim,
            approved_device_id=device.id,
            approved_by_user_id=actor_user_id,
            approved_at=approved_at,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="runtime_device_claim.approved",
            entity_type="device_claim",
            entity_id=claim.id,
            payload={"claim_code": claim.claim_code, "device_id": device.id},
        )
        await self._session.commit()
        return {
            "claim": serialize_device_claim(claim, device),
            "device": {
                "id": device.id,
                "tenant_id": device.tenant_id,
                "branch_id": device.branch_id,
                "device_name": device.device_name,
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
                "is_branch_hub": device.is_branch_hub,
                "status": device.status,
                "assigned_staff_profile_id": device.assigned_staff_profile_id,
                "installation_id": device.installation_id,
                "sync_access_secret": sync_access_secret,
            },
        }

    async def issue_store_desktop_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
        )
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.status != "ACTIVE" or device.session_surface != "store_desktop" or not device.installation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved packaged store desktop device required",
            )
        await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)
        if not device.assigned_staff_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned staff profile required before issuing desktop activation",
            )

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=device.assigned_staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

        await self._workforce_repo.supersede_store_desktop_activations(device_id=device.id)
        activation_version = await self._workforce_repo.get_next_store_desktop_activation_version(device_id=device.id)
        activation_code = build_store_desktop_activation_code()
        activation = await self._workforce_repo.create_store_desktop_activation(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device.id,
            staff_profile_id=profile.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
            activation_version=activation_version,
            issued_by_user_id=actor_user_id,
            expires_at=utc_now() + timedelta(minutes=STORE_DESKTOP_ACTIVATION_TTL_MINUTES),
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="device.desktop_activation.issued",
            entity_type="store_desktop_activation",
            entity_id=activation.id,
            payload={"device_id": device.id, "staff_profile_id": profile.id},
        )
        await self._session.commit()
        return {
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "activation_code": activation_code,
            "status": activation.status,
            "expires_at": activation.expires_at.isoformat(),
        }

    async def issue_runtime_activation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
        )
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.status != "ACTIVE" or device.session_surface == "store_desktop" or not device.installation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved non-desktop runtime device required",
            )
        await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)
        if not device.assigned_staff_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned staff profile required before issuing runtime activation",
            )

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=tenant_id,
            staff_profile_id=device.assigned_staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

        await self._workforce_repo.supersede_runtime_device_activations(device_id=device.id)
        activation_version = await self._workforce_repo.get_next_runtime_device_activation_version(device_id=device.id)
        activation_code = build_store_desktop_activation_code()
        activation = await self._workforce_repo.create_runtime_device_activation(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device.id,
            staff_profile_id=profile.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
            activation_version=activation_version,
            issued_by_user_id=actor_user_id,
            expires_at=utc_now() + timedelta(minutes=STORE_DESKTOP_ACTIVATION_TTL_MINUTES),
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="device.runtime_activation.issued",
            entity_type="runtime_activation",
            entity_id=activation.id,
            payload={
                "device_id": device.id,
                "staff_profile_id": profile.id,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
            },
        )
        await self._session.commit()
        return {
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "activation_code": activation_code,
            "status": activation.status,
            "expires_at": activation.expires_at.isoformat(),
            "runtime_profile": device.runtime_profile,
            "session_surface": device.session_surface,
        }

    async def redeem_store_desktop_activation(
        self,
        *,
        installation_id: str,
        activation_code: str,
        session_ttl_minutes: int,
    ) -> dict[str, object]:
        device = await self._workforce_repo.get_device_registration_by_installation_id_global(
            installation_id=installation_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface != "store_desktop":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Desktop activation is invalid")
        access = await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)

        activation = await self._workforce_repo.get_store_desktop_activation(
            device_id=device.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
        )
        if activation is None or activation.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Desktop activation is invalid")

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=device.tenant_id,
            staff_profile_id=activation.staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Desktop activation is invalid")
        runtime_user = await self._resolve_runtime_user_for_profile(
            profile=profile,
            synthetic_subject=build_runtime_user_subject(
                session_surface=device.session_surface,
                staff_profile_id=profile.id,
            ),
            provider=f"{device.session_surface}_activation",
        )
        await self._assert_runtime_branch_membership(runtime_user_id=runtime_user.id, device=device)

        redeemed_at = utc_now()
        local_auth_token = build_store_desktop_local_auth_token()
        offline_hours = self._commercial_access.resolve_offline_runtime_hours(
            access=access,
            fallback_hours=STORE_DESKTOP_OFFLINE_UNLOCK_TTL_HOURS,
        )
        offline_valid_until = redeemed_at + timedelta(hours=offline_hours)
        await self._workforce_repo.redeem_store_desktop_activation(
            activation=activation,
            local_auth_token_hash=hash_store_desktop_local_auth_token(local_auth_token),
            redeemed_at=redeemed_at,
            offline_valid_until=offline_valid_until,
        )
        session_record = await self._identity_repo.create_session(
            user_id=runtime_user.id,
            ttl_minutes=session_ttl_minutes,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=runtime_user.id,
            action="device.desktop_activation.redeemed",
            entity_type="store_desktop_activation",
            entity_id=activation.id,
            payload={"device_id": device.id, "staff_profile_id": profile.id},
        )
        await self._session.commit()
        return {
            "access_token": session_record.token,
            "token_type": "Bearer",
            "expires_at": session_record.expires_at.isoformat(),
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "local_auth_token": local_auth_token,
            "offline_valid_until": offline_valid_until.isoformat(),
            "activation_version": activation.activation_version,
        }

    async def redeem_runtime_activation(
        self,
        *,
        installation_id: str,
        activation_code: str,
        session_ttl_minutes: int,
    ) -> dict[str, object]:
        device = await self._workforce_repo.get_device_registration_by_installation_id_global(
            installation_id=installation_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface == "store_desktop":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime activation is invalid")
        await self._commercial_access.assert_runtime_activation_allowed(tenant_id=device.tenant_id)

        activation = await self._workforce_repo.get_runtime_device_activation(
            device_id=device.id,
            activation_code_hash=hash_store_desktop_activation_code(activation_code),
        )
        if activation is None or activation.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime activation is invalid")

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=device.tenant_id,
            staff_profile_id=activation.staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime activation is invalid")
        runtime_user = await self._resolve_runtime_user_for_profile(
            profile=profile,
            synthetic_subject=build_runtime_user_subject(
                session_surface=device.session_surface,
                staff_profile_id=profile.id,
            ),
            provider=f"{device.session_surface}_activation",
        )
        await self._assert_runtime_branch_membership(runtime_user_id=runtime_user.id, device=device)

        redeemed_at = utc_now()
        session_record = await self._identity_repo.create_session(
            user_id=runtime_user.id,
            ttl_minutes=session_ttl_minutes,
        )
        activation.status = "ACTIVE"
        activation.redeemed_at = redeemed_at
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=runtime_user.id,
            action="device.runtime_activation.redeemed",
            entity_type="runtime_activation",
            entity_id=activation.id,
            payload={
                "device_id": device.id,
                "staff_profile_id": profile.id,
                "session_surface": device.session_surface,
                "runtime_profile": device.runtime_profile,
            },
        )
        await self._session.commit()
        return {
            "access_token": session_record.token,
            "token_type": "Bearer",
            "expires_at": session_record.expires_at.isoformat(),
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "runtime_profile": device.runtime_profile,
            "session_surface": device.session_surface,
        }

    async def unlock_store_desktop_runtime(
        self,
        *,
        installation_id: str,
        local_auth_token: str,
        session_ttl_minutes: int,
    ) -> dict[str, object]:
        device = await self._workforce_repo.get_device_registration_by_installation_id_global(
            installation_id=installation_id,
        )
        if device is None or device.status != "ACTIVE" or device.session_surface != "store_desktop":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Store desktop unlock is invalid")
        access = await self._commercial_access.assert_runtime_session_allowed(tenant_id=device.tenant_id)

        activation = await self._workforce_repo.get_active_store_desktop_activation_by_local_auth_token(
            device_id=device.id,
            local_auth_token_hash=hash_store_desktop_local_auth_token(local_auth_token),
        )
        if activation is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Store desktop unlock is invalid")

        profile = await self._workforce_repo.get_staff_profile_by_id(
            tenant_id=device.tenant_id,
            staff_profile_id=activation.staff_profile_id,
        )
        if profile is None or profile.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Store desktop unlock is invalid")

        runtime_user = await self._resolve_runtime_user_for_profile(
            profile=profile,
            synthetic_subject=build_runtime_user_subject(
                session_surface=device.session_surface,
                staff_profile_id=profile.id,
            ),
            provider=f"{device.session_surface}_activation",
        )
        await self._assert_runtime_branch_membership(runtime_user_id=runtime_user.id, device=device)

        unlocked_at = utc_now()
        offline_hours = self._commercial_access.resolve_offline_runtime_hours(
            access=access,
            fallback_hours=STORE_DESKTOP_OFFLINE_UNLOCK_TTL_HOURS,
        )
        offline_valid_until = unlocked_at + timedelta(hours=offline_hours)
        await self._workforce_repo.touch_store_desktop_activation_unlock(
            activation=activation,
            unlocked_at=unlocked_at,
            offline_valid_until=offline_valid_until,
        )
        session_record = await self._identity_repo.create_session(
            user_id=runtime_user.id,
            ttl_minutes=session_ttl_minutes,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=runtime_user.id,
            action="device.desktop_activation.unlocked",
            entity_type="store_desktop_activation",
            entity_id=activation.id,
            payload={"device_id": device.id, "staff_profile_id": profile.id},
        )
        await self._session.commit()
        return {
            "access_token": session_record.token,
            "token_type": "Bearer",
            "expires_at": session_record.expires_at.isoformat(),
            "device_id": device.id,
            "staff_profile_id": profile.id,
            "local_auth_token": local_auth_token,
            "offline_valid_until": offline_valid_until.isoformat(),
            "activation_version": activation.activation_version,
        }
