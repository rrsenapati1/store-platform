from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_current_actor, get_session, get_settings
from ..schemas import AuditListResponse, AuditRecord, BranchCreateRequest, BranchListResponse, BranchMembershipCreateRequest, BranchRecord, BranchResponse, MembershipResponse, TenantMembershipCreateRequest, TenantSummaryResponse
from ..services import ActorContext, OnboardingService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])


@router.get("/{tenant_id}", response_model=TenantSummaryResponse)
async def get_tenant_summary(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantSummaryResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id="", capabilities=("tenant.manage", "sales.bill"))
    service = OnboardingService(session, settings)
    tenant = await service.get_tenant_summary(tenant_id)
    return TenantSummaryResponse.model_validate(tenant, from_attributes=True)


@router.post("/{tenant_id}/branches", response_model=BranchResponse)
async def create_branch(
    tenant_id: str,
    payload: BranchCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BranchResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="branch.manage")
    service = OnboardingService(session, settings)
    branch = await service.create_branch(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        name=payload.name,
        code=payload.code,
        gstin=payload.gstin,
        timezone=payload.timezone,
    )
    return BranchResponse.model_validate(branch, from_attributes=True)


@router.get("/{tenant_id}/branches", response_model=BranchListResponse)
async def list_branches(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BranchListResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id="", capabilities=("branch.manage", "sales.bill"))
    service = OnboardingService(session, settings)
    branches = await service.list_branches(tenant_id)
    return BranchListResponse(
        records=[
            BranchRecord(
                branch_id=branch.id,
                tenant_id=branch.tenant_id,
                name=branch.name,
                code=branch.code,
                gstin=branch.gstin,
                status=branch.status,
            )
            for branch in branches
        ]
    )


@router.post("/{tenant_id}/memberships", response_model=MembershipResponse)
async def create_tenant_membership(
    tenant_id: str,
    payload: TenantMembershipCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MembershipResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="staff.manage")
    service = OnboardingService(session, settings)
    membership = await service.assign_tenant_membership(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        email=payload.email,
        full_name=payload.full_name,
        role_name=payload.role_name,
    )
    return MembershipResponse(
        id=membership.id,
        tenant_id=membership.tenant_id,
        email=membership.invite_email,
        full_name=membership.full_name,
        role_name=membership.role_name,
        status=membership.status,
    )


@router.post("/{tenant_id}/branches/{branch_id}/memberships", response_model=MembershipResponse)
async def create_branch_membership(
    tenant_id: str,
    branch_id: str,
    payload: BranchMembershipCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MembershipResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="staff.manage")
    service = OnboardingService(session, settings)
    membership = await service.assign_branch_membership(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        email=payload.email,
        full_name=payload.full_name,
        role_name=payload.role_name,
    )
    return MembershipResponse(
        id=membership.id,
        tenant_id=membership.tenant_id,
        branch_id=membership.branch_id,
        email=membership.invite_email,
        full_name=membership.full_name,
        role_name=membership.role_name,
        status=membership.status,
    )


@router.get("/{tenant_id}/audit-events", response_model=AuditListResponse)
async def list_audit_events(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuditListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="audit.view")
    service = OnboardingService(session, settings)
    events = await service.list_audit_events(tenant_id)
    return AuditListResponse(
        records=[
            AuditRecord(
                id=event.id,
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                tenant_id=event.tenant_id,
                branch_id=event.branch_id,
                created_at=event.created_at,
                payload=event.payload,
            )
            for event in events
        ]
    )
