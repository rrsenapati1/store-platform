from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import (
    PromotionCampaignCreateRequest,
    PromotionCampaignListResponse,
    PromotionCampaignResponse,
    PromotionCampaignUpdateRequest,
    PromotionCodeCreateRequest,
    PromotionCodeResponse,
)
from ..services import ActorContext, PromotionService, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["promotions"])


@router.get("/{tenant_id}/promotion-campaigns", response_model=PromotionCampaignListResponse)
async def list_promotion_campaigns(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCampaignListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    records = await service.list_campaigns(tenant_id=tenant_id)
    return PromotionCampaignListResponse(**records)


@router.post("/{tenant_id}/promotion-campaigns", response_model=PromotionCampaignResponse)
async def create_promotion_campaign(
    tenant_id: str,
    payload: PromotionCampaignCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCampaignResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    record = await service.create_campaign(tenant_id=tenant_id, **payload.model_dump())
    await session.commit()
    return PromotionCampaignResponse(**record)


@router.get("/{tenant_id}/promotion-campaigns/{campaign_id}", response_model=PromotionCampaignResponse)
async def get_promotion_campaign(
    tenant_id: str,
    campaign_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCampaignResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    record = await service.get_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
    return PromotionCampaignResponse(**record)


@router.patch("/{tenant_id}/promotion-campaigns/{campaign_id}", response_model=PromotionCampaignResponse)
async def update_promotion_campaign(
    tenant_id: str,
    campaign_id: str,
    payload: PromotionCampaignUpdateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCampaignResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    record = await service.update_campaign(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        updates=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return PromotionCampaignResponse(**record)


@router.post("/{tenant_id}/promotion-campaigns/{campaign_id}/codes", response_model=PromotionCodeResponse)
async def create_promotion_code(
    tenant_id: str,
    campaign_id: str,
    payload: PromotionCodeCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCodeResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    record = await service.create_code(tenant_id=tenant_id, campaign_id=campaign_id, **payload.model_dump())
    await session.commit()
    return PromotionCodeResponse(**record)


@router.post("/{tenant_id}/promotion-campaigns/{campaign_id}/disable", response_model=PromotionCampaignResponse)
async def disable_promotion_campaign(
    tenant_id: str,
    campaign_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCampaignResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    record = await service.disable_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
    await session.commit()
    return PromotionCampaignResponse(**record)


@router.post("/{tenant_id}/promotion-campaigns/{campaign_id}/reactivate", response_model=PromotionCampaignResponse)
async def reactivate_promotion_campaign(
    tenant_id: str,
    campaign_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PromotionCampaignResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = PromotionService(session)
    record = await service.reactivate_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
    await session.commit()
    return PromotionCampaignResponse(**record)
