from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import RefundApprovalRequest, SaleCreateRequest, SaleListResponse, SaleRecord, SaleResponse, SaleReturnCreateRequest, SaleReturnListResponse, SaleReturnRecord, SaleReturnResponse
from ..services import ActorContext, BillingService, assert_branch_any_capability, assert_branch_capability, branch_has_capability

router = APIRouter(prefix="/v1/tenants", tags=["billing"])


@router.post("/{tenant_id}/branches/{branch_id}/sales", response_model=SaleResponse)
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
        customer_name=payload.customer_name,
        customer_gstin=payload.customer_gstin,
        payment_method=payload.payment_method,
        lines=[line.model_dump() for line in payload.lines],
    )
    return SaleResponse(**sale)


@router.get("/{tenant_id}/branches/{branch_id}/sales", response_model=SaleListResponse)
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


@router.post("/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns", response_model=SaleReturnResponse)
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


@router.get("/{tenant_id}/branches/{branch_id}/sale-returns", response_model=SaleReturnListResponse)
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


@router.post("/{tenant_id}/branches/{branch_id}/sale-returns/{sale_return_id}/approve-refund", response_model=SaleReturnResponse)
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
