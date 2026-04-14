from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PurchaseInvoiceCreateRequest(BaseModel):
    goods_receipt_id: str


class PurchaseInvoiceLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    unit_cost: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


class PurchaseInvoiceResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    supplier_id: str
    goods_receipt_id: str
    invoice_number: str
    invoice_date: date
    due_date: date
    payment_terms_days: int
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    lines: list[PurchaseInvoiceLineResponse]


class PurchaseInvoiceRecord(BaseModel):
    purchase_invoice_id: str
    purchase_invoice_number: str
    supplier_id: str
    supplier_name: str
    goods_receipt_id: str
    goods_receipt_number: str
    invoice_date: date
    due_date: date
    grand_total: float


class PurchaseInvoiceListResponse(BaseModel):
    records: list[PurchaseInvoiceRecord]


class SupplierReturnLineCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SupplierReturnCreateRequest(BaseModel):
    lines: list[SupplierReturnLineCreateRequest] = Field(min_length=1)


class SupplierReturnLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    unit_cost: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


class SupplierReturnResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    supplier_id: str
    purchase_invoice_id: str
    supplier_credit_note_number: str
    issued_on: date
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    lines: list[SupplierReturnLineResponse]


class SupplierPaymentCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str
    reference: str | None = None


class SupplierPaymentResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    supplier_id: str
    purchase_invoice_id: str
    payment_number: str
    paid_on: date
    payment_method: str
    amount: float
    reference: str | None = None


class SupplierPayablesReportRecord(BaseModel):
    purchase_invoice_id: str
    purchase_invoice_number: str
    supplier_name: str
    grand_total: float
    credit_note_total: float
    paid_total: float
    outstanding_total: float
    settlement_status: str


class SupplierPayablesReportResponse(BaseModel):
    branch_id: str
    invoiced_total: float
    credit_note_total: float
    paid_total: float
    outstanding_total: float
    records: list[SupplierPayablesReportRecord]
