from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_gstin: Mapped[str | None] = mapped_column(String(32), default=None)
    invoice_kind: Mapped[str] = mapped_column(String(16))
    irn_status: Mapped[str] = mapped_column(String(32), default="NOT_REQUIRED")
    subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)


class SaleLine(Base, TimestampMixin):
    __tablename__ = "sale_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_price: Mapped[float] = mapped_column(default=0.0)
    gst_rate: Mapped[float] = mapped_column(default=0.0)
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


class SaleReturn(Base, TimestampMixin):
    __tablename__ = "sale_returns"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
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
