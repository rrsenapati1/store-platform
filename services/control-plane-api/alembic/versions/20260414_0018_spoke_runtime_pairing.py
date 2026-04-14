"""spoke runtime pairing

Revision ID: 20260414_0018
Revises: 20260414_0017
Create Date: 2026-04-14 18:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0018"
down_revision = "20260414_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "device_registrations",
        sa.Column("runtime_profile", sa.String(length=64), nullable=False, server_default="desktop_spoke"),
    )
    op.alter_column("device_registrations", "runtime_profile", server_default=None)

    op.execute("UPDATE device_registrations SET runtime_profile = 'branch_hub' WHERE is_branch_hub = true")

    op.create_table(
        "spoke_runtime_activations",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("hub_device_id", sa.String(length=32), nullable=False),
        sa.Column("activation_code_hash", sa.String(length=128), nullable=False),
        sa.Column("pairing_mode", sa.String(length=32), nullable=False, server_default="approval_code"),
        sa.Column("runtime_profile", sa.String(length=64), nullable=False, server_default="desktop_spoke"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ISSUED"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("redeemed_spoke_installation_id", sa.String(length=96), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hub_device_id"], ["device_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_spoke_runtime_activations_tenant_id",
        "spoke_runtime_activations",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_spoke_runtime_activations_branch_id",
        "spoke_runtime_activations",
        ["branch_id"],
        unique=False,
    )
    op.create_index(
        "ix_spoke_runtime_activations_hub_device_id",
        "spoke_runtime_activations",
        ["hub_device_id"],
        unique=False,
    )
    op.create_index(
        "ix_spoke_runtime_activations_activation_code_hash",
        "spoke_runtime_activations",
        ["activation_code_hash"],
        unique=False,
    )
    op.create_index(
        "ix_spoke_runtime_activations_expires_at",
        "spoke_runtime_activations",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_spoke_runtime_activations_redeemed_spoke_installation_id",
        "spoke_runtime_activations",
        ["redeemed_spoke_installation_id"],
        unique=False,
    )
    op.alter_column("spoke_runtime_activations", "pairing_mode", server_default=None)
    op.alter_column("spoke_runtime_activations", "runtime_profile", server_default=None)
    op.alter_column("spoke_runtime_activations", "status", server_default=None)


def downgrade() -> None:
    op.drop_index(
        "ix_spoke_runtime_activations_redeemed_spoke_installation_id",
        table_name="spoke_runtime_activations",
    )
    op.drop_index("ix_spoke_runtime_activations_expires_at", table_name="spoke_runtime_activations")
    op.drop_index(
        "ix_spoke_runtime_activations_activation_code_hash",
        table_name="spoke_runtime_activations",
    )
    op.drop_index("ix_spoke_runtime_activations_hub_device_id", table_name="spoke_runtime_activations")
    op.drop_index("ix_spoke_runtime_activations_branch_id", table_name="spoke_runtime_activations")
    op.drop_index("ix_spoke_runtime_activations_tenant_id", table_name="spoke_runtime_activations")
    op.drop_table("spoke_runtime_activations")
    op.drop_column("device_registrations", "runtime_profile")
