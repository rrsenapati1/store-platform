from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    cashier_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("branch_cashier_sessions.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    customer_profile_id: Mapped[str | None] = mapped_column(ForeignKey("customer_profiles.id", ondelete="SET NULL"), default=None, index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_gstin: Mapped[str | None] = mapped_column(String(32), default=None)
    automatic_campaign_name: Mapped[str | None] = mapped_column(String(255), default=None)
    automatic_discount_total: Mapped[float] = mapped_column(default=0.0)
    promotion_campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("promotion_campaigns.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    promotion_code_id: Mapped[str | None] = mapped_column(
        ForeignKey("promotion_codes.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    customer_voucher_id: Mapped[str | None] = mapped_column(
        ForeignKey("customer_voucher_assignments.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    gift_card_id: Mapped[str | None] = mapped_column(
        ForeignKey("gift_cards.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    customer_voucher_name: Mapped[str | None] = mapped_column(String(255), default=None)
    gift_card_code: Mapped[str | None] = mapped_column(String(64), default=None)
    gift_card_amount: Mapped[float] = mapped_column(default=0.0)
    promotion_code: Mapped[str | None] = mapped_column(String(64), default=None)
    promotion_discount_amount: Mapped[float] = mapped_column(default=0.0)
    promotion_code_discount_total: Mapped[float] = mapped_column(default=0.0)
    customer_voucher_discount_total: Mapped[float] = mapped_column(default=0.0)
    invoice_kind: Mapped[str] = mapped_column(String(16))
    irn_status: Mapped[str] = mapped_column(String(32), default="NOT_REQUIRED")
    loyalty_points_redeemed: Mapped[int] = mapped_column(default=0)
    loyalty_discount_amount: Mapped[float] = mapped_column(default=0.0)
    loyalty_points_earned: Mapped[int] = mapped_column(default=0)
    mrp_total: Mapped[float] = mapped_column(default=0.0)
    selling_price_subtotal: Mapped[float] = mapped_column(default=0.0)
    total_discount: Mapped[float] = mapped_column(default=0.0)
    invoice_total: Mapped[float] = mapped_column(default=0.0)
    subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)


class SaleLine(Base, TimestampMixin):
    __tablename__ = "sale_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    mrp: Mapped[float] = mapped_column(default=0.0)
    unit_selling_price: Mapped[float] = mapped_column(default=0.0)
    unit_price: Mapped[float] = mapped_column(default=0.0)
    gst_rate: Mapped[float] = mapped_column(default=0.0)
    automatic_discount_amount: Mapped[float] = mapped_column(default=0.0)
    promotion_code_discount_amount: Mapped[float] = mapped_column(default=0.0)
    customer_voucher_discount_amount: Mapped[float] = mapped_column(default=0.0)
    promotion_discount_source: Mapped[str | None] = mapped_column(String(64), default=None)
    serial_numbers: Mapped[list[str]] = mapped_column(JSON, default=list)
    compliance_profile: Mapped[str] = mapped_column(String(32), default="NONE")
    compliance_capture: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    taxable_amount: Mapped[float] = mapped_column(default=0.0)
    tax_amount: Mapped[float] = mapped_column(default=0.0)
    line_subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    line_total: Mapped[float] = mapped_column(default=0.0)


class SalesInvoice(Base, TimestampMixin):
    __tablename__ = "sales_invoices"
    __table_args__ = (
        UniqueConstraint("branch_id", "invoice_number", name="uq_sales_invoices_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True, unique=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(64), index=True)
    issued_on: Mapped[date] = mapped_column(Date())
    subtotal: Mapped[float] = mapped_column(default=0.0)
    cgst_total: Mapped[float] = mapped_column(default=0.0)
    sgst_total: Mapped[float] = mapped_column(default=0.0)
    igst_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)


class InvoiceTaxLine(Base, TimestampMixin):
    __tablename__ = "invoice_tax_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sales_invoice_id: Mapped[str] = mapped_column(ForeignKey("sales_invoices.id", ondelete="CASCADE"), index=True)
    tax_type: Mapped[str] = mapped_column(String(16))
    tax_rate: Mapped[float] = mapped_column(default=0.0)
    taxable_amount: Mapped[float] = mapped_column(default=0.0)
    tax_amount: Mapped[float] = mapped_column(default=0.0)


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    payment_method: Mapped[str] = mapped_column(String(32))
    amount: Mapped[float] = mapped_column(default=0.0)


class CheckoutPaymentSession(Base, TimestampMixin):
    __tablename__ = "checkout_payment_sessions"
    __table_args__ = (
        UniqueConstraint("provider_name", "provider_order_id", name="uq_checkout_payment_sessions_provider_order"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    cashier_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("branch_cashier_sessions.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    customer_profile_id: Mapped[str | None] = mapped_column(ForeignKey("customer_profiles.id", ondelete="SET NULL"), default=None, index=True)
    provider_name: Mapped[str] = mapped_column(String(32), index=True)
    provider_order_id: Mapped[str] = mapped_column(String(255), index=True)
    provider_payment_session_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
    payment_method: Mapped[str] = mapped_column(String(64))
    handoff_surface: Mapped[str] = mapped_column(String(32), default="BRANDED_UPI_QR")
    provider_payment_mode: Mapped[str] = mapped_column(String(64), default="cashfree_upi")
    lifecycle_status: Mapped[str] = mapped_column(String(32), index=True)
    provider_status: Mapped[str] = mapped_column(String(64), index=True)
    order_amount: Mapped[float] = mapped_column(default=0.0)
    currency_code: Mapped[str] = mapped_column(String(8), default="INR")
    cart_summary_hash: Mapped[str] = mapped_column(String(64), index=True)
    cart_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_gstin: Mapped[str | None] = mapped_column(String(32), default=None)
    action_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    action_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    qr_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    qr_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    provider_response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    last_error_message: Mapped[str | None] = mapped_column(String(1024), default=None)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    finalized_sale_id: Mapped[str | None] = mapped_column(ForeignKey("sales.id", ondelete="SET NULL"), default=None, index=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class SaleReturn(Base, TimestampMixin):
    __tablename__ = "sale_returns"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    cashier_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("branch_cashier_sessions.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32))
    refund_amount: Mapped[float] = mapped_column(default=0.0)
    refund_method: Mapped[str] = mapped_column(String(32))


class SaleReturnLine(Base, TimestampMixin):
    __tablename__ = "sale_return_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sale_return_id: Mapped[str] = mapped_column(ForeignKey("sale_returns.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_price: Mapped[float] = mapped_column(default=0.0)
    gst_rate: Mapped[float] = mapped_column(default=0.0)
    line_subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    line_total: Mapped[float] = mapped_column(default=0.0)


class CreditNote(Base, TimestampMixin):
    __tablename__ = "credit_notes"
    __table_args__ = (
        UniqueConstraint("branch_id", "credit_note_number", name="uq_credit_notes_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sale_return_id: Mapped[str] = mapped_column(ForeignKey("sale_returns.id", ondelete="CASCADE"), index=True, unique=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    credit_note_number: Mapped[str] = mapped_column(String(64), index=True)
    issued_on: Mapped[date] = mapped_column(Date())
    subtotal: Mapped[float] = mapped_column(default=0.0)
    cgst_total: Mapped[float] = mapped_column(default=0.0)
    sgst_total: Mapped[float] = mapped_column(default=0.0)
    igst_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)


class CreditNoteTaxLine(Base, TimestampMixin):
    __tablename__ = "credit_note_tax_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    credit_note_id: Mapped[str] = mapped_column(ForeignKey("credit_notes.id", ondelete="CASCADE"), index=True)
    tax_type: Mapped[str] = mapped_column(String(16))
    tax_rate: Mapped[float] = mapped_column(default=0.0)
    taxable_amount: Mapped[float] = mapped_column(default=0.0)
    tax_amount: Mapped[float] = mapped_column(default=0.0)


class ExchangeOrder(Base, TimestampMixin):
    __tablename__ = "exchange_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    original_sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    replacement_sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    sale_return_id: Mapped[str] = mapped_column(ForeignKey("sale_returns.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32))
    balance_direction: Mapped[str] = mapped_column(String(32))
    balance_amount: Mapped[float] = mapped_column(default=0.0)
    settlement_method: Mapped[str] = mapped_column(String(32))
