"""procurement foundation

Revision ID: 20260413_0004
Revises: 20260413_0003
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0004"
down_revision = "20260413_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("gstin", sa.String(length=32), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"], unique=False)

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("supplier_id", sa.String(length=32), nullable=False),
        sa.Column("purchase_order_number", sa.String(length=64), nullable=False),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("tax_total", sa.Float(), nullable=False),
        sa.Column("grand_total", sa.Float(), nullable=False),
        sa.Column("approval_requested_note", sa.String(length=1024), nullable=True),
        sa.Column("approval_decision_note", sa.String(length=1024), nullable=True),
        sa.Column("approval_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_orders_tenant_id", "purchase_orders", ["tenant_id"], unique=False)
    op.create_index("ix_purchase_orders_branch_id", "purchase_orders", ["branch_id"], unique=False)
    op.create_index("ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"], unique=False)
    op.create_index("ix_purchase_orders_purchase_order_number", "purchase_orders", ["purchase_order_number"], unique=False)

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=False),
        sa.Column("gst_rate", sa.Float(), nullable=False),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.Column("tax_total", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_order_lines_purchase_order_id", "purchase_order_lines", ["purchase_order_id"], unique=False)
    op.create_index("ix_purchase_order_lines_product_id", "purchase_order_lines", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_purchase_order_lines_product_id", table_name="purchase_order_lines")
    op.drop_index("ix_purchase_order_lines_purchase_order_id", table_name="purchase_order_lines")
    op.drop_table("purchase_order_lines")
    op.drop_index("ix_purchase_orders_purchase_order_number", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_branch_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_tenant_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_index("ix_suppliers_tenant_id", table_name="suppliers")
    op.drop_table("suppliers")
