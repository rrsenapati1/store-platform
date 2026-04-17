"""add customer assigned vouchers

Revision ID: 20260417_0036
Revises: 20260417_0035
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0036"
down_revision = "20260417_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sales",
        sa.Column(
            "customer_voucher_id",
            sa.String(length=32),
            sa.ForeignKey("customer_voucher_assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("sales", sa.Column("customer_voucher_name", sa.String(length=255), nullable=True))
    op.add_column("sales", sa.Column("customer_voucher_discount_total", sa.Float(), nullable=False, server_default="0"))
    op.create_index("ix_sales_customer_voucher_id", "sales", ["customer_voucher_id"])

    op.add_column("sale_lines", sa.Column("customer_voucher_discount_amount", sa.Float(), nullable=False, server_default="0"))

    op.create_table(
        "customer_voucher_assignments",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "campaign_id",
            sa.String(length=32),
            sa.ForeignKey("promotion_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_profile_id",
            sa.String(length=32),
            sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("voucher_code", sa.String(length=64), nullable=False),
        sa.Column("voucher_name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("voucher_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("issued_note", sa.String(length=1024), nullable=True),
        sa.Column("canceled_note", sa.String(length=1024), nullable=True),
        sa.Column(
            "redeemed_sale_id",
            sa.String(length=32),
            sa.ForeignKey("sales.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("redeemed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint("tenant_id", "voucher_code", name="uq_customer_vouchers_tenant_code"),
    )
    op.create_index("ix_customer_voucher_assignments_tenant_id", "customer_voucher_assignments", ["tenant_id"])
    op.create_index("ix_customer_voucher_assignments_campaign_id", "customer_voucher_assignments", ["campaign_id"])
    op.create_index(
        "ix_customer_voucher_assignments_customer_profile_id",
        "customer_voucher_assignments",
        ["customer_profile_id"],
    )
    op.create_index("ix_customer_voucher_assignments_voucher_code", "customer_voucher_assignments", ["voucher_code"])
    op.create_index("ix_customer_voucher_assignments_status", "customer_voucher_assignments", ["status"])
    op.create_index("ix_customer_voucher_assignments_redeemed_sale_id", "customer_voucher_assignments", ["redeemed_sale_id"])


def downgrade() -> None:
    op.drop_column("sale_lines", "customer_voucher_discount_amount")
    op.drop_index("ix_sales_customer_voucher_id", table_name="sales")
    op.drop_column("sales", "customer_voucher_discount_total")
    op.drop_column("sales", "customer_voucher_name")
    op.drop_column("sales", "customer_voucher_id")

    op.drop_index("ix_customer_voucher_assignments_redeemed_sale_id", table_name="customer_voucher_assignments")
    op.drop_index("ix_customer_voucher_assignments_status", table_name="customer_voucher_assignments")
    op.drop_index("ix_customer_voucher_assignments_voucher_code", table_name="customer_voucher_assignments")
    op.drop_index("ix_customer_voucher_assignments_customer_profile_id", table_name="customer_voucher_assignments")
    op.drop_index("ix_customer_voucher_assignments_campaign_id", table_name="customer_voucher_assignments")
    op.drop_index("ix_customer_voucher_assignments_tenant_id", table_name="customer_voucher_assignments")
    op.drop_table("customer_voucher_assignments")
