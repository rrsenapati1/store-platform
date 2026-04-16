"""add billing promotion snapshot fields

Revision ID: 20260417_0034
Revises: 20260417_0033
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0034"
down_revision = "20260417_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sales",
        sa.Column(
            "promotion_campaign_id",
            sa.String(length=32),
            sa.ForeignKey("promotion_campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "sales",
        sa.Column(
            "promotion_code_id",
            sa.String(length=32),
            sa.ForeignKey("promotion_codes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("sales", sa.Column("promotion_code", sa.String(length=64), nullable=True))
    op.add_column("sales", sa.Column("promotion_discount_amount", sa.Float(), nullable=False, server_default="0"))
    op.create_index("ix_sales_promotion_campaign_id", "sales", ["promotion_campaign_id"])
    op.create_index("ix_sales_promotion_code_id", "sales", ["promotion_code_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_promotion_code_id", table_name="sales")
    op.drop_index("ix_sales_promotion_campaign_id", table_name="sales")
    op.drop_column("sales", "promotion_discount_amount")
    op.drop_column("sales", "promotion_code")
    op.drop_column("sales", "promotion_code_id")
    op.drop_column("sales", "promotion_campaign_id")
