from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import BranchCustomerReportResponse, CustomerDirectoryResponse, CustomerHistoryResponse
from ..services import ActorContext, CustomerReportingService, assert_branch_any_capability

router = APIRouter(prefix="/v1/tenants", tags=["customers"])


@router.get("/{tenant_id}/customers", response_model=CustomerDirectoryResponse)
async def list_customers(
    tenant_id: str,
    query: str | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerDirectoryResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerReportingService(session)
    report = await service.list_customer_directory(tenant_id=tenant_id, query=query)
    return CustomerDirectoryResponse(**report)


@router.get("/{tenant_id}/customers/{customer_id}/history", response_model=CustomerHistoryResponse)
async def get_customer_history(
    tenant_id: str,
    customer_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerHistoryResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerReportingService(session)
    report = await service.get_customer_history(tenant_id=tenant_id, customer_id=customer_id)
    return CustomerHistoryResponse(**report)


@router.get("/{tenant_id}/branches/{branch_id}/customer-report", response_model=BranchCustomerReportResponse)
async def get_branch_customer_report(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchCustomerReportResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerReportingService(session)
    report = await service.branch_customer_report(tenant_id=tenant_id, branch_id=branch_id)
    return BranchCustomerReportResponse(**report)
