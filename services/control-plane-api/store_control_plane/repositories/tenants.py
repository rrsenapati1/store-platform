from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Branch, OwnerInvite, Tenant
from ..utils import new_id


class TenantRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_tenant(self, *, name: str, slug: str) -> Tenant:
        tenant = Tenant(id=new_id(), name=name, slug=slug, status="ACTIVE", onboarding_status="OWNER_INVITE_PENDING")
        self._session.add(tenant)
        await self._session.flush()
        return tenant

    async def list_tenants(self) -> list[Tenant]:
        statement = select(Tenant).order_by(Tenant.created_at.desc(), Tenant.id.desc())
        return list((await self._session.scalars(statement)).all())

    async def get_tenant(self, tenant_id: str) -> Tenant | None:
        statement = select(Tenant).where(Tenant.id == tenant_id)
        return await self._session.scalar(statement)

    async def create_owner_invite(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        invited_by_user_id: str,
    ) -> OwnerInvite:
        invite = OwnerInvite(
            id=new_id(),
            tenant_id=tenant_id,
            email=email.lower(),
            full_name=full_name,
            status="PENDING",
            invited_by_user_id=invited_by_user_id,
        )
        self._session.add(invite)
        await self._session.flush()
        return invite

    async def list_pending_owner_invites(self, email: str) -> list[OwnerInvite]:
        statement = select(OwnerInvite).where(OwnerInvite.email == email.lower(), OwnerInvite.status == "PENDING")
        return list((await self._session.scalars(statement)).all())

    async def accept_owner_invite(self, invite: OwnerInvite, *, accepted_by_user_id: str) -> OwnerInvite:
        invite.status = "ACCEPTED"
        invite.accepted_by_user_id = accepted_by_user_id
        await self._session.flush()
        return invite

    async def create_branch(
        self,
        *,
        tenant_id: str,
        name: str,
        code: str,
        gstin: str | None,
        timezone: str,
    ) -> Branch:
        branch = Branch(
            id=new_id(),
            tenant_id=tenant_id,
            name=name,
            code=code,
            gstin=gstin,
            timezone=timezone,
            status="ACTIVE",
        )
        self._session.add(branch)
        await self._session.flush()
        return branch

    async def list_branches(self, tenant_id: str) -> list[Branch]:
        statement = (
            select(Branch)
            .where(Branch.tenant_id == tenant_id)
            .order_by(Branch.created_at.asc(), Branch.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_branch(self, *, tenant_id: str, branch_id: str) -> Branch | None:
        statement = select(Branch).where(
            Branch.id == branch_id,
            Branch.tenant_id == tenant_id,
        )
        return await self._session.scalar(statement)
