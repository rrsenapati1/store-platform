from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import (
    BranchCustomerReportResponse,
    CustomerDirectoryResponse,
    CustomerHistoryResponse,
    CustomerProfileCreateRequest,
    CustomerProfileListResponse,
    CustomerProfileResponse,
    CustomerProfileUpdateRequest,
    CustomerStoreCreditAdjustmentRequest,
    CustomerStoreCreditIssueRequest,
    CustomerStoreCreditResponse,
)
from ..services import (
    ActorContext,
    CustomerProfileService,
    CustomerReportingService,
    StoreCreditService,
    assert_branch_any_capability,
)

router = APIRouter(prefix="/v1/tenants", tags=["customers"])


@router.get("/{tenant_id}/customer-profiles", response_model=CustomerProfileListResponse)
async def list_customer_profiles(
    tenant_id: str,
    query: str | None = None,
    status: str | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerProfileListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerProfileService(session)
    report = await service.list_customer_profiles(tenant_id=tenant_id, query=query, status_filter=status)
    return CustomerProfileListResponse(**report)


@router.post("/{tenant_id}/customer-profiles", response_model=CustomerProfileResponse)
async def create_customer_profile(
    tenant_id: str,
    payload: CustomerProfileCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerProfileResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerProfileService(session)
    record = await service.create_customer_profile(tenant_id=tenant_id, **payload.model_dump())
    await session.commit()
    return CustomerProfileResponse(**record)


@router.get("/{tenant_id}/customer-profiles/{customer_profile_id}", response_model=CustomerProfileResponse)
async def get_customer_profile(
    tenant_id: str,
    customer_profile_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerProfileResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerProfileService(session)
    record = await service.get_customer_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
    return CustomerProfileResponse(**record)


@router.patch("/{tenant_id}/customer-profiles/{customer_profile_id}", response_model=CustomerProfileResponse)
async def update_customer_profile(
    tenant_id: str,
    customer_profile_id: str,
    payload: CustomerProfileUpdateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerProfileResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerProfileService(session)
    record = await service.update_customer_profile(
        tenant_id=tenant_id,
        customer_profile_id=customer_profile_id,
        updates=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return CustomerProfileResponse(**record)


@router.post("/{tenant_id}/customer-profiles/{customer_profile_id}/archive", response_model=CustomerProfileResponse)
async def archive_customer_profile(
    tenant_id: str,
    customer_profile_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerProfileResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerProfileService(session)
    record = await service.archive_customer_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
    await session.commit()
    return CustomerProfileResponse(**record)


@router.post("/{tenant_id}/customer-profiles/{customer_profile_id}/reactivate", response_model=CustomerProfileResponse)
async def reactivate_customer_profile(
    tenant_id: str,
    customer_profile_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerProfileResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = CustomerProfileService(session)
    record = await service.reactivate_customer_profile(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
    await session.commit()
    return CustomerProfileResponse(**record)


@router.get(
    "/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit",
    response_model=CustomerStoreCreditResponse,
)
async def get_customer_store_credit(
    tenant_id: str,
    customer_profile_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerStoreCreditResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = StoreCreditService(session)
    record = await service.get_customer_store_credit(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
    return CustomerStoreCreditResponse(**record)


@router.post(
    "/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
    response_model=CustomerStoreCreditResponse,
)
async def issue_customer_store_credit(
    tenant_id: str,
    customer_profile_id: str,
    payload: CustomerStoreCreditIssueRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerStoreCreditResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = StoreCreditService(session)
    record = await service.issue_customer_store_credit(
        tenant_id=tenant_id,
        customer_profile_id=customer_profile_id,
        amount=payload.amount,
        note=payload.note,
    )
    await session.commit()
    return CustomerStoreCreditResponse(**record)


@router.post(
    "/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/adjust",
    response_model=CustomerStoreCreditResponse,
)
async def adjust_customer_store_credit(
    tenant_id: str,
    customer_profile_id: str,
    payload: CustomerStoreCreditAdjustmentRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CustomerStoreCreditResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id="",
        capabilities=("reports.view", "sales.bill", "sales.return"),
    )
    service = StoreCreditService(session)
    record = await service.adjust_customer_store_credit(
        tenant_id=tenant_id,
        customer_profile_id=customer_profile_id,
        amount_delta=payload.amount_delta,
        note=payload.note,
    )
    await session.commit()
    return CustomerStoreCreditResponse(**record)


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
