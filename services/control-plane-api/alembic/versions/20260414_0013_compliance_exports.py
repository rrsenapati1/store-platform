"""sales invoice compliance exports

Revision ID: 20260414_0013
Revises: 20260414_0012
Create Date: 2026-04-14 18:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0013"
down_revision = "20260414_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gst_export_jobs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_id", sa.String(length=32), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sales_invoice_id", sa.String(length=32), sa.ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_number", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("seller_gstin", sa.String(length=32), nullable=False),
        sa.Column("buyer_gstin", sa.String(length=32), nullable=True),
        sa.Column("hsn_sac_summary", sa.String(length=255), nullable=False),
        sa.Column("grand_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="IRN_PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("sale_id", name="uq_gst_export_jobs_sale"),
        sa.UniqueConstraint("branch_id", "invoice_number", name="uq_gst_export_jobs_branch_invoice_number"),
    )
    op.create_index("ix_gst_export_jobs_tenant_id", "gst_export_jobs", ["tenant_id"])
    op.create_index("ix_gst_export_jobs_branch_id", "gst_export_jobs", ["branch_id"])
    op.create_index("ix_gst_export_jobs_sale_id", "gst_export_jobs", ["sale_id"])
    op.create_index("ix_gst_export_jobs_sales_invoice_id", "gst_export_jobs", ["sales_invoice_id"])
    op.create_index("ix_gst_export_jobs_invoice_number", "gst_export_jobs", ["invoice_number"])

    op.create_table(
        "irn_attachments",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gst_export_job_id", sa.String(length=32), sa.ForeignKey("gst_export_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sales_invoice_id", sa.String(length=32), sa.ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("irn", sa.String(length=128), nullable=False),
        sa.Column("ack_no", sa.String(length=128), nullable=False),
        sa.Column("signed_qr_payload", sa.String(length=2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("gst_export_job_id", name="uq_irn_attachments_job"),
        sa.UniqueConstraint("sales_invoice_id", name="uq_irn_attachments_invoice"),
    )
    op.create_index("ix_irn_attachments_tenant_id", "irn_attachments", ["tenant_id"])
    op.create_index("ix_irn_attachments_branch_id", "irn_attachments", ["branch_id"])
    op.create_index("ix_irn_attachments_gst_export_job_id", "irn_attachments", ["gst_export_job_id"])
    op.create_index("ix_irn_attachments_sales_invoice_id", "irn_attachments", ["sales_invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_irn_attachments_sales_invoice_id", table_name="irn_attachments")
    op.drop_index("ix_irn_attachments_gst_export_job_id", table_name="irn_attachments")
    op.drop_index("ix_irn_attachments_branch_id", table_name="irn_attachments")
    op.drop_index("ix_irn_attachments_tenant_id", table_name="irn_attachments")
    op.drop_table("irn_attachments")

    op.drop_index("ix_gst_export_jobs_invoice_number", table_name="gst_export_jobs")
    op.drop_index("ix_gst_export_jobs_sales_invoice_id", table_name="gst_export_jobs")
    op.drop_index("ix_gst_export_jobs_sale_id", table_name="gst_export_jobs")
    op.drop_index("ix_gst_export_jobs_branch_id", table_name="gst_export_jobs")
    op.drop_index("ix_gst_export_jobs_tenant_id", table_name="gst_export_jobs")
    op.drop_table("gst_export_jobs")
