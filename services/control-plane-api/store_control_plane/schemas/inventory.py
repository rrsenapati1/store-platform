from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class GoodsReceiptCreateRequest(BaseModel):
    purchase_order_id: str
    note: str | None = None
    lines: list["GoodsReceiptLineReceiveRequest"] | None = None


class GoodsReceiptLineReceiveRequest(BaseModel):
    product_id: str
    received_quantity: float
    discrepancy_note: str | None = None
    serial_numbers: list[str] | None = None


class StockAdjustmentCreateRequest(BaseModel):
    product_id: str
    quantity_delta: float
    reason: str
    note: str | None = None


class StockAdjustmentResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    product_id: str
    quantity_delta: float
    reason: str
    note: str | None = None
    resulting_stock_on_hand: float


class StockCountCreateRequest(BaseModel):
    product_id: str
    counted_quantity: float
    note: str | None = None


class StockCountReviewSessionCreateRequest(BaseModel):
    product_id: str
    note: str | None = None


class StockCountReviewSessionRecordRequest(BaseModel):
    counted_quantity: float
    note: str | None = None


class StockCountReviewSessionApproveRequest(BaseModel):
    review_note: str | None = None


class StockCountReviewSessionCancelRequest(BaseModel):
    review_note: str | None = None


class StockCountResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    product_id: str
    counted_quantity: float
    expected_quantity: float
    variance_quantity: float
    note: str | None = None
    closing_stock: float


class StockCountReviewSessionResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    product_id: str
    session_number: str
    status: str
    expected_quantity: float | None = None
    counted_quantity: float | None = None
    variance_quantity: float | None = None
    note: str | None = None
    review_note: str | None = None


class StockCountApprovalResponse(BaseModel):
    session: StockCountReviewSessionResponse
    stock_count: StockCountResponse


class StockCountBoardRecord(BaseModel):
    stock_count_session_id: str
    session_number: str
    product_id: str
    product_name: str
    sku_code: str
    status: str
    expected_quantity: float | None = None
    counted_quantity: float | None = None
    variance_quantity: float | None = None
    note: str | None = None
    review_note: str | None = None


class StockCountBoardResponse(BaseModel):
    branch_id: str
    open_count: int
    counted_count: int
    approved_count: int
    canceled_count: int
    records: list[StockCountBoardRecord]


class TransferCreateRequest(BaseModel):
    destination_branch_id: str
    product_id: str
    quantity: float
    note: str | None = None


class TransferResponse(BaseModel):
    id: str
    tenant_id: str
    source_branch_id: str
    destination_branch_id: str
    product_id: str
    transfer_number: str
    quantity: float
    status: str
    note: str | None = None


class GoodsReceiptLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    ordered_quantity: float
    quantity: float
    variance_quantity: float
    unit_cost: float
    line_total: float
    discrepancy_note: str | None = None
    serial_numbers: list[str] = []


class GoodsReceiptResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    purchase_order_id: str
    supplier_id: str
    goods_receipt_number: str
    received_on: date
    note: str | None = None
    ordered_quantity_total: float
    received_quantity_total: float
    variance_quantity_total: float
    has_discrepancy: bool
    lines: list[GoodsReceiptLineResponse]


class GoodsReceiptRecord(BaseModel):
    goods_receipt_id: str
    goods_receipt_number: str
    purchase_order_id: str
    purchase_order_number: str
    supplier_id: str
    supplier_name: str
    received_on: date
    line_count: int
    received_quantity: float
    ordered_quantity: float
    variance_quantity: float
    has_discrepancy: bool
    note: str | None = None


class GoodsReceiptListResponse(BaseModel):
    records: list[GoodsReceiptRecord]


class ReceivingBoardRecord(BaseModel):
    purchase_order_id: str
    purchase_order_number: str
    supplier_name: str
    approval_status: str
    receiving_status: str
    can_receive: bool
    has_discrepancy: bool = False
    variance_quantity: float = 0.0
    blocked_reason: str | None = None
    goods_receipt_id: str | None = None


class ReceivingBoardResponse(BaseModel):
    branch_id: str
    blocked_count: int
    ready_count: int
    received_count: int
    received_with_variance_count: int = 0
    records: list[ReceivingBoardRecord]


class InventoryLedgerRecord(BaseModel):
    inventory_ledger_entry_id: str
    product_id: str
    product_name: str
    sku_code: str
    entry_type: str
    quantity: float
    reference_type: str
    reference_id: str


class InventoryLedgerListResponse(BaseModel):
    records: list[InventoryLedgerRecord]


class InventorySnapshotRecord(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    stock_on_hand: float
    last_entry_type: str


class InventorySnapshotListResponse(BaseModel):
    records: list[InventorySnapshotRecord]


class ReplenishmentBoardRecord(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    availability_status: str
    stock_on_hand: float
    reorder_point: float
    target_stock: float
    suggested_reorder_quantity: float
    replenishment_status: str


class ReplenishmentBoardResponse(BaseModel):
    branch_id: str
    low_stock_count: int
    adequate_count: int
    records: list[ReplenishmentBoardRecord]


class RestockTaskCreateRequest(BaseModel):
    product_id: str
    requested_quantity: float
    source_posture: str
    note: str | None = None


class RestockTaskPickRequest(BaseModel):
    picked_quantity: float
    note: str | None = None


class RestockTaskCompleteRequest(BaseModel):
    completion_note: str | None = None


class RestockTaskCancelRequest(BaseModel):
    cancel_note: str | None = None


class RestockTaskResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    product_id: str
    task_number: str
    status: str
    stock_on_hand_snapshot: float
    reorder_point_snapshot: float
    target_stock_snapshot: float
    suggested_quantity_snapshot: float
    requested_quantity: float
    picked_quantity: float | None = None
    source_posture: str
    note: str | None = None
    completion_note: str | None = None


class RestockBoardRecord(BaseModel):
    restock_task_id: str
    task_number: str
    product_id: str
    product_name: str
    sku_code: str
    status: str
    stock_on_hand_snapshot: float
    reorder_point_snapshot: float
    target_stock_snapshot: float
    suggested_quantity_snapshot: float
    requested_quantity: float
    picked_quantity: float | None = None
    source_posture: str
    note: str | None = None
    completion_note: str | None = None
    has_active_task: bool


class RestockBoardResponse(BaseModel):
    branch_id: str
    open_count: int
    picked_count: int
    completed_count: int
    canceled_count: int
    records: list[RestockBoardRecord]


class TransferBoardRecord(BaseModel):
    transfer_order_id: str
    transfer_number: str
    direction: str
    counterparty_branch_id: str
    counterparty_branch_name: str
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    status: str


class TransferBoardResponse(BaseModel):
    branch_id: str
    outbound_count: int
    inbound_count: int
    records: list[TransferBoardRecord]
