"""catalog foundation

Revision ID: 20260413_0003
Revises: 20260413_0002
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0003"
down_revision = "20260413_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_products",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku_code", sa.String(length=128), nullable=False),
        sa.Column("barcode", sa.String(length=64), nullable=False),
        sa.Column("hsn_sac_code", sa.String(length=32), nullable=False),
        sa.Column("gst_rate", sa.Float(), nullable=False),
        sa.Column("selling_price", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "barcode", name="uq_catalog_products_tenant_barcode"),
        sa.UniqueConstraint("tenant_id", "sku_code", name="uq_catalog_products_tenant_sku"),
    )
    op.create_index("ix_catalog_products_tenant_id", "catalog_products", ["tenant_id"], unique=False)

    op.create_table(
        "branch_catalog_items",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("selling_price_override", sa.Float(), nullable=True),
        sa.Column("availability_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "product_id", name="uq_branch_catalog_items_branch_product"),
    )
    op.create_index("ix_branch_catalog_items_tenant_id", "branch_catalog_items", ["tenant_id"], unique=False)
    op.create_index("ix_branch_catalog_items_branch_id", "branch_catalog_items", ["branch_id"], unique=False)
    op.create_index("ix_branch_catalog_items_product_id", "branch_catalog_items", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_branch_catalog_items_product_id", table_name="branch_catalog_items")
    op.drop_index("ix_branch_catalog_items_branch_id", table_name="branch_catalog_items")
    op.drop_index("ix_branch_catalog_items_tenant_id", table_name="branch_catalog_items")
    op.drop_table("branch_catalog_items")
    op.drop_index("ix_catalog_products_tenant_id", table_name="catalog_products")
    op.drop_table("catalog_products")
