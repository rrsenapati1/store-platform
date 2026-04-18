from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class SaleLineCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)
    serial_numbers: list[str] | None = None
    compliance_capture: dict[str, object] | None = None


class SaleCreateRequest(BaseModel):
    cashier_session_id: str
    customer_profile_id: str | None = None
    customer_name: str
    customer_gstin: str | None = None
    payment_method: str
    promotion_code: str | None = None
    customer_voucher_id: str | None = None
    gift_card_code: str | None = None
    gift_card_amount: float = Field(default=0, ge=0)
    store_credit_amount: float = Field(default=0, ge=0)
    loyalty_points_to_redeem: int = Field(default=0, ge=0)
    lines: list[SaleLineCreateRequest]


class CheckoutPaymentSessionCreateRequest(BaseModel):
    cashier_session_id: str
    provider_name: str
    payment_method: str
    handoff_surface: str | None = None
    provider_payment_mode: str | None = None
    customer_profile_id: str | None = None
    customer_name: str
    customer_gstin: str | None = None
    promotion_code: str | None = None
    customer_voucher_id: str | None = None
    gift_card_code: str | None = None
    gift_card_amount: float = Field(default=0, ge=0)
    loyalty_points_to_redeem: int = Field(default=0, ge=0)
    store_credit_amount: float = Field(default=0, ge=0)
    lines: list[SaleLineCreateRequest]


class CheckoutPricePreviewRequest(BaseModel):
    customer_profile_id: str | None = None
    customer_name: str
    customer_gstin: str | None = None
    promotion_code: str | None = None
    customer_voucher_id: str | None = None
    gift_card_code: str | None = None
    gift_card_amount: float = Field(default=0, ge=0)
    loyalty_points_to_redeem: int = Field(default=0, ge=0)
    store_credit_amount: float = Field(default=0, ge=0)
    lines: list[SaleLineCreateRequest]


class CheckoutPricePreviewCampaignResponse(BaseModel):
    id: str
    name: str
    trigger_mode: str
    scope: str
    discount_type: str
    discount_value: float


class CheckoutPricePreviewCodeCampaignResponse(CheckoutPricePreviewCampaignResponse):
    code_id: str
    code: str


class CheckoutPricePreviewGiftCardResponse(BaseModel):
    id: str
    gift_card_code: str
    display_name: str
    status: str
    available_balance: float


class CheckoutPricePreviewCustomerVoucherResponse(BaseModel):
    id: str
    voucher_code: str
    voucher_name: str
    voucher_amount: float


class CheckoutPricePreviewSummaryResponse(BaseModel):
    mrp_total: float
    selling_price_subtotal: float
    automatic_discount_total: float = 0
    promotion_code_discount_total: float = 0
    customer_voucher_discount_total: float = 0
    loyalty_discount_total: float = 0
    total_discount: float = 0
    tax_total: float
    invoice_total: float
    grand_total: float
    gift_card_amount: float = 0
    store_credit_amount: float = 0
    final_payable_amount: float


class CheckoutPricePreviewLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    serial_numbers: list[str] | None = None
    compliance_profile: str = "NONE"
    compliance_capture: dict[str, object] | None = None
    mrp: float
    unit_selling_price: float
    automatic_discount_amount: float = 0
    promotion_code_discount_amount: float = 0
    customer_voucher_discount_amount: float | None = None
    promotion_discount_source: str | None = None
    taxable_amount: float
    tax_amount: float
    line_total: float


class CheckoutPricePreviewResponse(BaseModel):
    customer_profile_id: str | None = None
    customer_name: str
    customer_gstin: str | None = None
    automatic_campaign: CheckoutPricePreviewCampaignResponse | None = None
    promotion_code_campaign: CheckoutPricePreviewCodeCampaignResponse | None = None
    customer_voucher: CheckoutPricePreviewCustomerVoucherResponse | None = None
    gift_card: CheckoutPricePreviewGiftCardResponse | None = None
    summary: CheckoutPricePreviewSummaryResponse
    lines: list[CheckoutPricePreviewLineResponse]
    tax_lines: list["InvoiceTaxLineResponse"]


class CheckoutPaymentActionPayloadResponse(BaseModel):
    kind: str
    value: str
    label: str | None = None
    description: str | None = None


class CheckoutPaymentQrPayloadResponse(BaseModel):
    format: str
    value: str


class CheckoutPaymentSessionResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    cashier_session_id: str | None = None
    customer_profile_id: str | None = None
    provider_name: str
    provider_order_id: str
    provider_payment_session_id: str | None = None
    provider_payment_id: str | None = None
    payment_method: str
    handoff_surface: str
    provider_payment_mode: str
    lifecycle_status: str
    provider_status: str
    order_amount: float
    currency_code: str
    automatic_campaign_name: str | None = None
    automatic_discount_total: float = 0
    promotion_code: str | None = None
    promotion_discount_amount: float = 0
    promotion_code_discount_total: float = 0
    customer_voucher_id: str | None = None
    customer_voucher_name: str | None = None
    customer_voucher_discount_total: float = 0
    gift_card_id: str | None = None
    gift_card_code: str | None = None
    gift_card_amount: float = 0
    store_credit_amount: float = 0
    action_payload: CheckoutPaymentActionPayloadResponse
    action_expires_at: datetime | None = None
    qr_payload: CheckoutPaymentQrPayloadResponse | None = None
    qr_expires_at: datetime | None = None
    last_error_message: str | None = None
    last_reconciled_at: datetime | None = None
    recovery_state: str
    sale: "SaleResponse | None" = None


class CheckoutPaymentWebhookResponse(BaseModel):
    status: str
    checkout_payment_session_id: str | None = None
    lifecycle_status: str | None = None


class CheckoutPaymentSessionListResponse(BaseModel):
    records: list[CheckoutPaymentSessionResponse]


class PaymentResponse(BaseModel):
    payment_method: str
    amount: float


class SaleLineResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    hsn_sac_code: str
    quantity: float
    serial_numbers: list[str] | None = None
    compliance_profile: str = "NONE"
    compliance_capture: dict[str, object] | None = None
    mrp: float = 0
    unit_selling_price: float = 0
    unit_price: float
    gst_rate: float
    automatic_discount_amount: float = 0
    promotion_code_discount_amount: float = 0
    customer_voucher_discount_amount: float | None = None
    promotion_discount_source: str | None = None
    taxable_amount: float = 0
    tax_amount: float = 0
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
    sale_id: str
    tenant_id: str
    branch_id: str
    cashier_session_id: str | None = None
    customer_profile_id: str | None = None
    customer_name: str
    customer_gstin: str | None = None
    invoice_kind: str
    irn_status: str
    invoice_number: str
    issued_on: date
    mrp_total: float = 0
    selling_price_subtotal: float = 0
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    automatic_campaign_name: str | None = None
    automatic_discount_total: float = 0
    promotion_code_discount_total: float = 0
    total_discount: float = 0
    invoice_total: float = 0
    grand_total: float
    promotion_campaign_id: str | None = None
    promotion_code_id: str | None = None
    customer_voucher_id: str | None = None
    gift_card_id: str | None = None
    customer_voucher_name: str | None = None
    gift_card_code: str | None = None
    promotion_code: str | None = None
    promotion_discount_amount: float = 0
    customer_voucher_discount_total: float = 0
    gift_card_amount: float = 0
    store_credit_amount: float = 0
    loyalty_points_redeemed: int = 0
    loyalty_discount_amount: float = 0
    loyalty_points_earned: int = 0
    payment: PaymentResponse
    lines: list[SaleLineResponse]
    tax_lines: list[InvoiceTaxLineResponse]


class SaleRecord(BaseModel):
    sale_id: str
    cashier_session_id: str | None = None
    customer_profile_id: str | None = None
    invoice_number: str
    customer_name: str
    invoice_kind: str
    irn_status: str
    payment_method: str
    automatic_campaign_name: str | None = None
    automatic_discount_total: float = 0
    promotion_code_discount_total: float = 0
    total_discount: float = 0
    invoice_total: float = 0
    grand_total: float
    promotion_campaign_id: str | None = None
    promotion_code_id: str | None = None
    customer_voucher_id: str | None = None
    gift_card_id: str | None = None
    customer_voucher_name: str | None = None
    gift_card_code: str | None = None
    promotion_code: str | None = None
    promotion_discount_amount: float = 0
    customer_voucher_discount_total: float = 0
    gift_card_amount: float = 0
    store_credit_amount: float = 0
    loyalty_points_redeemed: int = 0
    loyalty_discount_amount: float = 0
    loyalty_points_earned: int = 0
    issued_on: date


class SaleListResponse(BaseModel):
    records: list[SaleRecord]


class SaleReturnLineCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SaleReturnCreateRequest(BaseModel):
    cashier_session_id: str
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
    cashier_session_id: str | None = None
    sale_id: str
    status: str
    refund_amount: float
    refund_method: str
    lines: list[SaleReturnLineResponse]
    credit_note: CreditNoteResponse


class SaleReturnRecord(BaseModel):
    sale_return_id: str
    cashier_session_id: str | None = None
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


CheckoutPaymentSessionResponse.model_rebuild()
CheckoutPricePreviewResponse.model_rebuild()
