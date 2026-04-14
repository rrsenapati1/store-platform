"""store desktop activation records

Revision ID: 20260414_0015
Revises: 20260414_0014
Create Date: 2026-04-14 10:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0015"
down_revision = "20260414_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "store_desktop_activations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(length=32), sa.ForeignKey("device_registrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("staff_profile_id", sa.String(length=32), sa.ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activation_code_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("issued_by_user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_store_desktop_activations_tenant_id", "store_desktop_activations", ["tenant_id"], unique=False)
    op.create_index("ix_store_desktop_activations_branch_id", "store_desktop_activations", ["branch_id"], unique=False)
    op.create_index("ix_store_desktop_activations_device_id", "store_desktop_activations", ["device_id"], unique=False)
    op.create_index("ix_store_desktop_activations_staff_profile_id", "store_desktop_activations", ["staff_profile_id"], unique=False)
    op.create_index("ix_store_desktop_activations_activation_code_hash", "store_desktop_activations", ["activation_code_hash"], unique=False)
    op.create_index("ix_store_desktop_activations_issued_by_user_id", "store_desktop_activations", ["issued_by_user_id"], unique=False)
    op.create_index("ix_store_desktop_activations_expires_at", "store_desktop_activations", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_store_desktop_activations_expires_at", table_name="store_desktop_activations")
    op.drop_index("ix_store_desktop_activations_issued_by_user_id", table_name="store_desktop_activations")
    op.drop_index("ix_store_desktop_activations_activation_code_hash", table_name="store_desktop_activations")
    op.drop_index("ix_store_desktop_activations_staff_profile_id", table_name="store_desktop_activations")
    op.drop_index("ix_store_desktop_activations_device_id", table_name="store_desktop_activations")
    op.drop_index("ix_store_desktop_activations_branch_id", table_name="store_desktop_activations")
    op.drop_index("ix_store_desktop_activations_tenant_id", table_name="store_desktop_activations")
    op.drop_table("store_desktop_activations")
