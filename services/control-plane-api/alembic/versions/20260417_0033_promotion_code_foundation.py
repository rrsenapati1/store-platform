"""add promotion code foundation

Revision ID: 20260417_0033
Revises: 20260416_0032
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0033"
down_revision = "20260416_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "promotion_campaigns",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("discount_type", sa.String(length=32), nullable=False),
        sa.Column("discount_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("minimum_order_amount", sa.Float(), nullable=True),
        sa.Column("maximum_discount_amount", sa.Float(), nullable=True),
        sa.Column("redemption_limit_total", sa.Integer(), nullable=True),
        sa.Column("redemption_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index("ix_promotion_campaigns_tenant_id", "promotion_campaigns", ["tenant_id"])
    op.create_index("ix_promotion_campaigns_status", "promotion_campaigns", ["status"])

    op.create_table(
        "promotion_codes",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "campaign_id",
            sa.String(length=32),
            sa.ForeignKey("promotion_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("redemption_limit_per_code", sa.Integer(), nullable=True),
        sa.Column("redemption_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_promotion_codes_tenant_code"),
    )
    op.create_index("ix_promotion_codes_tenant_id", "promotion_codes", ["tenant_id"])
    op.create_index("ix_promotion_codes_campaign_id", "promotion_codes", ["campaign_id"])
    op.create_index("ix_promotion_codes_code", "promotion_codes", ["code"])
    op.create_index("ix_promotion_codes_status", "promotion_codes", ["status"])


def downgrade() -> None:
    op.drop_index("ix_promotion_codes_status", table_name="promotion_codes")
    op.drop_index("ix_promotion_codes_code", table_name="promotion_codes")
    op.drop_index("ix_promotion_codes_campaign_id", table_name="promotion_codes")
    op.drop_index("ix_promotion_codes_tenant_id", table_name="promotion_codes")
    op.drop_table("promotion_codes")

    op.drop_index("ix_promotion_campaigns_status", table_name="promotion_campaigns")
    op.drop_index("ix_promotion_campaigns_tenant_id", table_name="promotion_campaigns")
    op.drop_table("promotion_campaigns")
