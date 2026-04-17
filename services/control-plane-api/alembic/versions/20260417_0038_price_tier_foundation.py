"""add price tier foundation

Revision ID: 20260417_0038
Revises: 20260417_0037
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0038"
down_revision = "20260417_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_tiers",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_price_tiers_tenant_code"),
    )
    op.create_index(op.f("ix_price_tiers_tenant_id"), "price_tiers", ["tenant_id"], unique=False)

    op.create_table(
        "branch_price_tier_prices",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("price_tier_id", sa.String(length=32), nullable=False),
        sa.Column("selling_price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["price_tier_id"], ["price_tiers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "branch_id",
            "product_id",
            "price_tier_id",
            name="uq_branch_price_tier_prices_branch_product_tier",
        ),
    )
    op.create_index(op.f("ix_branch_price_tier_prices_branch_id"), "branch_price_tier_prices", ["branch_id"], unique=False)
    op.create_index(op.f("ix_branch_price_tier_prices_price_tier_id"), "branch_price_tier_prices", ["price_tier_id"], unique=False)
    op.create_index(op.f("ix_branch_price_tier_prices_product_id"), "branch_price_tier_prices", ["product_id"], unique=False)
    op.create_index(op.f("ix_branch_price_tier_prices_tenant_id"), "branch_price_tier_prices", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_branch_price_tier_prices_tenant_id"), table_name="branch_price_tier_prices")
    op.drop_index(op.f("ix_branch_price_tier_prices_product_id"), table_name="branch_price_tier_prices")
    op.drop_index(op.f("ix_branch_price_tier_prices_price_tier_id"), table_name="branch_price_tier_prices")
    op.drop_index(op.f("ix_branch_price_tier_prices_branch_id"), table_name="branch_price_tier_prices")
    op.drop_table("branch_price_tier_prices")
    op.drop_index(op.f("ix_price_tiers_tenant_id"), table_name="price_tiers")
    op.drop_table("price_tiers")
