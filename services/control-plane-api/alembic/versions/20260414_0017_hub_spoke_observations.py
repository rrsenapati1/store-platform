"""hub spoke observations

Revision ID: 20260414_0017
Revises: 20260414_0016
Create Date: 2026-04-14 14:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0017"
down_revision = "20260414_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hub_spoke_observations",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("hub_device_id", sa.String(length=32), nullable=False),
        sa.Column("spoke_device_id", sa.String(length=128), nullable=False),
        sa.Column("runtime_kind", sa.String(length=64), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("operating_system", sa.String(length=64), nullable=True),
        sa.Column("app_version", sa.String(length=64), nullable=True),
        sa.Column("connection_state", sa.String(length=32), nullable=False, server_default="DISCOVERED"),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_local_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hub_device_id"], ["device_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "branch_id",
            "hub_device_id",
            "spoke_device_id",
            name="uq_hub_spoke_observation_scope",
        ),
    )
    op.create_index("ix_hub_spoke_observations_tenant_id", "hub_spoke_observations", ["tenant_id"], unique=False)
    op.create_index("ix_hub_spoke_observations_branch_id", "hub_spoke_observations", ["branch_id"], unique=False)
    op.create_index("ix_hub_spoke_observations_hub_device_id", "hub_spoke_observations", ["hub_device_id"], unique=False)
    op.create_index("ix_hub_spoke_observations_spoke_device_id", "hub_spoke_observations", ["spoke_device_id"], unique=False)
    op.alter_column("hub_spoke_observations", "connection_state", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_hub_spoke_observations_spoke_device_id", table_name="hub_spoke_observations")
    op.drop_index("ix_hub_spoke_observations_hub_device_id", table_name="hub_spoke_observations")
    op.drop_index("ix_hub_spoke_observations_branch_id", table_name="hub_spoke_observations")
    op.drop_index("ix_hub_spoke_observations_tenant_id", table_name="hub_spoke_observations")
    op.drop_table("hub_spoke_observations")
