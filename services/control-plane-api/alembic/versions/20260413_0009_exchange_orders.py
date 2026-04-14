"""exchange order foundation

Revision ID: 20260413_0009
Revises: 20260413_0008
Create Date: 2026-04-13 23:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0009"
down_revision = "20260413_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exchange_orders",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_sale_id", sa.String(length=32), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("replacement_sale_id", sa.String(length=32), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_return_id", sa.String(length=32), sa.ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("balance_direction", sa.String(length=32), nullable=False),
        sa.Column("balance_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("settlement_method", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_exchange_orders_tenant_id", "exchange_orders", ["tenant_id"])
    op.create_index("ix_exchange_orders_branch_id", "exchange_orders", ["branch_id"])
    op.create_index("ix_exchange_orders_original_sale_id", "exchange_orders", ["original_sale_id"])
    op.create_index("ix_exchange_orders_replacement_sale_id", "exchange_orders", ["replacement_sale_id"])
    op.create_index("ix_exchange_orders_sale_return_id", "exchange_orders", ["sale_return_id"])


def downgrade() -> None:
    op.drop_index("ix_exchange_orders_sale_return_id", table_name="exchange_orders")
    op.drop_index("ix_exchange_orders_replacement_sale_id", table_name="exchange_orders")
    op.drop_index("ix_exchange_orders_original_sale_id", table_name="exchange_orders")
    op.drop_index("ix_exchange_orders_branch_id", table_name="exchange_orders")
    op.drop_index("ix_exchange_orders_tenant_id", table_name="exchange_orders")
    op.drop_table("exchange_orders")
