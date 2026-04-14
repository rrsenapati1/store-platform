from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import ExchangeCreateRequest, ExchangeResponse
from ..services import ActorContext, BillingService, branch_has_capability, assert_branch_capability

router = APIRouter(prefix="/v1/tenants", tags=["billing"])


@router.post("/{tenant_id}/branches/{branch_id}/sales/{sale_id}/exchanges", response_model=ExchangeResponse)
async def create_exchange(
    tenant_id: str,
    branch_id: str,
    sale_id: str,
    payload: ExchangeCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ExchangeResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="sales.return")
    service = BillingService(session)
    exchange = await service.create_exchange(
        tenant_id=tenant_id,
        branch_id=branch_id,
        sale_id=sale_id,
        actor_user_id=actor.user_id,
        settlement_method=payload.settlement_method,
        return_lines=[line.model_dump() for line in payload.return_lines],
        replacement_lines=[line.model_dump() for line in payload.replacement_lines],
        can_approve_refund=branch_has_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="refund.approve"),
    )
    return ExchangeResponse(**exchange)
