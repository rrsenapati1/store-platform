"""branch irp profiles and gst export provider fields

Revision ID: 20260414_0021
Revises: 20260414_0020
Create Date: 2026-04-14 22:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0021"
down_revision = "20260414_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branch_irp_profiles",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("api_username", sa.String(length=255), nullable=False),
        sa.Column("encrypted_api_password", sa.String(length=4096), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CONFIGURED"),
        sa.Column("last_validated_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_error_message", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("branch_id", name="uq_branch_irp_profiles_branch"),
    )
    op.create_index("ix_branch_irp_profiles_tenant_id", "branch_irp_profiles", ["tenant_id"])
    op.create_index("ix_branch_irp_profiles_branch_id", "branch_irp_profiles", ["branch_id"])

    op.add_column("gst_export_jobs", sa.Column("provider_name", sa.String(length=64), nullable=True))
    op.add_column("gst_export_jobs", sa.Column("provider_status", sa.String(length=64), nullable=True))
    op.add_column("gst_export_jobs", sa.Column("prepared_payload", sa.JSON(), nullable=True))
    op.add_column("gst_export_jobs", sa.Column("submission_attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("gst_export_jobs", sa.Column("last_submitted_at", sa.DateTime(timezone=False), nullable=True))
    op.add_column("gst_export_jobs", sa.Column("last_error_code", sa.String(length=64), nullable=True))
    op.add_column("gst_export_jobs", sa.Column("last_error_message", sa.String(length=1024), nullable=True))
    op.alter_column("gst_export_jobs", "submission_attempt_count", server_default=None)


def downgrade() -> None:
    op.drop_column("gst_export_jobs", "last_error_message")
    op.drop_column("gst_export_jobs", "last_error_code")
    op.drop_column("gst_export_jobs", "last_submitted_at")
    op.drop_column("gst_export_jobs", "submission_attempt_count")
    op.drop_column("gst_export_jobs", "prepared_payload")
    op.drop_column("gst_export_jobs", "provider_status")
    op.drop_column("gst_export_jobs", "provider_name")

    op.drop_index("ix_branch_irp_profiles_branch_id", table_name="branch_irp_profiles")
    op.drop_index("ix_branch_irp_profiles_tenant_id", table_name="branch_irp_profiles")
    op.drop_table("branch_irp_profiles")
