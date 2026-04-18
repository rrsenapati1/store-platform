"""add hub sync status foundation

Revision ID: 20260419_0044
Revises: 20260418_0043
Create Date: 2026-04-19 05:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260419_0044"
down_revision = "20260418_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hub_sync_status",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("hub_device_id", sa.String(length=32), nullable=True),
        sa.Column("source_device_id", sa.String(length=128), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_successful_push_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_successful_pull_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_successful_push_mutations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("last_pull_cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("branch_cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_mutation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("connected_spoke_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("local_outbox_depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("oldest_unsynced_mutation_age_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("runtime_state", sa.String(length=32), nullable=False, server_default="CURRENT"),
        sa.Column("last_local_spoke_sync_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hub_device_id"], ["device_registrations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "branch_id", name="uq_hub_sync_status_scope"),
    )
    op.create_index("ix_hub_sync_status_tenant_id", "hub_sync_status", ["tenant_id"], unique=False)
    op.create_index("ix_hub_sync_status_branch_id", "hub_sync_status", ["branch_id"], unique=False)
    op.alter_column("hub_sync_status", "last_successful_push_mutations", server_default=None)
    op.alter_column("hub_sync_status", "last_pull_cursor", server_default=None)
    op.alter_column("hub_sync_status", "branch_cursor", server_default=None)
    op.alter_column("hub_sync_status", "pending_mutation_count", server_default=None)
    op.alter_column("hub_sync_status", "connected_spoke_count", server_default=None)
    op.alter_column("hub_sync_status", "local_outbox_depth", server_default=None)
    op.alter_column("hub_sync_status", "oldest_unsynced_mutation_age_seconds", server_default=None)
    op.alter_column("hub_sync_status", "runtime_state", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_hub_sync_status_branch_id", table_name="hub_sync_status")
    op.drop_index("ix_hub_sync_status_tenant_id", table_name="hub_sync_status")
    op.drop_table("hub_sync_status")
