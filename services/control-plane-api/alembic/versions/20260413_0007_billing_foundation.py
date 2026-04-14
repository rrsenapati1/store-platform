"""billing foundation

Revision ID: 20260413_0007
Revises: 20260413_0006
Create Date: 2026-04-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0007"
down_revision = "20260413_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sales",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_gstin", sa.String(length=32), nullable=True),
        sa.Column("invoice_kind", sa.String(length=16), nullable=False),
        sa.Column("irn_status", sa.String(length=32), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("tax_total", sa.Float(), nullable=False),
        sa.Column("grand_total", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_tenant_id", "sales", ["tenant_id"], unique=False)
    op.create_index("ix_sales_branch_id", "sales", ["branch_id"], unique=False)

    op.create_table(
        "sale_lines",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("sale_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("gst_rate", sa.Float(), nullable=False),
        sa.Column("line_subtotal", sa.Float(), nullable=False),
        sa.Column("tax_total", sa.Float(), nullable=False),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sale_lines_sale_id", "sale_lines", ["sale_id"], unique=False)
    op.create_index("ix_sale_lines_product_id", "sale_lines", ["product_id"], unique=False)

    op.create_table(
        "sales_invoices",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("sale_id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("invoice_number", sa.String(length=64), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("cgst_total", sa.Float(), nullable=False),
        sa.Column("sgst_total", sa.Float(), nullable=False),
        sa.Column("igst_total", sa.Float(), nullable=False),
        sa.Column("grand_total", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "invoice_number", name="uq_sales_invoices_branch_number"),
        sa.UniqueConstraint("sale_id"),
    )
    op.create_index("ix_sales_invoices_tenant_id", "sales_invoices", ["tenant_id"], unique=False)
    op.create_index("ix_sales_invoices_branch_id", "sales_invoices", ["branch_id"], unique=False)
    op.create_index("ix_sales_invoices_sale_id", "sales_invoices", ["sale_id"], unique=False)
    op.create_index("ix_sales_invoices_invoice_number", "sales_invoices", ["invoice_number"], unique=False)

    op.create_table(
        "invoice_tax_lines",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("sales_invoice_id", sa.String(length=32), nullable=False),
        sa.Column("tax_type", sa.String(length=16), nullable=False),
        sa.Column("tax_rate", sa.Float(), nullable=False),
        sa.Column("taxable_amount", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["sales_invoice_id"], ["sales_invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_tax_lines_sales_invoice_id", "invoice_tax_lines", ["sales_invoice_id"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("sale_id", sa.String(length=32), nullable=False),
        sa.Column("payment_method", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_sale_id", "payments", ["sale_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payments_sale_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_invoice_tax_lines_sales_invoice_id", table_name="invoice_tax_lines")
    op.drop_table("invoice_tax_lines")
    op.drop_index("ix_sales_invoices_invoice_number", table_name="sales_invoices")
    op.drop_index("ix_sales_invoices_sale_id", table_name="sales_invoices")
    op.drop_index("ix_sales_invoices_branch_id", table_name="sales_invoices")
    op.drop_index("ix_sales_invoices_tenant_id", table_name="sales_invoices")
    op.drop_table("sales_invoices")
    op.drop_index("ix_sale_lines_product_id", table_name="sale_lines")
    op.drop_index("ix_sale_lines_sale_id", table_name="sale_lines")
    op.drop_table("sale_lines")
    op.drop_index("ix_sales_branch_id", table_name="sales")
    op.drop_index("ix_sales_tenant_id", table_name="sales")
    op.drop_table("sales")
