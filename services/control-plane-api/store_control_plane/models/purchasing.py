from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    gstin: Mapped[str | None] = mapped_column(String(32), default=None)
    payment_terms_days: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    purchase_order_number: Mapped[str] = mapped_column(String(64), index=True)
    approval_status: Mapped[str] = mapped_column(String(32), default="NOT_REQUESTED")
    subtotal: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
    grand_total: Mapped[float] = mapped_column(default=0.0)
    approval_requested_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    approval_decision_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    approval_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    approval_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class PurchaseOrderLine(Base, TimestampMixin):
    __tablename__ = "purchase_order_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    purchase_order_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_cost: Mapped[float] = mapped_column(default=0.0)
    gst_rate: Mapped[float] = mapped_column(default=0.0)
    line_total: Mapped[float] = mapped_column(default=0.0)
    tax_total: Mapped[float] = mapped_column(default=0.0)
