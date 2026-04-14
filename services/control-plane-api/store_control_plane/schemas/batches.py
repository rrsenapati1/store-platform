from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class BatchLotCreateRequest(BaseModel):
    product_id: str
    batch_number: str = Field(min_length=1)
    quantity: float
    expiry_date: date


class GoodsReceiptBatchLotCreateRequest(BaseModel):
    lots: list[BatchLotCreateRequest] = Field(min_length=1)


class BatchLotResponse(BaseModel):
    id: str
    product_id: str
    batch_number: str
    quantity: float
    expiry_date: date


class GoodsReceiptBatchLotResponse(BaseModel):
    goods_receipt_id: str
    records: list[BatchLotResponse]


class BatchExpiryReportRecord(BaseModel):
    batch_lot_id: str
    product_id: str
    product_name: str
    batch_number: str
    expiry_date: date
    days_to_expiry: int
    received_quantity: float
    written_off_quantity: float
    remaining_quantity: float
    status: str


class BatchExpiryReportResponse(BaseModel):
    branch_id: str
    tracked_lot_count: int
    expiring_soon_count: int
    expired_count: int
    untracked_stock_quantity: float
    records: list[BatchExpiryReportRecord]


class BatchExpiryWriteOffCreateRequest(BaseModel):
    quantity: float
    reason: str = Field(min_length=1)


class BatchExpiryWriteOffResponse(BaseModel):
    batch_lot_id: str
    product_id: str
    product_name: str
    batch_number: str
    expiry_date: date
    received_quantity: float
    written_off_quantity: float
    remaining_quantity: float
    status: str
    reason: str
