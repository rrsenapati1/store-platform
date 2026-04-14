from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_current_actor, get_session, get_settings
from ..schemas import (
    BillingPlanCreateRequest,
    BillingPlanListResponse,
    BillingPlanResponse,
    OwnerInviteCreateRequest,
    OwnerInviteResponse,
    PlatformTenantListResponse,
    PlatformTenantRecord,
    TenantBillingOverrideRequest,
    TenantCreateRequest,
    TenantCreatedResponse,
    TenantLifecycleSummaryResponse,
)
from ..services import ActorContext, CommerceService, OnboardingService, assert_platform_admin

router = APIRouter(prefix="/v1/platform", tags=["platform"])


@router.post("/tenants", response_model=TenantCreatedResponse)
async def create_tenant(
    payload: TenantCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantCreatedResponse:
    assert_platform_admin(actor)
    service = OnboardingService(session, settings)
    tenant = await service.create_tenant(actor_user_id=actor.user_id, name=payload.name, slug=payload.slug)
    return TenantCreatedResponse.model_validate(tenant, from_attributes=True)


@router.get("/tenants", response_model=PlatformTenantListResponse)
async def list_tenants(
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> PlatformTenantListResponse:
    assert_platform_admin(actor)
    service = OnboardingService(session, settings)
    tenants = await service.list_tenants()
    return PlatformTenantListResponse(
        records=[
            PlatformTenantRecord(
                tenant_id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                status=tenant.status,
                onboarding_status=tenant.onboarding_status,
            )
            for tenant in tenants
        ]
    )


@router.post("/tenants/{tenant_id}/owner-invites", response_model=OwnerInviteResponse)
async def create_owner_invite(
    tenant_id: str,
    payload: OwnerInviteCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> OwnerInviteResponse:
    assert_platform_admin(actor)
    service = OnboardingService(session, settings)
    invite = await service.create_owner_invite(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        email=payload.email,
        full_name=payload.full_name,
    )
    return OwnerInviteResponse(
        id=invite.id,
        tenant_id=invite.tenant_id,
        email=invite.email,
        full_name=invite.full_name,
        status=invite.status,
    )


@router.get("/billing/plans", response_model=BillingPlanListResponse)
async def list_billing_plans(
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BillingPlanListResponse:
    assert_platform_admin(actor)
    service = CommerceService(session, settings)
    records = await service.list_billing_plans()
    return BillingPlanListResponse(records=[BillingPlanResponse(**record) for record in records])


@router.post("/billing/plans", response_model=BillingPlanResponse)
async def create_billing_plan(
    payload: BillingPlanCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BillingPlanResponse:
    assert_platform_admin(actor)
    service = CommerceService(session, settings)
    record = await service.create_billing_plan(**payload.model_dump())
    return BillingPlanResponse(**record)


@router.get("/tenants/{tenant_id}/billing-lifecycle", response_model=TenantLifecycleSummaryResponse)
async def get_tenant_billing_lifecycle(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantLifecycleSummaryResponse:
    assert_platform_admin(actor)
    service = CommerceService(session, settings)
    summary = await service.get_tenant_lifecycle_summary(tenant_id=tenant_id)
    return TenantLifecycleSummaryResponse.model_validate(summary)


@router.post("/tenants/{tenant_id}/billing/suspend", response_model=TenantLifecycleSummaryResponse)
async def suspend_tenant_billing(
    tenant_id: str,
    payload: dict[str, str],
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantLifecycleSummaryResponse:
    assert_platform_admin(actor)
    service = CommerceService(session, settings)
    summary = await service.suspend_tenant_commercial_access(
        tenant_id=tenant_id,
        reason=payload.get("reason", "Manual suspension"),
    )
    return TenantLifecycleSummaryResponse.model_validate(summary)


@router.post("/tenants/{tenant_id}/billing/reactivate", response_model=TenantLifecycleSummaryResponse)
async def reactivate_tenant_billing(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantLifecycleSummaryResponse:
    assert_platform_admin(actor)
    service = CommerceService(session, settings)
    summary = await service.reactivate_tenant_commercial_access(tenant_id=tenant_id)
    return TenantLifecycleSummaryResponse.model_validate(summary)


@router.post("/tenants/{tenant_id}/billing/overrides", response_model=TenantLifecycleSummaryResponse)
async def create_tenant_billing_override(
    tenant_id: str,
    payload: TenantBillingOverrideRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantLifecycleSummaryResponse:
    assert_platform_admin(actor)
    service = CommerceService(session, settings)
    summary = await service.create_billing_override(
        tenant_id=tenant_id,
        created_by_user_id=actor.user_id,
        grants_lifecycle_status=payload.grants_lifecycle_status,
        branch_limit_override=payload.branch_limit_override,
        device_limit_override=payload.device_limit_override,
        offline_runtime_hours_override=payload.offline_runtime_hours_override,
        feature_flags_override=payload.feature_flags_override,
        reason=payload.reason,
        expires_at=datetime.fromisoformat(payload.expires_at),
    )
    return TenantLifecycleSummaryResponse.model_validate(summary)
