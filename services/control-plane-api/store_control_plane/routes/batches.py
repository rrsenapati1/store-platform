from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import (
    BatchExpiryBoardRecord,
    BatchExpiryBoardResponse,
    BatchExpiryReportRecord,
    BatchExpiryReportResponse,
    BatchExpiryReviewApprovalResponse,
    BatchExpiryReviewSessionApproveRequest,
    BatchExpiryReviewSessionCancelRequest,
    BatchExpiryReviewSessionCreateRequest,
    BatchExpiryReviewSessionRecordRequest,
    BatchExpiryReviewSessionResponse,
    BatchExpiryWriteOffCreateRequest,
    BatchExpiryWriteOffResponse,
    BatchLotResponse,
    GoodsReceiptBatchLotCreateRequest,
    GoodsReceiptBatchLotResponse,
)
from ..services import ActorContext, BatchService, assert_branch_any_capability

router = APIRouter(prefix="/v1/tenants", tags=["batches"])


@router.post("/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt_id}/batch-lots", response_model=GoodsReceiptBatchLotResponse)
async def create_goods_receipt_batch_lots(
    tenant_id: str,
    branch_id: str,
    goods_receipt_id: str,
    payload: GoodsReceiptBatchLotCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> GoodsReceiptBatchLotResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("purchase.manage", "inventory.adjust"))
    service = BatchService(session)
    response = await service.create_goods_receipt_batch_lots(
        tenant_id=tenant_id,
        branch_id=branch_id,
        goods_receipt_id=goods_receipt_id,
        actor_user_id=actor.user_id,
        lots=[lot.model_dump() for lot in payload.lots],
    )
    return GoodsReceiptBatchLotResponse(
        goods_receipt_id=response["goods_receipt_id"],
        records=[BatchLotResponse(**record) for record in response["records"]],
    )


@router.get("/{tenant_id}/branches/{branch_id}/batch-expiry-report", response_model=BatchExpiryReportResponse)
async def batch_expiry_report(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryReportResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("purchase.manage", "inventory.adjust", "reports.view"))
    service = BatchService(session)
    report = await service.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id)
    return BatchExpiryReportResponse(
        branch_id=report["branch_id"],
        tracked_lot_count=report["tracked_lot_count"],
        expiring_soon_count=report["expiring_soon_count"],
        expired_count=report["expired_count"],
        untracked_stock_quantity=report["untracked_stock_quantity"],
        records=[BatchExpiryReportRecord(**record) for record in report["records"]],
    )


@router.get("/{tenant_id}/branches/{branch_id}/batch-expiry-board", response_model=BatchExpiryBoardResponse)
async def batch_expiry_board(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryBoardResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("inventory.adjust", "reports.view"))
    service = BatchService(session)
    board = await service.batch_expiry_board(tenant_id=tenant_id, branch_id=branch_id)
    return BatchExpiryBoardResponse(
        branch_id=board["branch_id"],
        open_count=board["open_count"],
        reviewed_count=board["reviewed_count"],
        approved_count=board["approved_count"],
        canceled_count=board["canceled_count"],
        records=[BatchExpiryBoardRecord(**record) for record in board["records"]],
    )


@router.post("/{tenant_id}/branches/{branch_id}/batch-expiry-sessions", response_model=BatchExpiryReviewSessionResponse)
async def create_batch_expiry_review_session(
    tenant_id: str,
    branch_id: str,
    payload: BatchExpiryReviewSessionCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryReviewSessionResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("inventory.adjust",))
    service = BatchService(session)
    record = await service.create_batch_expiry_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        batch_lot_id=payload.batch_lot_id,
        actor_user_id=actor.user_id,
        note=payload.note,
    )
    return BatchExpiryReviewSessionResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/batch-expiry-sessions/{batch_expiry_session_id}/review", response_model=BatchExpiryReviewSessionResponse)
async def record_batch_expiry_review_session(
    tenant_id: str,
    branch_id: str,
    batch_expiry_session_id: str,
    payload: BatchExpiryReviewSessionRecordRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryReviewSessionResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("inventory.adjust",))
    service = BatchService(session)
    record = await service.record_batch_expiry_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        batch_expiry_session_id=batch_expiry_session_id,
        actor_user_id=actor.user_id,
        quantity=payload.quantity,
        reason=payload.reason,
    )
    return BatchExpiryReviewSessionResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/batch-expiry-sessions/{batch_expiry_session_id}/approve", response_model=BatchExpiryReviewApprovalResponse)
async def approve_batch_expiry_review_session(
    tenant_id: str,
    branch_id: str,
    batch_expiry_session_id: str,
    payload: BatchExpiryReviewSessionApproveRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryReviewApprovalResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("inventory.adjust",))
    service = BatchService(session)
    record = await service.approve_batch_expiry_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        batch_expiry_session_id=batch_expiry_session_id,
        actor_user_id=actor.user_id,
        review_note=payload.review_note,
    )
    return BatchExpiryReviewApprovalResponse(
        session=BatchExpiryReviewSessionResponse(**record["session"]),
        write_off=BatchExpiryWriteOffResponse(**record["write_off"]),
    )


@router.post("/{tenant_id}/branches/{branch_id}/batch-expiry-sessions/{batch_expiry_session_id}/cancel", response_model=BatchExpiryReviewSessionResponse)
async def cancel_batch_expiry_review_session(
    tenant_id: str,
    branch_id: str,
    batch_expiry_session_id: str,
    payload: BatchExpiryReviewSessionCancelRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryReviewSessionResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("inventory.adjust",))
    service = BatchService(session)
    record = await service.cancel_batch_expiry_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        batch_expiry_session_id=batch_expiry_session_id,
        actor_user_id=actor.user_id,
        review_note=payload.review_note,
    )
    return BatchExpiryReviewSessionResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/batch-lots/{batch_lot_id}/expiry-write-offs", response_model=BatchExpiryWriteOffResponse)
async def create_batch_expiry_write_off(
    tenant_id: str,
    branch_id: str,
    batch_lot_id: str,
    payload: BatchExpiryWriteOffCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BatchExpiryWriteOffResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("inventory.adjust",))
    service = BatchService(session)
    response = await service.create_batch_expiry_write_off(
        tenant_id=tenant_id,
        branch_id=branch_id,
        batch_lot_id=batch_lot_id,
        actor_user_id=actor.user_id,
        quantity=payload.quantity,
        reason=payload.reason,
    )
    return BatchExpiryWriteOffResponse(**response)
