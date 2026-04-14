"""batch tracking foundation

Revision ID: 20260414_0012
Revises: 20260414_0011
Create Date: 2026-04-14 15:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0012"
down_revision = "20260414_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_lots",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=32), sa.ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_number", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("goods_receipt_id", "batch_number", name="uq_batch_lots_goods_receipt_batch_number"),
    )
    op.create_index("ix_batch_lots_tenant_id", "batch_lots", ["tenant_id"])
    op.create_index("ix_batch_lots_branch_id", "batch_lots", ["branch_id"])
    op.create_index("ix_batch_lots_goods_receipt_id", "batch_lots", ["goods_receipt_id"])
    op.create_index("ix_batch_lots_product_id", "batch_lots", ["product_id"])
    op.create_index("ix_batch_lots_batch_number", "batch_lots", ["batch_number"])

    op.create_table(
        "batch_expiry_write_offs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_lot_id", sa.String(length=32), sa.ForeignKey("batch_lots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_batch_expiry_write_offs_tenant_id", "batch_expiry_write_offs", ["tenant_id"])
    op.create_index("ix_batch_expiry_write_offs_branch_id", "batch_expiry_write_offs", ["branch_id"])
    op.create_index("ix_batch_expiry_write_offs_batch_lot_id", "batch_expiry_write_offs", ["batch_lot_id"])
    op.create_index("ix_batch_expiry_write_offs_product_id", "batch_expiry_write_offs", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_batch_expiry_write_offs_product_id", table_name="batch_expiry_write_offs")
    op.drop_index("ix_batch_expiry_write_offs_batch_lot_id", table_name="batch_expiry_write_offs")
    op.drop_index("ix_batch_expiry_write_offs_branch_id", table_name="batch_expiry_write_offs")
    op.drop_index("ix_batch_expiry_write_offs_tenant_id", table_name="batch_expiry_write_offs")
    op.drop_table("batch_expiry_write_offs")

    op.drop_index("ix_batch_lots_batch_number", table_name="batch_lots")
    op.drop_index("ix_batch_lots_product_id", table_name="batch_lots")
    op.drop_index("ix_batch_lots_goods_receipt_id", table_name="batch_lots")
    op.drop_index("ix_batch_lots_branch_id", table_name="batch_lots")
    op.drop_index("ix_batch_lots_tenant_id", table_name="batch_lots")
    op.drop_table("batch_lots")
