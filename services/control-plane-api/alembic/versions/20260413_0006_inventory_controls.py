"""inventory controls

Revision ID: 20260413_0006
Revises: 20260413_0005
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0006"
down_revision = "20260413_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_adjustments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("quantity_delta", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_adjustments_tenant_id", "stock_adjustments", ["tenant_id"], unique=False)
    op.create_index("ix_stock_adjustments_branch_id", "stock_adjustments", ["branch_id"], unique=False)
    op.create_index("ix_stock_adjustments_product_id", "stock_adjustments", ["product_id"], unique=False)

    op.create_table(
        "stock_count_sessions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("counted_quantity", sa.Float(), nullable=False),
        sa.Column("expected_quantity", sa.Float(), nullable=False),
        sa.Column("variance_quantity", sa.Float(), nullable=False),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_count_sessions_tenant_id", "stock_count_sessions", ["tenant_id"], unique=False)
    op.create_index("ix_stock_count_sessions_branch_id", "stock_count_sessions", ["branch_id"], unique=False)
    op.create_index("ix_stock_count_sessions_product_id", "stock_count_sessions", ["product_id"], unique=False)

    op.create_table(
        "transfer_orders",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("source_branch_id", sa.String(length=32), nullable=False),
        sa.Column("destination_branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("transfer_number", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["destination_branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_branch_id", "transfer_number", name="uq_transfer_orders_source_number"),
    )
    op.create_index("ix_transfer_orders_tenant_id", "transfer_orders", ["tenant_id"], unique=False)
    op.create_index("ix_transfer_orders_source_branch_id", "transfer_orders", ["source_branch_id"], unique=False)
    op.create_index("ix_transfer_orders_destination_branch_id", "transfer_orders", ["destination_branch_id"], unique=False)
    op.create_index("ix_transfer_orders_product_id", "transfer_orders", ["product_id"], unique=False)
    op.create_index("ix_transfer_orders_transfer_number", "transfer_orders", ["transfer_number"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transfer_orders_transfer_number", table_name="transfer_orders")
    op.drop_index("ix_transfer_orders_product_id", table_name="transfer_orders")
    op.drop_index("ix_transfer_orders_destination_branch_id", table_name="transfer_orders")
    op.drop_index("ix_transfer_orders_source_branch_id", table_name="transfer_orders")
    op.drop_index("ix_transfer_orders_tenant_id", table_name="transfer_orders")
    op.drop_table("transfer_orders")
    op.drop_index("ix_stock_count_sessions_product_id", table_name="stock_count_sessions")
    op.drop_index("ix_stock_count_sessions_branch_id", table_name="stock_count_sessions")
    op.drop_index("ix_stock_count_sessions_tenant_id", table_name="stock_count_sessions")
    op.drop_table("stock_count_sessions")
    op.drop_index("ix_stock_adjustments_product_id", table_name="stock_adjustments")
    op.drop_index("ix_stock_adjustments_branch_id", table_name="stock_adjustments")
    op.drop_index("ix_stock_adjustments_tenant_id", table_name="stock_adjustments")
    op.drop_table("stock_adjustments")
