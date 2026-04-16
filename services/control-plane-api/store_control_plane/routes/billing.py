from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import (
    CheckoutPaymentSessionCreateRequest,
    CheckoutPaymentSessionListResponse,
    CheckoutPaymentSessionResponse,
    CheckoutPaymentWebhookResponse,
    RefundApprovalRequest,
    SaleCreateRequest,
    SaleListResponse,
    SaleRecord,
    SaleResponse,
    SaleReturnCreateRequest,
    SaleReturnListResponse,
    SaleReturnRecord,
    SaleReturnResponse,
)
from ..services import (
    ActorContext,
    BillingService,
    CheckoutPaymentsService,
    assert_branch_any_capability,
    assert_branch_capability,
    branch_has_capability,
)

router = APIRouter(tags=["billing"])
branch_router = APIRouter(prefix="/v1/tenants", tags=["billing"])
webhook_router = APIRouter(prefix="/v1/billing", tags=["billing"])


@branch_router.post("/{tenant_id}/branches/{branch_id}/sales", response_model=SaleResponse)
async def create_sale(
    tenant_id: str,
    branch_id: str,
    payload: SaleCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SaleResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = BillingService(session)
    sale = await service.create_sale(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        customer_profile_id=payload.customer_profile_id,
        customer_name=payload.customer_name,
        customer_gstin=payload.customer_gstin,
        payment_method=payload.payment_method,
        lines=[line.model_dump() for line in payload.lines],
    )
    return SaleResponse(**sale)


@branch_router.post("/{tenant_id}/branches/{branch_id}/checkout-payment-sessions", response_model=CheckoutPaymentSessionResponse)
async def create_checkout_payment_session(
    tenant_id: str,
    branch_id: str,
    payload: CheckoutPaymentSessionCreateRequest,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_session = await service.create_checkout_payment_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        provider_name=payload.provider_name,
        payment_method=payload.payment_method,
        handoff_surface=payload.handoff_surface,
        provider_payment_mode=payload.provider_payment_mode,
        customer_profile_id=payload.customer_profile_id,
        customer_name=payload.customer_name,
        customer_gstin=payload.customer_gstin,
        lines=[line.model_dump() for line in payload.lines],
    )
    return CheckoutPaymentSessionResponse(**checkout_payment_session)


@branch_router.get(
    "/{tenant_id}/branches/{branch_id}/checkout-payment-sessions",
    response_model=CheckoutPaymentSessionListResponse,
)
async def list_checkout_payment_sessions(
    tenant_id: str,
    branch_id: str,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionListResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_sessions = await service.list_checkout_payment_sessions(
        tenant_id=tenant_id,
        branch_id=branch_id,
    )
    return CheckoutPaymentSessionListResponse(
        records=[CheckoutPaymentSessionResponse(**record) for record in checkout_payment_sessions]
    )


@branch_router.get(
    "/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{checkout_payment_session_id}",
    response_model=CheckoutPaymentSessionResponse,
)
async def get_checkout_payment_session(
    tenant_id: str,
    branch_id: str,
    checkout_payment_session_id: str,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_session = await service.get_checkout_payment_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        checkout_payment_session_id=checkout_payment_session_id,
    )
    return CheckoutPaymentSessionResponse(**checkout_payment_session)


@branch_router.post(
    "/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{checkout_payment_session_id}/cancel",
    response_model=CheckoutPaymentSessionResponse,
)
async def cancel_checkout_payment_session(
    tenant_id: str,
    branch_id: str,
    checkout_payment_session_id: str,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_session = await service.cancel_checkout_payment_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        checkout_payment_session_id=checkout_payment_session_id,
        actor_user_id=actor.user_id,
    )
    return CheckoutPaymentSessionResponse(**checkout_payment_session)


@branch_router.post(
    "/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{checkout_payment_session_id}/refresh",
    response_model=CheckoutPaymentSessionResponse,
)
async def refresh_checkout_payment_session(
    tenant_id: str,
    branch_id: str,
    checkout_payment_session_id: str,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_session = await service.refresh_checkout_payment_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        checkout_payment_session_id=checkout_payment_session_id,
        actor_user_id=actor.user_id,
    )
    return CheckoutPaymentSessionResponse(**checkout_payment_session)


@branch_router.post(
    "/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{checkout_payment_session_id}/finalize",
    response_model=CheckoutPaymentSessionResponse,
)
async def finalize_checkout_payment_session(
    tenant_id: str,
    branch_id: str,
    checkout_payment_session_id: str,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_session = await service.finalize_checkout_payment_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        checkout_payment_session_id=checkout_payment_session_id,
        actor_user_id=actor.user_id,
    )
    return CheckoutPaymentSessionResponse(**checkout_payment_session)


@branch_router.post(
    "/{tenant_id}/branches/{branch_id}/checkout-payment-sessions/{checkout_payment_session_id}/retry",
    response_model=CheckoutPaymentSessionResponse,
)
async def retry_checkout_payment_session(
    tenant_id: str,
    branch_id: str,
    checkout_payment_session_id: str,
    request: Request,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentSessionResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.bill")
    service = CheckoutPaymentsService(session, request.app.state.settings)
    checkout_payment_session = await service.retry_checkout_payment_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        checkout_payment_session_id=checkout_payment_session_id,
        actor_user_id=actor.user_id,
    )
    return CheckoutPaymentSessionResponse(**checkout_payment_session)


@branch_router.get("/{tenant_id}/branches/{branch_id}/sales", response_model=SaleListResponse)
async def list_sales(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SaleListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("sales.bill", "sales.return", "refund.approve"),
    )
    service = BillingService(session)
    records = await service.list_sales(tenant_id=tenant_id, branch_id=branch_id)
    return SaleListResponse(records=[SaleRecord(**record) for record in records])


@branch_router.post("/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns", response_model=SaleReturnResponse)
async def create_sale_return(
    tenant_id: str,
    branch_id: str,
    sale_id: str,
    payload: SaleReturnCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SaleReturnResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.return")
    service = BillingService(session)
    sale_return = await service.create_sale_return(
        tenant_id=tenant_id,
        branch_id=branch_id,
        sale_id=sale_id,
        actor_user_id=actor.user_id,
        refund_amount=payload.refund_amount,
        refund_method=payload.refund_method,
        lines=[line.model_dump() for line in payload.lines],
        can_approve_refund=branch_has_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="refund.approve"),
    )
    return SaleReturnResponse(**sale_return)


@branch_router.get("/{tenant_id}/branches/{branch_id}/sale-returns", response_model=SaleReturnListResponse)
async def list_sale_returns(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SaleReturnListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("sales.return", "refund.approve"),
    )
    service = BillingService(session)
    records = await service.list_sale_returns(tenant_id=tenant_id, branch_id=branch_id)
    return SaleReturnListResponse(records=[SaleReturnRecord(**record) for record in records])


@branch_router.post("/{tenant_id}/branches/{branch_id}/sale-returns/{sale_return_id}/approve-refund", response_model=SaleReturnResponse)
async def approve_sale_return_refund(
    tenant_id: str,
    branch_id: str,
    sale_return_id: str,
    payload: RefundApprovalRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SaleReturnResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="refund.approve")
    service = BillingService(session)
    sale_return = await service.approve_sale_return_refund(
        tenant_id=tenant_id,
        branch_id=branch_id,
        sale_return_id=sale_return_id,
        actor_user_id=actor.user_id,
        note=payload.note,
    )
    return SaleReturnResponse(**sale_return)


@webhook_router.post("/webhooks/cashfree/payments", response_model=CheckoutPaymentWebhookResponse)
async def ingest_cashfree_checkout_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> CheckoutPaymentWebhookResponse:
    service = CheckoutPaymentsService(session, request.app.state.settings)
    raw_body = await request.body()
    result = await service.handle_cashfree_webhook(
        raw_body=raw_body,
        signature=request.headers.get("x-webhook-signature"),
        timestamp=request.headers.get("x-webhook-timestamp"),
    )
    return CheckoutPaymentWebhookResponse(**result)


router.include_router(branch_router)
router.include_router(webhook_router)
