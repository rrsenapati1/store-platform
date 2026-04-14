"""workforce foundation

Revision ID: 20260413_0002
Revises: 20260413_0001
Create Date: 2026-04-13 09:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260413_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_profiles",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("primary_branch_id", sa.String(length=32), sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_staff_profiles_tenant_id", "staff_profiles", ["tenant_id"], unique=False)
    op.create_index("ix_staff_profiles_user_id", "staff_profiles", ["user_id"], unique=False)
    op.create_index("ix_staff_profiles_primary_branch_id", "staff_profiles", ["primary_branch_id"], unique=False)
    op.create_index("ix_staff_profiles_email", "staff_profiles", ["email"], unique=False)
    op.create_index("uq_staff_profiles_tenant_email", "staff_profiles", ["tenant_id", "email"], unique=True)

    op.create_table(
        "device_registrations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_staff_profile_id", sa.String(length=32), sa.ForeignKey("staff_profiles.id"), nullable=True),
        sa.Column("device_name", sa.String(length=255), nullable=False),
        sa.Column("device_code", sa.String(length=64), nullable=False),
        sa.Column("session_surface", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_device_registrations_tenant_id", "device_registrations", ["tenant_id"], unique=False)
    op.create_index("ix_device_registrations_branch_id", "device_registrations", ["branch_id"], unique=False)
    op.create_index("ix_device_registrations_assigned_staff_profile_id", "device_registrations", ["assigned_staff_profile_id"], unique=False)
    op.create_index("ix_device_registrations_device_code", "device_registrations", ["device_code"], unique=False)
    op.create_index("uq_device_registrations_branch_code", "device_registrations", ["branch_id", "device_code"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_device_registrations_branch_code", table_name="device_registrations")
    op.drop_index("ix_device_registrations_device_code", table_name="device_registrations")
    op.drop_index("ix_device_registrations_assigned_staff_profile_id", table_name="device_registrations")
    op.drop_index("ix_device_registrations_branch_id", table_name="device_registrations")
    op.drop_index("ix_device_registrations_tenant_id", table_name="device_registrations")
    op.drop_table("device_registrations")

    op.drop_index("uq_staff_profiles_tenant_email", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_email", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_primary_branch_id", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_user_id", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_tenant_id", table_name="staff_profiles")
    op.drop_table("staff_profiles")
