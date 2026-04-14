from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GstExportCreateRequest(BaseModel):
    sale_id: str


class AttachIrnRequest(BaseModel):
    irn: str
    ack_no: str
    signed_qr_payload: str


class BranchIrpProfileUpsertRequest(BaseModel):
    provider_name: str
    api_username: str
    api_password: str | None = None


class BranchIrpProfileResponse(BaseModel):
    provider_name: str | None
    api_username: str | None
    has_password: bool
    status: str
    last_error_message: str | None = None


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
    provider_name: str | None = None
    provider_status: str | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None
    irn: str | None = None
    ack_no: str | None = None
    signed_qr_payload: str | None = None
    created_at: datetime


class GstExportJobListResponse(BaseModel):
    branch_id: str
    pending_count: int
    attached_count: int
    records: list[GstExportJobResponse]
