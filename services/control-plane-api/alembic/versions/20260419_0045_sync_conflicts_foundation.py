"""add sync conflicts foundation

Revision ID: 20260419_0045
Revises: 20260419_0044
Create Date: 2026-04-19 05:38:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260419_0045"
down_revision = "20260419_0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_conflicts",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("device_id", sa.String(length=32), nullable=False),
        sa.Column("source_idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("conflict_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_hash", sa.String(length=128), nullable=False),
        sa.Column("table_name", sa.String(length=64), nullable=False),
        sa.Column("record_id", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
        sa.Column("resolution", sa.String(length=64), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("client_version", sa.Integer(), nullable=True),
        sa.Column("server_version", sa.Integer(), nullable=True),
        sa.Column("retry_strategy", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="OPEN"),
        sa.Column("resolved_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("resolution_method", sa.String(length=64), nullable=True),
        sa.Column("resolved_by_idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("resolved_by_device_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_id"], ["device_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_conflicts_tenant_id", "sync_conflicts", ["tenant_id"], unique=False)
    op.create_index("ix_sync_conflicts_branch_id", "sync_conflicts", ["branch_id"], unique=False)
    op.create_index("ix_sync_conflicts_device_id", "sync_conflicts", ["device_id"], unique=False)
    op.create_index(
        "ix_sync_conflicts_source_idempotency_key",
        "sync_conflicts",
        ["source_idempotency_key"],
        unique=False,
    )
    op.create_index("ix_sync_conflicts_table_name", "sync_conflicts", ["table_name"], unique=False)
    op.create_index("ix_sync_conflicts_record_id", "sync_conflicts", ["record_id"], unique=False)
    op.alter_column("sync_conflicts", "conflict_index", server_default=None)
    op.alter_column("sync_conflicts", "reason", server_default=None)
    op.alter_column("sync_conflicts", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_sync_conflicts_record_id", table_name="sync_conflicts")
    op.drop_index("ix_sync_conflicts_table_name", table_name="sync_conflicts")
    op.drop_index("ix_sync_conflicts_source_idempotency_key", table_name="sync_conflicts")
    op.drop_index("ix_sync_conflicts_device_id", table_name="sync_conflicts")
    op.drop_index("ix_sync_conflicts_branch_id", table_name="sync_conflicts")
    op.drop_index("ix_sync_conflicts_tenant_id", table_name="sync_conflicts")
    op.drop_table("sync_conflicts")
