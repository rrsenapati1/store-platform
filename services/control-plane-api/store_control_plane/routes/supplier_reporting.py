from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import VendorDisputeCreateRequest, VendorDisputeResolveRequest
from ..services import ActorContext, SupplierReportingService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["supplier-reporting"])


def _assert_supplier_reporting_access(actor: ActorContext, *, tenant_id: str, branch_id: str) -> None:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("purchase.manage", "reports.view", "sales.bill", "sales.return"),
    )


@router.post("/{tenant_id}/branches/{branch_id}/vendor-disputes")
async def create_vendor_dispute(
    tenant_id: str,
    branch_id: str,
    payload: VendorDisputeCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = SupplierReportingService(session)
    return await service.create_vendor_dispute(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        goods_receipt_id=payload.goods_receipt_id,
        purchase_invoice_id=payload.purchase_invoice_id,
        dispute_type=payload.dispute_type,
        note=payload.note,
    )


@router.post("/{tenant_id}/branches/{branch_id}/vendor-disputes/{dispute_id}/resolve")
async def resolve_vendor_dispute(
    tenant_id: str,
    branch_id: str,
    dispute_id: str,
    payload: VendorDisputeResolveRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = SupplierReportingService(session)
    return await service.resolve_vendor_dispute(
        tenant_id=tenant_id,
        branch_id=branch_id,
        dispute_id=dispute_id,
        actor_user_id=actor.user_id,
        resolution_note=payload.resolution_note,
    )


@router.get("/{tenant_id}/branches/{branch_id}/vendor-dispute-board")
async def vendor_dispute_board(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.vendor_dispute_board(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-payables-report")
async def supplier_payables_report(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_payables_report(tenant_id=tenant_id, branch_id=branch_id)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-aging-report")
async def supplier_aging_report(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_aging_report(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-statements")
async def supplier_statements(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_statements(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-due-schedule")
async def supplier_due_schedule(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_due_schedule(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-settlement-report")
async def supplier_settlement_report(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_settlement_report(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-settlement-blockers")
async def supplier_settlement_blockers(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_settlement_blockers(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-exception-report")
async def supplier_exception_report(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_exception_report(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-escalation-report")
async def supplier_escalation_report(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_escalation_report(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-performance-report")
async def supplier_performance_report(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_performance_report(tenant_id=tenant_id, branch_id=branch_id)


@router.get("/{tenant_id}/branches/{branch_id}/supplier-payment-activity")
async def supplier_payment_activity(
    tenant_id: str,
    branch_id: str,
    as_of_date: date | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_supplier_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SupplierReportingService(session)
    return await service.supplier_payment_activity(tenant_id=tenant_id, branch_id=branch_id, as_of_date=as_of_date)
