from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import OwnerInviteCreateRequest, OwnerInviteResponse, PlatformTenantListResponse, PlatformTenantRecord, TenantCreateRequest, TenantCreatedResponse
from ..services import ActorContext, OnboardingService, assert_platform_admin

router = APIRouter(prefix="/v1/platform", tags=["platform"])


@router.post("/tenants", response_model=TenantCreatedResponse)
async def create_tenant(
    payload: TenantCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> TenantCreatedResponse:
    assert_platform_admin(actor)
    service = OnboardingService(session)
    tenant = await service.create_tenant(actor_user_id=actor.user_id, name=payload.name, slug=payload.slug)
    return TenantCreatedResponse.model_validate(tenant, from_attributes=True)


@router.get("/tenants", response_model=PlatformTenantListResponse)
async def list_tenants(
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PlatformTenantListResponse:
    assert_platform_admin(actor)
    service = OnboardingService(session)
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
) -> OwnerInviteResponse:
    assert_platform_admin(actor)
    service = OnboardingService(session)
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
