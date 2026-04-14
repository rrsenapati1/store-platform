"""inventory foundation

Revision ID: 20260413_0005
Revises: 20260413_0004
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0005"
down_revision = "20260413_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=32), nullable=False),
        sa.Column("supplier_id", sa.String(length=32), nullable=False),
        sa.Column("goods_receipt_number", sa.String(length=64), nullable=False),
        sa.Column("received_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "goods_receipt_number", name="uq_goods_receipts_branch_number"),
        sa.UniqueConstraint("purchase_order_id", name="uq_goods_receipts_purchase_order"),
    )
    op.create_index("ix_goods_receipts_tenant_id", "goods_receipts", ["tenant_id"], unique=False)
    op.create_index("ix_goods_receipts_branch_id", "goods_receipts", ["branch_id"], unique=False)
    op.create_index("ix_goods_receipts_purchase_order_id", "goods_receipts", ["purchase_order_id"], unique=False)
    op.create_index("ix_goods_receipts_supplier_id", "goods_receipts", ["supplier_id"], unique=False)
    op.create_index("ix_goods_receipts_goods_receipt_number", "goods_receipts", ["goods_receipt_number"], unique=False)

    op.create_table(
        "goods_receipt_lines",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=False),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goods_receipt_lines_goods_receipt_id", "goods_receipt_lines", ["goods_receipt_id"], unique=False)
    op.create_index("ix_goods_receipt_lines_product_id", "goods_receipt_lines", ["product_id"], unique=False)

    op.create_table(
        "inventory_ledger_entries",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reference_type", sa.String(length=64), nullable=False),
        sa.Column("reference_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_ledger_entries_tenant_id", "inventory_ledger_entries", ["tenant_id"], unique=False)
    op.create_index("ix_inventory_ledger_entries_branch_id", "inventory_ledger_entries", ["branch_id"], unique=False)
    op.create_index("ix_inventory_ledger_entries_product_id", "inventory_ledger_entries", ["product_id"], unique=False)
    op.create_index("ix_inventory_ledger_entries_entry_type", "inventory_ledger_entries", ["entry_type"], unique=False)
    op.create_index("ix_inventory_ledger_entries_reference_id", "inventory_ledger_entries", ["reference_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inventory_ledger_entries_reference_id", table_name="inventory_ledger_entries")
    op.drop_index("ix_inventory_ledger_entries_entry_type", table_name="inventory_ledger_entries")
    op.drop_index("ix_inventory_ledger_entries_product_id", table_name="inventory_ledger_entries")
    op.drop_index("ix_inventory_ledger_entries_branch_id", table_name="inventory_ledger_entries")
    op.drop_index("ix_inventory_ledger_entries_tenant_id", table_name="inventory_ledger_entries")
    op.drop_table("inventory_ledger_entries")
    op.drop_index("ix_goods_receipt_lines_product_id", table_name="goods_receipt_lines")
    op.drop_index("ix_goods_receipt_lines_goods_receipt_id", table_name="goods_receipt_lines")
    op.drop_table("goods_receipt_lines")
    op.drop_index("ix_goods_receipts_goods_receipt_number", table_name="goods_receipts")
    op.drop_index("ix_goods_receipts_supplier_id", table_name="goods_receipts")
    op.drop_index("ix_goods_receipts_purchase_order_id", table_name="goods_receipts")
    op.drop_index("ix_goods_receipts_branch_id", table_name="goods_receipts")
    op.drop_index("ix_goods_receipts_tenant_id", table_name="goods_receipts")
    op.drop_table("goods_receipts")
