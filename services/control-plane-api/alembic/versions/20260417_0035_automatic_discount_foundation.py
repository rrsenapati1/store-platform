"""add automatic discount pricing foundation

Revision ID: 20260417_0035
Revises: 20260417_0034
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0035"
down_revision = "20260417_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("catalog_products", sa.Column("mrp", sa.Float(), nullable=False, server_default="0"))
    op.add_column("catalog_products", sa.Column("category_code", sa.String(length=64), nullable=True))

    op.add_column(
        "promotion_campaigns",
        sa.Column("trigger_mode", sa.String(length=32), nullable=False, server_default="CODE"),
    )
    op.add_column(
        "promotion_campaigns",
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="CART"),
    )
    op.add_column("promotion_campaigns", sa.Column("target_product_ids", sa.JSON(), nullable=True))
    op.add_column("promotion_campaigns", sa.Column("target_category_codes", sa.JSON(), nullable=True))
    op.create_index("ix_promotion_campaigns_trigger_mode", "promotion_campaigns", ["trigger_mode"])

    op.add_column("sales", sa.Column("automatic_campaign_name", sa.String(length=255), nullable=True))
    op.add_column("sales", sa.Column("automatic_discount_total", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("promotion_code_discount_total", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("mrp_total", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("selling_price_subtotal", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("total_discount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("invoice_total", sa.Float(), nullable=False, server_default="0"))

    op.add_column("sale_lines", sa.Column("mrp", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sale_lines", sa.Column("unit_selling_price", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sale_lines", sa.Column("automatic_discount_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sale_lines", sa.Column("promotion_code_discount_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sale_lines", sa.Column("promotion_discount_source", sa.String(length=64), nullable=True))
    op.add_column("sale_lines", sa.Column("taxable_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sale_lines", sa.Column("tax_amount", sa.Float(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("sale_lines", "tax_amount")
    op.drop_column("sale_lines", "taxable_amount")
    op.drop_column("sale_lines", "promotion_discount_source")
    op.drop_column("sale_lines", "promotion_code_discount_amount")
    op.drop_column("sale_lines", "automatic_discount_amount")
    op.drop_column("sale_lines", "unit_selling_price")
    op.drop_column("sale_lines", "mrp")

    op.drop_column("sales", "invoice_total")
    op.drop_column("sales", "total_discount")
    op.drop_column("sales", "selling_price_subtotal")
    op.drop_column("sales", "mrp_total")
    op.drop_column("sales", "promotion_code_discount_total")
    op.drop_column("sales", "automatic_discount_total")
    op.drop_column("sales", "automatic_campaign_name")

    op.drop_index("ix_promotion_campaigns_trigger_mode", table_name="promotion_campaigns")
    op.drop_column("promotion_campaigns", "target_category_codes")
    op.drop_column("promotion_campaigns", "target_product_ids")
    op.drop_column("promotion_campaigns", "scope")
    op.drop_column("promotion_campaigns", "trigger_mode")

    op.drop_column("catalog_products", "category_code")
    op.drop_column("catalog_products", "mrp")
