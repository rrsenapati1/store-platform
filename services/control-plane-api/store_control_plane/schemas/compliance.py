from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GstExportCreateRequest(BaseModel):
    sale_id: str


class AttachIrnRequest(BaseModel):
    irn: str
    ack_no: str
    signed_qr_payload: str


class GstExportJobResponse(BaseModel):
    id: str
    sale_id: str
    invoice_id: str
    invoice_number: str
    customer_name: str
    seller_gstin: str
    buyer_gstin: str | None = None
    hsn_sac_summary: str
    grand_total: float
    status: str
    irn: str | None = None
    ack_no: str | None = None
    signed_qr_payload: str | None = None
    created_at: datetime


class GstExportJobListResponse(BaseModel):
    branch_id: str
    pending_count: int
    attached_count: int
    records: list[GstExportJobResponse]
