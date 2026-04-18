"""add serialized inventory foundation

Revision ID: 20260418_0043
Revises: 20260417_0042
Create Date: 2026-04-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260418_0043"
down_revision = "20260417_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "catalog_products",
        sa.Column("tracking_mode", sa.String(length=32), nullable=False, server_default="STANDARD"),
    )
    op.add_column(
        "catalog_products",
        sa.Column("compliance_profile", sa.String(length=32), nullable=False, server_default="NONE"),
    )
    op.add_column(
        "catalog_products",
        sa.Column("compliance_config", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index(op.f("ix_catalog_products_tracking_mode"), "catalog_products", ["tracking_mode"], unique=False)

    op.add_column(
        "goods_receipt_lines",
        sa.Column("serial_numbers", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.add_column(
        "sale_lines",
        sa.Column("serial_numbers", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "sale_lines",
        sa.Column("compliance_profile", sa.String(length=32), nullable=False, server_default="NONE"),
    )
    op.add_column(
        "sale_lines",
        sa.Column("compliance_capture", sa.JSON(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "serialized_inventory_units",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=32), nullable=False),
        sa.Column("goods_receipt_line_id", sa.String(length=32), nullable=False),
        sa.Column("sale_id", sa.String(length=32), nullable=True),
        sa.Column("sale_line_id", sa.String(length=32), nullable=True),
        sa.Column("serial_number", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="AVAILABLE"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goods_receipt_line_id"], ["goods_receipt_lines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sale_line_id"], ["sale_lines.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "branch_id",
            "product_id",
            "serial_number",
            name="uq_serialized_inventory_units_branch_product_serial",
        ),
    )
    op.create_index(op.f("ix_serialized_inventory_units_tenant_id"), "serialized_inventory_units", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_serialized_inventory_units_branch_id"), "serialized_inventory_units", ["branch_id"], unique=False)
    op.create_index(op.f("ix_serialized_inventory_units_product_id"), "serialized_inventory_units", ["product_id"], unique=False)
    op.create_index(
        op.f("ix_serialized_inventory_units_goods_receipt_id"),
        "serialized_inventory_units",
        ["goods_receipt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_serialized_inventory_units_goods_receipt_line_id"),
        "serialized_inventory_units",
        ["goods_receipt_line_id"],
        unique=False,
    )
    op.create_index(op.f("ix_serialized_inventory_units_sale_id"), "serialized_inventory_units", ["sale_id"], unique=False)
    op.create_index(op.f("ix_serialized_inventory_units_sale_line_id"), "serialized_inventory_units", ["sale_line_id"], unique=False)
    op.create_index(
        op.f("ix_serialized_inventory_units_serial_number"),
        "serialized_inventory_units",
        ["serial_number"],
        unique=False,
    )
    op.create_index(op.f("ix_serialized_inventory_units_status"), "serialized_inventory_units", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_serialized_inventory_units_status"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_serial_number"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_sale_line_id"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_sale_id"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_goods_receipt_line_id"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_goods_receipt_id"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_product_id"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_branch_id"), table_name="serialized_inventory_units")
    op.drop_index(op.f("ix_serialized_inventory_units_tenant_id"), table_name="serialized_inventory_units")
    op.drop_table("serialized_inventory_units")

    op.drop_column("sale_lines", "compliance_capture")
    op.drop_column("sale_lines", "compliance_profile")
    op.drop_column("sale_lines", "serial_numbers")
    op.drop_column("goods_receipt_lines", "serial_numbers")

    op.drop_index(op.f("ix_catalog_products_tracking_mode"), table_name="catalog_products")
    op.drop_column("catalog_products", "compliance_config")
    op.drop_column("catalog_products", "compliance_profile")
    op.drop_column("catalog_products", "tracking_mode")
