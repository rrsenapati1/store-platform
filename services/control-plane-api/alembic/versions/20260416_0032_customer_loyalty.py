"""add customer loyalty

Revision ID: 20260416_0032
Revises: 20260416_0031
Create Date: 2026-04-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260416_0032"
down_revision = "20260416_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_loyalty_programs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DISABLED"),
        sa.Column("earn_points_per_currency_unit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("redeem_step_points", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("redeem_value_per_step", sa.Float(), nullable=False, server_default="0"),
        sa.Column("minimum_redeem_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_loyalty_programs_tenant"),
    )
    op.create_index("ix_tenant_loyalty_programs_tenant_id", "tenant_loyalty_programs", ["tenant_id"])

    op.create_table(
        "customer_loyalty_accounts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "customer_profile_id",
            sa.String(length=32),
            sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("available_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("earned_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("redeemed_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("adjusted_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "customer_profile_id",
            name="uq_customer_loyalty_accounts_tenant_customer_profile",
        ),
    )
    op.create_index("ix_customer_loyalty_accounts_tenant_id", "customer_loyalty_accounts", ["tenant_id"])
    op.create_index(
        "ix_customer_loyalty_accounts_customer_profile_id",
        "customer_loyalty_accounts",
        ["customer_profile_id"],
    )

    op.create_table(
        "customer_loyalty_ledger_entries",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "customer_profile_id",
            sa.String(length=32),
            sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.String(length=32),
            sa.ForeignKey("customer_loyalty_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference_id", sa.String(length=64), nullable=True),
        sa.Column("points_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balance_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index("ix_customer_loyalty_ledger_entries_tenant_id", "customer_loyalty_ledger_entries", ["tenant_id"])
    op.create_index(
        "ix_customer_loyalty_ledger_entries_customer_profile_id",
        "customer_loyalty_ledger_entries",
        ["customer_profile_id"],
    )
    op.create_index(
        "ix_customer_loyalty_ledger_entries_created_at",
        "customer_loyalty_ledger_entries",
        ["created_at"],
    )

    op.add_column("sales", sa.Column("loyalty_points_redeemed", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("loyalty_discount_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("sales", sa.Column("loyalty_points_earned", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("sales", "loyalty_points_earned")
    op.drop_column("sales", "loyalty_discount_amount")
    op.drop_column("sales", "loyalty_points_redeemed")

    op.drop_index("ix_customer_loyalty_ledger_entries_created_at", table_name="customer_loyalty_ledger_entries")
    op.drop_index(
        "ix_customer_loyalty_ledger_entries_customer_profile_id",
        table_name="customer_loyalty_ledger_entries",
    )
    op.drop_index("ix_customer_loyalty_ledger_entries_tenant_id", table_name="customer_loyalty_ledger_entries")
    op.drop_table("customer_loyalty_ledger_entries")

    op.drop_index("ix_customer_loyalty_accounts_customer_profile_id", table_name="customer_loyalty_accounts")
    op.drop_index("ix_customer_loyalty_accounts_tenant_id", table_name="customer_loyalty_accounts")
    op.drop_table("customer_loyalty_accounts")

    op.drop_index("ix_tenant_loyalty_programs_tenant_id", table_name="tenant_loyalty_programs")
    op.drop_table("tenant_loyalty_programs")
