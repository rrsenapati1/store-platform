from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class PurchaseInvoice(Base, TimestampMixin):
    __tablename__ = "purchase_invoices"
    __table_args__ = (
        UniqueConstraint("goods_receipt_id", name="uq_purchase_invoices_goods_receipt"),
        UniqueConstraint("branch_id", "invoice_number", name="uq_purchase_invoices_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    goods_receipt_id: Mapped[str] = mapped_column(ForeignKey("goods_receipts.id", ondelete="CASCADE"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(64), index=True)
    invoice_date: Mapped[date] = mapped_column(Date())
    due_date: Mapped[date] = mapped_column(Date())
    payment_terms_days: Mapped[int] = mapped_column(default=0)
    subtotal: Mapped[float] = mapped_column(default=0.0)
    cgst_total: Mapped[float] = mapped_column(default=0.0)
    sgst_total: Mapped[float] = mapped_column(default=0.0)
    igst_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)


class PurchaseInvoiceLine(Base, TimestampMixin):
    __tablename__ = "purchase_invoice_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    purchase_invoice_id: Mapped[str] = mapped_column(ForeignKey("purchase_invoices.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_cost: Mapped[float] = mapped_column(default=0.0)
    gst_rate: Mapped[float] = mapped_column(default=0.0)
    line_subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    line_total: Mapped[float] = mapped_column(default=0.0)


class SupplierReturn(Base, TimestampMixin):
    __tablename__ = "supplier_returns"
    __table_args__ = (
        UniqueConstraint("branch_id", "supplier_credit_note_number", name="uq_supplier_returns_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    purchase_invoice_id: Mapped[str] = mapped_column(ForeignKey("purchase_invoices.id", ondelete="CASCADE"), index=True)
    supplier_credit_note_number: Mapped[str] = mapped_column(String(64), index=True)
    issued_on: Mapped[date] = mapped_column(Date())
    subtotal: Mapped[float] = mapped_column(default=0.0)
    cgst_total: Mapped[float] = mapped_column(default=0.0)
    sgst_total: Mapped[float] = mapped_column(default=0.0)
    igst_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)


class SupplierReturnLine(Base, TimestampMixin):
    __tablename__ = "supplier_return_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    supplier_return_id: Mapped[str] = mapped_column(ForeignKey("supplier_returns.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_cost: Mapped[float] = mapped_column(default=0.0)
    gst_rate: Mapped[float] = mapped_column(default=0.0)
    line_subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    line_total: Mapped[float] = mapped_column(default=0.0)


class SupplierPayment(Base, TimestampMixin):
    __tablename__ = "supplier_payments"
    __table_args__ = (
        UniqueConstraint("branch_id", "payment_number", name="uq_supplier_payments_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    purchase_invoice_id: Mapped[str] = mapped_column(ForeignKey("purchase_invoices.id", ondelete="CASCADE"), index=True)
    payment_number: Mapped[str] = mapped_column(String(64), index=True)
    paid_on: Mapped[date] = mapped_column(Date())
    payment_method: Mapped[str] = mapped_column(String(64))
    amount: Mapped[float] = mapped_column(default=0.0)
    reference: Mapped[str | None] = mapped_column(String(255), default=None)
