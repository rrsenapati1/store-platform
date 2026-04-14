from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PrintJobQueueRequest(BaseModel):
    device_id: str
    copies: int = 1


class PrintJobCompletionRequest(BaseModel):
    status: str
    failure_reason: str | None = None


class RuntimeDeviceHeartbeatResponse(BaseModel):
    device_id: str
    status: str
    last_seen_at: datetime | None = None
    queued_job_count: int


class BarcodeLabelPayloadItem(BaseModel):
    sku_code: str
    product_name: str
    barcode: str
    price_label: str


class PrintJobPayload(BaseModel):
    document_number: str | None = None
    customer_name: str | None = None
    receipt_lines: list[str] = Field(default_factory=list)
    product_id: str | None = None
    labels: list[BarcodeLabelPayloadItem] = Field(default_factory=list)


class PrintJobResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    device_id: str
    reference_type: str
    reference_id: str
    job_type: str
    copies: int
    status: str
    failure_reason: str | None = None
    payload: PrintJobPayload


class PrintJobListResponse(BaseModel):
    records: list[PrintJobResponse]
