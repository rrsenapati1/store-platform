from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import OperationsJobListResponse, OperationsJobResponse
from ..services import ActorContext, OperationsQueueService, assert_branch_any_capability
from ..utils import utc_now

router = APIRouter(prefix="/v1/tenants", tags=["operations"])


def _assert_operations_access(actor: ActorContext, *, tenant_id: str, branch_id: str) -> None:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("reports.view", "compliance.export", "purchase.manage", "settings.manage"),
    )


@router.get("/{tenant_id}/branches/{branch_id}/operations/jobs", response_model=OperationsJobListResponse)
async def list_operations_jobs(
    tenant_id: str,
    branch_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> OperationsJobListResponse:
    _assert_operations_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = OperationsQueueService(session)
    response = await service.list_branch_jobs(
        tenant_id=tenant_id,
        branch_id=branch_id,
        status=status_filter,
    )
    return OperationsJobListResponse(**response)


@router.post("/{tenant_id}/branches/{branch_id}/operations/jobs/{job_id}/retry", response_model=OperationsJobResponse)
async def retry_operations_job(
    tenant_id: str,
    branch_id: str,
    job_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> OperationsJobResponse:
    _assert_operations_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = OperationsQueueService(session)
    job = await service.retry_job(
        tenant_id=tenant_id,
        branch_id=branch_id,
        job_id=job_id,
        now=utc_now(),
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operations job not found or not retryable")
    return OperationsJobResponse(**job)
