"""sale returns foundation

Revision ID: 20260413_0008
Revises: 20260413_0007
Create Date: 2026-04-13 11:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_0008"
down_revision: str | None = "20260413_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sale_returns",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_id", sa.String(length=32), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("refund_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("refund_method", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sale_returns_tenant_id", "sale_returns", ["tenant_id"])
    op.create_index("ix_sale_returns_branch_id", "sale_returns", ["branch_id"])
    op.create_index("ix_sale_returns_sale_id", "sale_returns", ["sale_id"])

    op.create_table(
        "sale_return_lines",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("sale_return_id", sa.String(length=32), sa.ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gst_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sale_return_lines_sale_return_id", "sale_return_lines", ["sale_return_id"])
    op.create_index("ix_sale_return_lines_product_id", "sale_return_lines", ["product_id"])

    op.create_table(
        "credit_notes",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("sale_return_id", sa.String(length=32), sa.ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credit_note_number", sa.String(length=64), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cgst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sgst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("igst_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("sale_return_id"),
        sa.UniqueConstraint("branch_id", "credit_note_number", name="uq_credit_notes_branch_number"),
    )
    op.create_index("ix_credit_notes_sale_return_id", "credit_notes", ["sale_return_id"])
    op.create_index("ix_credit_notes_tenant_id", "credit_notes", ["tenant_id"])
    op.create_index("ix_credit_notes_branch_id", "credit_notes", ["branch_id"])
    op.create_index("ix_credit_notes_credit_note_number", "credit_notes", ["credit_note_number"])

    op.create_table(
        "credit_note_tax_lines",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("credit_note_id", sa.String(length=32), sa.ForeignKey("credit_notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tax_type", sa.String(length=16), nullable=False),
        sa.Column("tax_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("taxable_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_credit_note_tax_lines_credit_note_id", "credit_note_tax_lines", ["credit_note_id"])


def downgrade() -> None:
    op.drop_index("ix_credit_note_tax_lines_credit_note_id", table_name="credit_note_tax_lines")
    op.drop_table("credit_note_tax_lines")
    op.drop_index("ix_credit_notes_credit_note_number", table_name="credit_notes")
    op.drop_index("ix_credit_notes_branch_id", table_name="credit_notes")
    op.drop_index("ix_credit_notes_tenant_id", table_name="credit_notes")
    op.drop_index("ix_credit_notes_sale_return_id", table_name="credit_notes")
    op.drop_table("credit_notes")
    op.drop_index("ix_sale_return_lines_product_id", table_name="sale_return_lines")
    op.drop_index("ix_sale_return_lines_sale_return_id", table_name="sale_return_lines")
    op.drop_table("sale_return_lines")
    op.drop_index("ix_sale_returns_sale_id", table_name="sale_returns")
    op.drop_index("ix_sale_returns_branch_id", table_name="sale_returns")
    op.drop_index("ix_sale_returns_tenant_id", table_name="sale_returns")
    op.drop_table("sale_returns")
