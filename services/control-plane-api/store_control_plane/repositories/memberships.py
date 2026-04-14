from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BranchMembership, TenantMembership
from ..utils import new_id


class MembershipRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_tenant_membership(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        role_name: str,
        status: str,
        user_id: str | None = None,
    ) -> TenantMembership:
        membership = TenantMembership(
            id=new_id(),
            tenant_id=tenant_id,
            user_id=user_id,
            invite_email=email.lower(),
            full_name=full_name,
            role_name=role_name,
            status=status,
        )
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def create_branch_membership(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        email: str,
        full_name: str,
        role_name: str,
        status: str,
        user_id: str | None = None,
    ) -> BranchMembership:
        membership = BranchMembership(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user_id,
            invite_email=email.lower(),
            full_name=full_name,
            role_name=role_name,
            status=status,
        )
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def get_matching_tenant_membership(
        self,
        *,
        tenant_id: str,
        email: str,
        role_name: str,
    ) -> TenantMembership | None:
        statement = select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.invite_email == email.lower(),
            TenantMembership.role_name == role_name,
        )
        return await self._session.scalar(statement)

    async def list_active_tenant_memberships(self, user_id: str) -> list[TenantMembership]:
        statement = (
            select(TenantMembership)
            .where(TenantMembership.user_id == user_id, TenantMembership.status == "ACTIVE")
            .order_by(TenantMembership.created_at.asc(), TenantMembership.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_active_branch_memberships(self, user_id: str) -> list[BranchMembership]:
        statement = (
            select(BranchMembership)
            .where(BranchMembership.user_id == user_id, BranchMembership.status == "ACTIVE")
            .order_by(BranchMembership.created_at.asc(), BranchMembership.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_tenant_memberships_for_tenant(self, tenant_id: str) -> list[TenantMembership]:
        statement = (
            select(TenantMembership)
            .where(TenantMembership.tenant_id == tenant_id)
            .order_by(TenantMembership.created_at.asc(), TenantMembership.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_branch_memberships_for_tenant(self, tenant_id: str) -> list[BranchMembership]:
        statement = (
            select(BranchMembership)
            .where(BranchMembership.tenant_id == tenant_id)
            .order_by(BranchMembership.created_at.asc(), BranchMembership.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_pending_tenant_memberships(self, email: str) -> list[TenantMembership]:
        statement = select(TenantMembership).where(
            TenantMembership.invite_email == email.lower(),
            TenantMembership.status == "PENDING",
        )
        return list((await self._session.scalars(statement)).all())

    async def list_pending_branch_memberships(self, email: str) -> list[BranchMembership]:
        statement = select(BranchMembership).where(
            BranchMembership.invite_email == email.lower(),
            BranchMembership.status == "PENDING",
        )
        return list((await self._session.scalars(statement)).all())

    async def activate_pending_memberships(self, *, email: str, user_id: str) -> None:
        for membership in await self.list_pending_tenant_memberships(email):
            membership.user_id = user_id
            membership.status = "ACTIVE"
        for membership in await self.list_pending_branch_memberships(email):
            membership.user_id = user_id
            membership.status = "ACTIVE"
        await self._session.flush()
