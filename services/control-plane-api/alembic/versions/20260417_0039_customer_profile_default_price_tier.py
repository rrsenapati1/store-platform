"""add customer profile default price tier

Revision ID: 20260417_0039
Revises: 20260417_0038
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0039"
down_revision = "20260417_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customer_profiles",
        sa.Column("default_price_tier_id", sa.String(length=32), nullable=True),
    )
    op.create_foreign_key(
        "fk_customer_profiles_default_price_tier_id",
        "customer_profiles",
        "price_tiers",
        ["default_price_tier_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_customer_profiles_default_price_tier_id"),
        "customer_profiles",
        ["default_price_tier_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_customer_profiles_default_price_tier_id"), table_name="customer_profiles")
    op.drop_constraint("fk_customer_profiles_default_price_tier_id", "customer_profiles", type_="foreignkey")
    op.drop_column("customer_profiles", "default_price_tier_id")
