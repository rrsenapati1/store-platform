"""procurement finance foundation

Revision ID: 20260414_0011
Revises: 20260413_0010
Create Date: 2026-04-14 10:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0011"
down_revision = "20260413_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_invoices",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.String(length=32), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=32), sa.ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_number", sa.String(length=64), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cgst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sgst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("igst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("goods_receipt_id", name="uq_purchase_invoices_goods_receipt"),
        sa.UniqueConstraint("branch_id", "invoice_number", name="uq_purchase_invoices_branch_number"),
    )
    op.create_index("ix_purchase_invoices_tenant_id", "purchase_invoices", ["tenant_id"])
    op.create_index("ix_purchase_invoices_branch_id", "purchase_invoices", ["branch_id"])
    op.create_index("ix_purchase_invoices_supplier_id", "purchase_invoices", ["supplier_id"])
    op.create_index("ix_purchase_invoices_goods_receipt_id", "purchase_invoices", ["goods_receipt_id"])
    op.create_index("ix_purchase_invoices_invoice_number", "purchase_invoices", ["invoice_number"])

    op.create_table(
        "purchase_invoice_lines",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("purchase_invoice_id", sa.String(length=32), sa.ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gst_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_purchase_invoice_lines_purchase_invoice_id", "purchase_invoice_lines", ["purchase_invoice_id"])
    op.create_index("ix_purchase_invoice_lines_product_id", "purchase_invoice_lines", ["product_id"])

    op.create_table(
        "supplier_returns",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.String(length=32), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_invoice_id", sa.String(length=32), sa.ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_credit_note_number", sa.String(length=64), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cgst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sgst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("igst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("branch_id", "supplier_credit_note_number", name="uq_supplier_returns_branch_number"),
    )
    op.create_index("ix_supplier_returns_tenant_id", "supplier_returns", ["tenant_id"])
    op.create_index("ix_supplier_returns_branch_id", "supplier_returns", ["branch_id"])
    op.create_index("ix_supplier_returns_supplier_id", "supplier_returns", ["supplier_id"])
    op.create_index("ix_supplier_returns_purchase_invoice_id", "supplier_returns", ["purchase_invoice_id"])

    op.create_table(
        "supplier_return_lines",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("supplier_return_id", sa.String(length=32), sa.ForeignKey("supplier_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gst_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_supplier_return_lines_supplier_return_id", "supplier_return_lines", ["supplier_return_id"])
    op.create_index("ix_supplier_return_lines_product_id", "supplier_return_lines", ["product_id"])

    op.create_table(
        "supplier_payments",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.String(length=32), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_invoice_id", sa.String(length=32), sa.ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_number", sa.String(length=64), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("branch_id", "payment_number", name="uq_supplier_payments_branch_number"),
    )
    op.create_index("ix_supplier_payments_tenant_id", "supplier_payments", ["tenant_id"])
    op.create_index("ix_supplier_payments_branch_id", "supplier_payments", ["branch_id"])
    op.create_index("ix_supplier_payments_supplier_id", "supplier_payments", ["supplier_id"])
    op.create_index("ix_supplier_payments_purchase_invoice_id", "supplier_payments", ["purchase_invoice_id"])
    op.create_index("ix_supplier_payments_payment_number", "supplier_payments", ["payment_number"])


def downgrade() -> None:
    op.drop_index("ix_supplier_payments_payment_number", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_purchase_invoice_id", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_supplier_id", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_branch_id", table_name="supplier_payments")
    op.drop_index("ix_supplier_payments_tenant_id", table_name="supplier_payments")
    op.drop_table("supplier_payments")

    op.drop_index("ix_supplier_return_lines_product_id", table_name="supplier_return_lines")
    op.drop_index("ix_supplier_return_lines_supplier_return_id", table_name="supplier_return_lines")
    op.drop_table("supplier_return_lines")

    op.drop_index("ix_supplier_returns_purchase_invoice_id", table_name="supplier_returns")
    op.drop_index("ix_supplier_returns_supplier_id", table_name="supplier_returns")
    op.drop_index("ix_supplier_returns_branch_id", table_name="supplier_returns")
    op.drop_index("ix_supplier_returns_tenant_id", table_name="supplier_returns")
    op.drop_table("supplier_returns")

    op.drop_index("ix_purchase_invoice_lines_product_id", table_name="purchase_invoice_lines")
    op.drop_index("ix_purchase_invoice_lines_purchase_invoice_id", table_name="purchase_invoice_lines")
    op.drop_table("purchase_invoice_lines")

    op.drop_index("ix_purchase_invoices_invoice_number", table_name="purchase_invoices")
    op.drop_index("ix_purchase_invoices_goods_receipt_id", table_name="purchase_invoices")
    op.drop_index("ix_purchase_invoices_supplier_id", table_name="purchase_invoices")
    op.drop_index("ix_purchase_invoices_branch_id", table_name="purchase_invoices")
    op.drop_index("ix_purchase_invoices_tenant_id", table_name="purchase_invoices")
    op.drop_table("purchase_invoices")
