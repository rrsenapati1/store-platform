from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import PurchaseApprovalReportRecord, PurchaseApprovalReportResponse, PurchaseOrderApprovalRequest, PurchaseOrderCreateRequest, PurchaseOrderListResponse, PurchaseOrderRecord, PurchaseOrderResponse, SupplierCreateRequest, SupplierListResponse, SupplierRecord, SupplierResponse
from ..services import ActorContext, PurchasingService, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["purchasing"])


@router.post("/{tenant_id}/suppliers", response_model=SupplierResponse)
async def create_supplier(
    tenant_id: str,
    payload: SupplierCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SupplierResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    supplier = await service.create_supplier(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        name=payload.name,
        gstin=payload.gstin,
        payment_terms_days=payload.payment_terms_days,
    )
    return SupplierResponse.model_validate(supplier, from_attributes=True)


@router.get("/{tenant_id}/suppliers", response_model=SupplierListResponse)
async def list_suppliers(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SupplierListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    records = await service.list_suppliers(tenant_id=tenant_id)
    return SupplierListResponse(records=[SupplierRecord(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/purchase-orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    tenant_id: str,
    branch_id: str,
    payload: PurchaseOrderCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOrderResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    purchase_order = await service.create_purchase_order(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        supplier_id=payload.supplier_id,
        lines=[line.model_dump() for line in payload.lines],
    )
    return PurchaseOrderResponse(**purchase_order)


@router.get("/{tenant_id}/branches/{branch_id}/purchase-orders", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOrderListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    records = await service.list_purchase_orders(tenant_id=tenant_id, branch_id=branch_id)
    return PurchaseOrderListResponse(records=[PurchaseOrderRecord(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    tenant_id: str,
    branch_id: str,
    purchase_order_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOrderResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    purchase_order = await service.get_purchase_order(
        tenant_id=tenant_id,
        branch_id=branch_id,
        purchase_order_id=purchase_order_id,
    )
    return PurchaseOrderResponse(**purchase_order)


@router.post("/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval", response_model=PurchaseOrderResponse)
async def submit_purchase_order(
    tenant_id: str,
    branch_id: str,
    purchase_order_id: str,
    payload: PurchaseOrderApprovalRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOrderResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    purchase_order = await service.submit_purchase_order(
        tenant_id=tenant_id,
        branch_id=branch_id,
        purchase_order_id=purchase_order_id,
        actor_user_id=actor.user_id,
        note=payload.note,
    )
    return PurchaseOrderResponse(**purchase_order)


@router.post("/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve", response_model=PurchaseOrderResponse)
async def approve_purchase_order(
    tenant_id: str,
    branch_id: str,
    purchase_order_id: str,
    payload: PurchaseOrderApprovalRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOrderResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    purchase_order = await service.approve_purchase_order(
        tenant_id=tenant_id,
        branch_id=branch_id,
        purchase_order_id=purchase_order_id,
        actor_user_id=actor.user_id,
        note=payload.note,
    )
    return PurchaseOrderResponse(**purchase_order)


@router.get("/{tenant_id}/branches/{branch_id}/purchase-approval-report", response_model=PurchaseApprovalReportResponse)
async def purchase_approval_report(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PurchaseApprovalReportResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = PurchasingService(session)
    report = await service.purchase_approval_report(tenant_id=tenant_id, branch_id=branch_id)
    return PurchaseApprovalReportResponse(
        branch_id=report["branch_id"],
        not_requested_count=report["not_requested_count"],
        pending_approval_count=report["pending_approval_count"],
        approved_count=report["approved_count"],
        rejected_count=report["rejected_count"],
        records=[PurchaseApprovalReportRecord(**record) for record in report["records"]],
    )
