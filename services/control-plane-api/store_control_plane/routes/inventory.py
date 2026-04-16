from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import GoodsReceiptCreateRequest, GoodsReceiptListResponse, GoodsReceiptRecord, GoodsReceiptResponse, InventoryLedgerListResponse, InventoryLedgerRecord, InventorySnapshotListResponse, InventorySnapshotRecord, ReceivingBoardRecord, ReceivingBoardResponse, ReplenishmentBoardRecord, ReplenishmentBoardResponse, RestockBoardRecord, RestockBoardResponse, RestockTaskCancelRequest, RestockTaskCompleteRequest, RestockTaskCreateRequest, RestockTaskPickRequest, RestockTaskResponse, StockAdjustmentCreateRequest, StockAdjustmentResponse, StockCountApprovalResponse, StockCountBoardRecord, StockCountBoardResponse, StockCountCreateRequest, StockCountResponse, StockCountReviewSessionApproveRequest, StockCountReviewSessionCancelRequest, StockCountReviewSessionCreateRequest, StockCountReviewSessionRecordRequest, StockCountReviewSessionResponse, TransferBoardRecord, TransferBoardResponse, TransferCreateRequest, TransferResponse
from ..services import ActorContext, InventoryService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["inventory"])


@router.get("/{tenant_id}/branches/{branch_id}/receiving-board", response_model=ReceivingBoardResponse)
async def receiving_board(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ReceivingBoardResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = InventoryService(session)
    report = await service.receiving_board(tenant_id=tenant_id, branch_id=branch_id)
    return ReceivingBoardResponse(
        branch_id=report["branch_id"],
        blocked_count=report["blocked_count"],
        ready_count=report["ready_count"],
        received_count=report["received_count"],
        received_with_variance_count=report["received_with_variance_count"],
        records=[ReceivingBoardRecord(**record) for record in report["records"]],
    )


@router.post("/{tenant_id}/branches/{branch_id}/goods-receipts", response_model=GoodsReceiptResponse)
async def create_goods_receipt(
    tenant_id: str,
    branch_id: str,
    payload: GoodsReceiptCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> GoodsReceiptResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = InventoryService(session)
    receipt = await service.create_goods_receipt(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        purchase_order_id=payload.purchase_order_id,
        note=payload.note,
        lines=[line.model_dump() for line in payload.lines] if payload.lines is not None else None,
    )
    return GoodsReceiptResponse(**receipt)


@router.post("/{tenant_id}/branches/{branch_id}/stock-adjustments", response_model=StockAdjustmentResponse)
async def create_stock_adjustment(
    tenant_id: str,
    branch_id: str,
    payload: StockAdjustmentCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockAdjustmentResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    adjustment = await service.create_stock_adjustment(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        product_id=payload.product_id,
        quantity_delta=payload.quantity_delta,
        reason=payload.reason,
        note=payload.note,
    )
    return StockAdjustmentResponse(**adjustment)


@router.post("/{tenant_id}/branches/{branch_id}/stock-counts", response_model=StockCountResponse)
async def create_stock_count(
    tenant_id: str,
    branch_id: str,
    payload: StockCountCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockCountResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    stock_count = await service.create_stock_count(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        product_id=payload.product_id,
        counted_quantity=payload.counted_quantity,
        note=payload.note,
    )
    return StockCountResponse(**stock_count)


@router.get("/{tenant_id}/branches/{branch_id}/stock-count-board", response_model=StockCountBoardResponse)
async def stock_count_board(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockCountBoardResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    report = await service.stock_count_board(tenant_id=tenant_id, branch_id=branch_id)
    return StockCountBoardResponse(
        branch_id=report["branch_id"],
        open_count=report["open_count"],
        counted_count=report["counted_count"],
        approved_count=report["approved_count"],
        canceled_count=report["canceled_count"],
        records=[StockCountBoardRecord(**record) for record in report["records"]],
    )


@router.post("/{tenant_id}/branches/{branch_id}/stock-count-sessions", response_model=StockCountReviewSessionResponse)
async def create_stock_count_review_session(
    tenant_id: str,
    branch_id: str,
    payload: StockCountReviewSessionCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockCountReviewSessionResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.create_stock_count_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        product_id=payload.product_id,
        note=payload.note,
    )
    return StockCountReviewSessionResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/stock-count-sessions/{stock_count_session_id}/record", response_model=StockCountReviewSessionResponse)
async def record_stock_count_review_session(
    tenant_id: str,
    branch_id: str,
    stock_count_session_id: str,
    payload: StockCountReviewSessionRecordRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockCountReviewSessionResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.record_stock_count_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        stock_count_session_id=stock_count_session_id,
        counted_quantity=payload.counted_quantity,
        note=payload.note,
    )
    return StockCountReviewSessionResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/stock-count-sessions/{stock_count_session_id}/approve", response_model=StockCountApprovalResponse)
async def approve_stock_count_review_session(
    tenant_id: str,
    branch_id: str,
    stock_count_session_id: str,
    payload: StockCountReviewSessionApproveRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockCountApprovalResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.approve_stock_count_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        stock_count_session_id=stock_count_session_id,
        review_note=payload.review_note,
    )
    return StockCountApprovalResponse(
        session=StockCountReviewSessionResponse(**record["session"]),
        stock_count=StockCountResponse(**record["stock_count"]),
    )


@router.post("/{tenant_id}/branches/{branch_id}/stock-count-sessions/{stock_count_session_id}/cancel", response_model=StockCountReviewSessionResponse)
async def cancel_stock_count_review_session(
    tenant_id: str,
    branch_id: str,
    stock_count_session_id: str,
    payload: StockCountReviewSessionCancelRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StockCountReviewSessionResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.cancel_stock_count_review_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        stock_count_session_id=stock_count_session_id,
        review_note=payload.review_note,
    )
    return StockCountReviewSessionResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/transfers", response_model=TransferResponse)
async def create_transfer(
    tenant_id: str,
    branch_id: str,
    payload: TransferCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> TransferResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.transfer")
    service = InventoryService(session)
    transfer = await service.create_transfer(
        tenant_id=tenant_id,
        source_branch_id=branch_id,
        actor_user_id=actor.user_id,
        destination_branch_id=payload.destination_branch_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        note=payload.note,
    )
    return TransferResponse(**transfer)


@router.get("/{tenant_id}/branches/{branch_id}/goods-receipts", response_model=GoodsReceiptListResponse)
async def list_goods_receipts(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> GoodsReceiptListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = InventoryService(session)
    records = await service.list_goods_receipts(tenant_id=tenant_id, branch_id=branch_id)
    return GoodsReceiptListResponse(records=[GoodsReceiptRecord(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/inventory-ledger", response_model=InventoryLedgerListResponse)
async def inventory_ledger(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> InventoryLedgerListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="purchase.manage")
    service = InventoryService(session)
    records = await service.inventory_ledger(tenant_id=tenant_id, branch_id=branch_id)
    return InventoryLedgerListResponse(records=[InventoryLedgerRecord(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/inventory-snapshot", response_model=InventorySnapshotListResponse)
async def inventory_snapshot(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> InventorySnapshotListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("purchase.manage", "inventory.adjust", "inventory.transfer", "sales.bill", "reports.view"),
    )
    service = InventoryService(session)
    report = await service.inventory_snapshot(tenant_id=tenant_id, branch_id=branch_id)
    return InventorySnapshotListResponse(records=[InventorySnapshotRecord(**record) for record in report["records"]])


@router.get("/{tenant_id}/branches/{branch_id}/replenishment-board", response_model=ReplenishmentBoardResponse)
async def replenishment_board(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ReplenishmentBoardResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("purchase.manage", "inventory.adjust", "reports.view"),
    )
    service = InventoryService(session)
    report = await service.replenishment_board(tenant_id=tenant_id, branch_id=branch_id)
    return ReplenishmentBoardResponse(
        branch_id=report["branch_id"],
        low_stock_count=report["low_stock_count"],
        adequate_count=report["adequate_count"],
        records=[ReplenishmentBoardRecord(**record) for record in report["records"]],
    )


@router.get("/{tenant_id}/branches/{branch_id}/restock-board", response_model=RestockBoardResponse)
async def restock_board(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RestockBoardResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("purchase.manage", "inventory.adjust", "reports.view"),
    )
    service = InventoryService(session)
    report = await service.restock_board(tenant_id=tenant_id, branch_id=branch_id)
    return RestockBoardResponse(
        branch_id=report["branch_id"],
        open_count=report["open_count"],
        picked_count=report["picked_count"],
        completed_count=report["completed_count"],
        canceled_count=report["canceled_count"],
        records=[RestockBoardRecord(**record) for record in report["records"]],
    )


@router.post("/{tenant_id}/branches/{branch_id}/restock-tasks", response_model=RestockTaskResponse)
async def create_restock_task(
    tenant_id: str,
    branch_id: str,
    payload: RestockTaskCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RestockTaskResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.create_restock_task(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        product_id=payload.product_id,
        requested_quantity=payload.requested_quantity,
        source_posture=payload.source_posture,
        note=payload.note,
    )
    return RestockTaskResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/restock-tasks/{restock_task_id}/pick", response_model=RestockTaskResponse)
async def pick_restock_task(
    tenant_id: str,
    branch_id: str,
    restock_task_id: str,
    payload: RestockTaskPickRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RestockTaskResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.pick_restock_task(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        restock_task_id=restock_task_id,
        picked_quantity=payload.picked_quantity,
        note=payload.note,
    )
    return RestockTaskResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/restock-tasks/{restock_task_id}/complete", response_model=RestockTaskResponse)
async def complete_restock_task(
    tenant_id: str,
    branch_id: str,
    restock_task_id: str,
    payload: RestockTaskCompleteRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RestockTaskResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.complete_restock_task(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        restock_task_id=restock_task_id,
        completion_note=payload.completion_note,
    )
    return RestockTaskResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/restock-tasks/{restock_task_id}/cancel", response_model=RestockTaskResponse)
async def cancel_restock_task(
    tenant_id: str,
    branch_id: str,
    restock_task_id: str,
    payload: RestockTaskCancelRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RestockTaskResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.adjust")
    service = InventoryService(session)
    record = await service.cancel_restock_task(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        restock_task_id=restock_task_id,
        cancel_note=payload.cancel_note,
    )
    return RestockTaskResponse(**record)


@router.get("/{tenant_id}/branches/{branch_id}/transfer-board", response_model=TransferBoardResponse)
async def transfer_board(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> TransferBoardResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="inventory.transfer")
    service = InventoryService(session)
    report = await service.transfer_board(tenant_id=tenant_id, branch_id=branch_id)
    return TransferBoardResponse(
        branch_id=report["branch_id"],
        outbound_count=report["outbound_count"],
        inbound_count=report["inbound_count"],
        records=[TransferBoardRecord(**record) for record in report["records"]],
    )
