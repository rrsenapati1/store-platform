"""add customer profiles

Revision ID: 20260416_0030
Revises: 20260416_0029
Create Date: 2026-04-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260416_0030"
down_revision = "20260416_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_profiles",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("gstin", sa.String(length=32), nullable=True),
        sa.Column("default_note", sa.String(length=1024), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint("tenant_id", "gstin", name="uq_customer_profiles_tenant_gstin"),
    )
    op.create_index("ix_customer_profiles_tenant_id", "customer_profiles", ["tenant_id"])
    op.create_index("ix_customer_profiles_gstin", "customer_profiles", ["gstin"])
    op.create_index("ix_customer_profiles_status", "customer_profiles", ["status"])

    op.add_column("sales", sa.Column("customer_profile_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_sales_customer_profile_id",
        "sales",
        "customer_profiles",
        ["customer_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_sales_customer_profile_id", "sales", ["customer_profile_id"])

    op.add_column("checkout_payment_sessions", sa.Column("customer_profile_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_checkout_payment_sessions_customer_profile_id",
        "checkout_payment_sessions",
        "customer_profiles",
        ["customer_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_checkout_payment_sessions_customer_profile_id",
        "checkout_payment_sessions",
        ["customer_profile_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_checkout_payment_sessions_customer_profile_id", table_name="checkout_payment_sessions")
    op.drop_constraint("fk_checkout_payment_sessions_customer_profile_id", "checkout_payment_sessions", type_="foreignkey")
    op.drop_column("checkout_payment_sessions", "customer_profile_id")

    op.drop_index("ix_sales_customer_profile_id", table_name="sales")
    op.drop_constraint("fk_sales_customer_profile_id", "sales", type_="foreignkey")
    op.drop_column("sales", "customer_profile_id")

    op.drop_index("ix_customer_profiles_status", table_name="customer_profiles")
    op.drop_index("ix_customer_profiles_gstin", table_name="customer_profiles")
    op.drop_index("ix_customer_profiles_tenant_id", table_name="customer_profiles")
    op.drop_table("customer_profiles")
