from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import (
    PurchaseInvoiceCreateRequest,
    PurchaseInvoiceListResponse,
    PurchaseInvoiceRecord,
    PurchaseInvoiceResponse,
    SupplierPaymentCreateRequest,
    SupplierPaymentResponse,
    SupplierReturnCreateRequest,
    SupplierReturnResponse,
)
from ..services import ActorContext, ProcurementFinanceService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["procurement-finance"])


@router.post("/{tenant_id}/branches/{branch_id}/purchase-invoices", response_model=PurchaseInvoiceResponse)
async def create_purchase_invoice(
    tenant_id: str,
    branch_id: str,
    payload: PurchaseInvoiceCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseInvoiceResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = ProcurementFinanceService(session)
    purchase_invoice = await service.create_purchase_invoice(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        goods_receipt_id=payload.goods_receipt_id,
    )
    return PurchaseInvoiceResponse(**purchase_invoice)


@router.get("/{tenant_id}/branches/{branch_id}/purchase-invoices", response_model=PurchaseInvoiceListResponse)
async def list_purchase_invoices(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseInvoiceListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("purchase.manage", "reports.view"),
    )
    service = ProcurementFinanceService(session)
    records = await service.list_purchase_invoices(tenant_id=tenant_id, branch_id=branch_id)
    return PurchaseInvoiceListResponse(records=[PurchaseInvoiceRecord(**record) for record in records])


@router.post(
    "/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-returns",
    response_model=SupplierReturnResponse,
)
async def create_supplier_return(
    tenant_id: str,
    branch_id: str,
    purchase_invoice_id: str,
    payload: SupplierReturnCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SupplierReturnResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = ProcurementFinanceService(session)
    supplier_return = await service.create_supplier_return(
        tenant_id=tenant_id,
        branch_id=branch_id,
        purchase_invoice_id=purchase_invoice_id,
        actor_user_id=actor.user_id,
        lines=[line.model_dump() for line in payload.lines],
    )
    return SupplierReturnResponse(**supplier_return)


@router.post(
    "/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-payments",
    response_model=SupplierPaymentResponse,
)
async def create_supplier_payment(
    tenant_id: str,
    branch_id: str,
    purchase_invoice_id: str,
    payload: SupplierPaymentCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SupplierPaymentResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = ProcurementFinanceService(session)
    supplier_payment = await service.create_supplier_payment(
        tenant_id=tenant_id,
        branch_id=branch_id,
        purchase_invoice_id=purchase_invoice_id,
        actor_user_id=actor.user_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        reference=payload.reference,
    )
    return SupplierPaymentResponse(**supplier_payment)
