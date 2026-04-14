"""operations jobs

Revision ID: 20260414_0020
Revises: 20260414_0019
Create Date: 2026-04-14 18:25:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0020"
down_revision = "20260414_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operations_jobs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="QUEUED"),
        sa.Column("queue_key", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("run_after", sa.DateTime(timezone=False), nullable=False),
        sa.Column("leased_until", sa.DateTime(timezone=False), nullable=True),
        sa.Column("lease_token", sa.String(length=128), nullable=True),
        sa.Column("last_error", sa.String(length=1024), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index("ix_operations_jobs_tenant_id", "operations_jobs", ["tenant_id"])
    op.create_index("ix_operations_jobs_branch_id", "operations_jobs", ["branch_id"])
    op.create_index("ix_operations_jobs_created_by_user_id", "operations_jobs", ["created_by_user_id"])
    op.create_index("ix_operations_jobs_job_type", "operations_jobs", ["job_type"])
    op.create_index("ix_operations_jobs_status", "operations_jobs", ["status"])
    op.create_index("ix_operations_jobs_queue_key", "operations_jobs", ["queue_key"])
    op.create_index("ix_operations_jobs_run_after", "operations_jobs", ["run_after"])
    op.create_index("ix_operations_jobs_leased_until", "operations_jobs", ["leased_until"])
    op.create_index("ix_operations_jobs_lease_token", "operations_jobs", ["lease_token"])
    op.create_index("ix_operations_jobs_dead_lettered_at", "operations_jobs", ["dead_lettered_at"])
    op.alter_column("operations_jobs", "status", server_default=None)
    op.alter_column("operations_jobs", "payload", server_default=None)
    op.alter_column("operations_jobs", "attempt_count", server_default=None)
    op.alter_column("operations_jobs", "max_attempts", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_operations_jobs_dead_lettered_at", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_lease_token", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_leased_until", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_run_after", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_queue_key", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_status", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_job_type", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_created_by_user_id", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_branch_id", table_name="operations_jobs")
    op.drop_index("ix_operations_jobs_tenant_id", table_name="operations_jobs")
    op.drop_table("operations_jobs")
