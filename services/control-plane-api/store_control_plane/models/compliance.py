from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
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
    provider_name: Mapped[str | None] = mapped_column(String(64), default=None)
    provider_status: Mapped[str | None] = mapped_column(String(64), default=None)
    prepared_payload: Mapped[dict | None] = mapped_column(JSON, default=None)
    submission_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_error_code: Mapped[str | None] = mapped_column(String(64), default=None)
    last_error_message: Mapped[str | None] = mapped_column(String(1024), default=None)


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


class BranchIrpProfile(Base, TimestampMixin):
    __tablename__ = "branch_irp_profiles"
    __table_args__ = (
        UniqueConstraint("branch_id", name="uq_branch_irp_profiles_branch"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    provider_name: Mapped[str] = mapped_column(String(64))
    api_username: Mapped[str] = mapped_column(String(255))
    encrypted_api_password: Mapped[str] = mapped_column(String(4096))
    status: Mapped[str] = mapped_column(String(32), default="CONFIGURED")
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_error_message: Mapped[str | None] = mapped_column(String(1024), default=None)
