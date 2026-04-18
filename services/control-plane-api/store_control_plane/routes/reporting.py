from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..services import ActorContext, ReportingService, assert_branch_any_capability

router = APIRouter(prefix="/v1/tenants", tags=["reporting"])


def _assert_reporting_access(actor: ActorContext, *, tenant_id: str, branch_id: str) -> None:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("reports.view", "purchase.manage"),
    )


@router.get("/{tenant_id}/branches/{branch_id}/management-dashboard")
async def branch_management_dashboard(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    _assert_reporting_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = ReportingService(session)
    return await service.branch_management_dashboard(tenant_id=tenant_id, branch_id=branch_id)
