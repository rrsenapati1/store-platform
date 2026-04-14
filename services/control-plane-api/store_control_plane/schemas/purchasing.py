from __future__ import annotations

from pydantic import BaseModel, Field


class SupplierCreateRequest(BaseModel):
    name: str
    gstin: str | None = None
    payment_terms_days: int = Field(default=0, ge=0)


class SupplierResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    gstin: str | None = None
    payment_terms_days: int
    status: str


class SupplierRecord(BaseModel):
    supplier_id: str
    tenant_id: str
    name: str
    gstin: str | None = None
    payment_terms_days: int
    status: str


class SupplierListResponse(BaseModel):
    records: list[SupplierRecord]


class PurchaseOrderLineCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)
    unit_cost: float = Field(gt=0)


class PurchaseOrderCreateRequest(BaseModel):
    supplier_id: str
    lines: list[PurchaseOrderLineCreateRequest] = Field(min_length=1)


class PurchaseOrderLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    unit_cost: float
    line_total: float


class PurchaseOrderResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    supplier_id: str
    purchase_order_number: str
    approval_status: str
    subtotal: float
    tax_total: float
    grand_total: float
    lines: list[PurchaseOrderLineResponse]


class PurchaseOrderRecord(BaseModel):
    purchase_order_id: str
    purchase_order_number: str
    supplier_id: str
    supplier_name: str
    approval_status: str
    line_count: int
    ordered_quantity: float
    grand_total: float
    approval_requested_note: str | None = None
    approval_decision_note: str | None = None


class PurchaseOrderListResponse(BaseModel):
    records: list[PurchaseOrderRecord]


class PurchaseOrderApprovalRequest(BaseModel):
    note: str | None = None


class PurchaseApprovalReportRecord(BaseModel):
    purchase_order_id: str
    purchase_order_number: str
    supplier_name: str
    approval_status: str
    line_count: int
    ordered_quantity: float
    grand_total: float
    approval_requested_note: str | None = None
    approval_decision_note: str | None = None


class PurchaseApprovalReportResponse(BaseModel):
    branch_id: str
    not_requested_count: int
    pending_approval_count: int
    approved_count: int
    rejected_count: int
    records: list[PurchaseApprovalReportRecord]
