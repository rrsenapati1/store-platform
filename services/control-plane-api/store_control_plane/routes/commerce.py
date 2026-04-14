from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_current_actor, get_session, get_settings
from ..schemas import (
    SubscriptionBootstrapRequest,
    SubscriptionBootstrapResponse,
    SubscriptionWebhookResponse,
    TenantLifecycleSummaryResponse,
)
from ..services import ActorContext, CommerceService, assert_tenant_capability

router = APIRouter(tags=["commerce"])


@router.get("/v1/tenants/{tenant_id}/billing/lifecycle", response_model=TenantLifecycleSummaryResponse)
async def get_owner_billing_lifecycle(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TenantLifecycleSummaryResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = CommerceService(session, settings)
    summary = await service.get_tenant_lifecycle_summary(tenant_id=tenant_id)
    return TenantLifecycleSummaryResponse.model_validate(summary)


@router.post("/v1/tenants/{tenant_id}/billing/subscription-bootstrap", response_model=SubscriptionBootstrapResponse)
async def bootstrap_tenant_subscription(
    tenant_id: str,
    payload: SubscriptionBootstrapRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SubscriptionBootstrapResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="tenant.manage")
    service = CommerceService(session, settings)
    checkout = await service.bootstrap_subscription_checkout(tenant_id=tenant_id, provider_name=payload.provider_name)
    return SubscriptionBootstrapResponse(**checkout)


@router.post("/v1/billing/webhooks/{provider_name}", response_model=SubscriptionWebhookResponse)
async def ingest_subscription_webhook(
    provider_name: str,
    payload: dict[str, object],
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SubscriptionWebhookResponse:
    service = CommerceService(session, settings)
    result = await service.handle_provider_webhook(provider_name=provider_name, payload=payload)
    return SubscriptionWebhookResponse(**result)
