from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class GstExportJob(Base, TimestampMixin):
    __tablename__ = "gst_export_jobs"
    __table_args__ = (
        UniqueConstraint("sale_id", name="uq_gst_export_jobs_sale"),
        UniqueConstraint("branch_id", "invoice_number", name="uq_gst_export_jobs_branch_invoice_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    sales_invoice_id: Mapped[str] = mapped_column(ForeignKey("sales_invoices.id", ondelete="CASCADE"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(64), index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    seller_gstin: Mapped[str] = mapped_column(String(32))
    buyer_gstin: Mapped[str | None] = mapped_column(String(32), default=None)
    hsn_sac_summary: Mapped[str] = mapped_column(String(255))
    grand_total: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="IRN_PENDING")


class IrnAttachment(Base, TimestampMixin):
    __tablename__ = "irn_attachments"
    __table_args__ = (
        UniqueConstraint("gst_export_job_id", name="uq_irn_attachments_job"),
        UniqueConstraint("sales_invoice_id", name="uq_irn_attachments_invoice"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    gst_export_job_id: Mapped[str] = mapped_column(ForeignKey("gst_export_jobs.id", ondelete="CASCADE"), index=True)
    sales_invoice_id: Mapped[str] = mapped_column(ForeignKey("sales_invoices.id", ondelete="CASCADE"), index=True)
    irn: Mapped[str] = mapped_column(String(128))
    ack_no: Mapped[str] = mapped_column(String(128))
    signed_qr_payload: Mapped[str] = mapped_column(String(2048))
