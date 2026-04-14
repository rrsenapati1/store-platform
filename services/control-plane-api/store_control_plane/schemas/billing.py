from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class SaleLineCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SaleCreateRequest(BaseModel):
    customer_name: str
    customer_gstin: str | None = None
    payment_method: str
    lines: list[SaleLineCreateRequest]


class PaymentResponse(BaseModel):
    payment_method: str
    amount: float


class SaleLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    hsn_sac_code: str
    quantity: float
    unit_price: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


class InvoiceTaxLineResponse(BaseModel):
    tax_type: str
    tax_rate: float
    taxable_amount: float
    tax_amount: float


class SaleResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    customer_name: str
    customer_gstin: str | None = None
    invoice_kind: str
    irn_status: str
    invoice_number: str
    issued_on: date
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    payment: PaymentResponse
    lines: list[SaleLineResponse]
    tax_lines: list[InvoiceTaxLineResponse]


class SaleRecord(BaseModel):
    sale_id: str
    invoice_number: str
    customer_name: str
    invoice_kind: str
    irn_status: str
    payment_method: str
    grand_total: float
    issued_on: date


class SaleListResponse(BaseModel):
    records: list[SaleRecord]


class SaleReturnLineCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SaleReturnCreateRequest(BaseModel):
    refund_amount: float = Field(ge=0)
    refund_method: str
    lines: list[SaleReturnLineCreateRequest]


class RefundApprovalRequest(BaseModel):
    note: str | None = None


class CreditNoteTaxLineResponse(BaseModel):
    tax_type: str
    tax_rate: float
    taxable_amount: float
    tax_amount: float


class CreditNoteResponse(BaseModel):
    id: str
    credit_note_number: str
    issued_on: date
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    tax_lines: list[CreditNoteTaxLineResponse]


class SaleReturnLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    hsn_sac_code: str
    quantity: float
    unit_price: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


class SaleReturnResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    sale_id: str
    status: str
    refund_amount: float
    refund_method: str
    lines: list[SaleReturnLineResponse]
    credit_note: CreditNoteResponse


class SaleReturnRecord(BaseModel):
    sale_return_id: str
    sale_id: str
    invoice_number: str
    customer_name: str
    status: str
    refund_amount: float
    refund_method: str
    credit_note_number: str
    credit_note_total: float
    issued_on: date


class SaleReturnListResponse(BaseModel):
    records: list[SaleReturnRecord]
