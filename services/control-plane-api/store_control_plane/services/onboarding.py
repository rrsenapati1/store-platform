from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, MembershipRepository, TenantRepository, WorkforceRepository


class OnboardingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._membership_repo = MembershipRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_tenant(self, *, actor_user_id: str, name: str, slug: str):
        tenant = await self._tenant_repo.create_tenant(name=name, slug=slug)
        await self._audit_repo.record(
            tenant_id=tenant.id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="tenant.created",
            entity_type="tenant",
            entity_id=tenant.id,
            payload={"name": name, "slug": slug},
        )
        await self._session.commit()
        return tenant

    async def list_tenants(self):
        return await self._tenant_repo.list_tenants()

    async def create_owner_invite(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        email: str,
        full_name: str,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        invite = await self._tenant_repo.create_owner_invite(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            invited_by_user_id=actor_user_id,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="owner_invite.created",
            entity_type="owner_invite",
            entity_id=invite.id,
            payload={"email": invite.email},
        )
        await self._session.commit()
        return invite

    async def get_tenant_summary(self, tenant_id: str):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return tenant

    async def create_branch(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        name: str,
        code: str,
        gstin: str | None,
        timezone: str,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        branch = await self._tenant_repo.create_branch(
            tenant_id=tenant_id,
            name=name,
            code=code,
            gstin=gstin,
            timezone=timezone,
        )
        tenant.onboarding_status = "BRANCH_READY"
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch.id,
            actor_user_id=actor_user_id,
            action="branch.created",
            entity_type="branch",
            entity_id=branch.id,
            payload={"name": branch.name, "code": branch.code},
        )
        await self._session.commit()
        return branch

    async def list_branches(self, tenant_id: str):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return await self._tenant_repo.list_branches(tenant_id)

    async def assign_tenant_membership(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        email: str,
        full_name: str,
        role_name: str,
    ):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        membership = await self._membership_repo.create_tenant_membership(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            role_name=role_name,
            status="PENDING",
        )
        await self._workforce_repo.upsert_staff_profile(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=None,
            actor_user_id=actor_user_id,
            action="tenant_membership.assigned",
            entity_type="tenant_membership",
            entity_id=membership.id,
            payload={"email": membership.invite_email, "role_name": membership.role_name},
        )
        await self._session.commit()
        return membership

    async def assign_branch_membership(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        email: str,
        full_name: str,
        role_name: str,
    ):
        branches = await self._tenant_repo.list_branches(tenant_id)
        branch = next((item for item in branches if item.id == branch_id), None)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        membership = await self._membership_repo.create_branch_membership(
            tenant_id=tenant_id,
            branch_id=branch_id,
            email=email,
            full_name=full_name,
            role_name=role_name,
            status="PENDING",
        )
        await self._workforce_repo.upsert_staff_profile(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            primary_branch_id=branch_id,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="branch_membership.assigned",
            entity_type="branch_membership",
            entity_id=membership.id,
            payload={"email": membership.invite_email, "role_name": membership.role_name},
        )
        await self._session.commit()
        return membership

    async def list_audit_events(self, tenant_id: str):
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return await self._audit_repo.list_for_tenant(tenant_id)
