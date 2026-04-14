"""device claims and installation binding

Revision ID: 20260414_0014
Revises: 20260414_0013
Create Date: 2026-04-14 08:45:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0014"
down_revision = "20260414_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("device_registrations", sa.Column("installation_id", sa.String(length=96), nullable=True))
    op.create_index("ix_device_registrations_installation_id", "device_registrations", ["installation_id"], unique=True)

    op.create_table(
        "device_claims",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("installation_id", sa.String(length=96), nullable=False),
        sa.Column("claim_code", sa.String(length=32), nullable=False),
        sa.Column("runtime_kind", sa.String(length=64), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("operating_system", sa.String(length=64), nullable=True),
        sa.Column("architecture", sa.String(length=64), nullable=True),
        sa.Column("app_version", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approved_device_id", sa.String(length=32), sa.ForeignKey("device_registrations.id"), nullable=True),
        sa.Column("approved_by_user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_device_claims_tenant_id", "device_claims", ["tenant_id"], unique=False)
    op.create_index("ix_device_claims_branch_id", "device_claims", ["branch_id"], unique=False)
    op.create_index("ix_device_claims_installation_id", "device_claims", ["installation_id"], unique=False)
    op.create_index("ix_device_claims_claim_code", "device_claims", ["claim_code"], unique=False)
    op.create_index("ix_device_claims_approved_device_id", "device_claims", ["approved_device_id"], unique=False)
    op.create_index("ix_device_claims_approved_by_user_id", "device_claims", ["approved_by_user_id"], unique=False)
    op.create_index("uq_device_claims_branch_installation", "device_claims", ["branch_id", "installation_id"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_device_claims_branch_installation", table_name="device_claims")
    op.drop_index("ix_device_claims_approved_by_user_id", table_name="device_claims")
    op.drop_index("ix_device_claims_approved_device_id", table_name="device_claims")
    op.drop_index("ix_device_claims_claim_code", table_name="device_claims")
    op.drop_index("ix_device_claims_installation_id", table_name="device_claims")
    op.drop_index("ix_device_claims_branch_id", table_name="device_claims")
    op.drop_index("ix_device_claims_tenant_id", table_name="device_claims")
    op.drop_table("device_claims")

    op.drop_index("ix_device_registrations_installation_id", table_name="device_registrations")
    op.drop_column("device_registrations", "installation_id")
