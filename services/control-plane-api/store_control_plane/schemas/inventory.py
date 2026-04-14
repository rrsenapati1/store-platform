from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class GoodsReceiptCreateRequest(BaseModel):
    purchase_order_id: str


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
    quantity: float
    unit_cost: float
    line_total: float


class GoodsReceiptResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    purchase_order_id: str
    supplier_id: str
    goods_receipt_number: str
    received_on: date
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


class GoodsReceiptListResponse(BaseModel):
    records: list[GoodsReceiptRecord]


class ReceivingBoardRecord(BaseModel):
    purchase_order_id: str
    purchase_order_number: str
    supplier_name: str
    approval_status: str
    receiving_status: str
    can_receive: bool
    blocked_reason: str | None = None
    goods_receipt_id: str | None = None


class ReceivingBoardResponse(BaseModel):
    branch_id: str
    blocked_count: int
    ready_count: int
    received_count: int
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
