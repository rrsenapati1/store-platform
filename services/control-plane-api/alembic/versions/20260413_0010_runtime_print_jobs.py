"""runtime print queue foundation

Revision ID: 20260413_0010
Revises: 20260413_0009
Create Date: 2026-04-13 23:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0010"
down_revision = "20260413_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "print_jobs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(length=32), sa.ForeignKey("device_registrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_type", sa.String(length=32), nullable=False),
        sa.Column("reference_id", sa.String(length=32), nullable=False),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("copies", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="QUEUED"),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_print_jobs_tenant_id", "print_jobs", ["tenant_id"])
    op.create_index("ix_print_jobs_branch_id", "print_jobs", ["branch_id"])
    op.create_index("ix_print_jobs_device_id", "print_jobs", ["device_id"])
    op.create_index("ix_print_jobs_reference_id", "print_jobs", ["reference_id"])


def downgrade() -> None:
    op.drop_index("ix_print_jobs_reference_id", table_name="print_jobs")
    op.drop_index("ix_print_jobs_device_id", table_name="print_jobs")
    op.drop_index("ix_print_jobs_branch_id", table_name="print_jobs")
    op.drop_index("ix_print_jobs_tenant_id", table_name="print_jobs")
    op.drop_table("print_jobs")
