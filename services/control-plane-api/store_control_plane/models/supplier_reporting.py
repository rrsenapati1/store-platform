from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class VendorDispute(Base, TimestampMixin):
    __tablename__ = "vendor_disputes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    goods_receipt_id: Mapped[str | None] = mapped_column(ForeignKey("goods_receipts.id", ondelete="CASCADE"), default=None, index=True)
    purchase_invoice_id: Mapped[str | None] = mapped_column(ForeignKey("purchase_invoices.id", ondelete="CASCADE"), default=None, index=True)
    dispute_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    opened_on: Mapped[date] = mapped_column(Date())
    resolved_on: Mapped[date | None] = mapped_column(Date(), default=None)
    note: Mapped[str | None] = mapped_column(String(1024), default=None)
    resolution_note: Mapped[str | None] = mapped_column(String(1024), default=None)


class SupplierReportSnapshot(Base, TimestampMixin):
    __tablename__ = "supplier_report_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "branch_id",
            "supplier_id",
            "report_type",
            "report_date",
            name="uq_supplier_report_snapshots_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), default=None, index=True)
    report_type: Mapped[str] = mapped_column(String(64), index=True)
    report_date: Mapped[date | None] = mapped_column(Date(), default=None, index=True)
    source_watermark: Mapped[str] = mapped_column(String(255), default="")
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    is_dirty: Mapped[bool] = mapped_column(Boolean(), default=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
