"""add customer store credit

Revision ID: 20260416_0031
Revises: 20260416_0030
Create Date: 2026-04-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260416_0031"
down_revision = "20260416_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_credit_accounts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "customer_profile_id",
            sa.String(length=32),
            sa.ForeignKey("customer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("available_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("issued_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("redeemed_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("adjusted_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "customer_profile_id",
            name="uq_customer_credit_accounts_tenant_customer_profile",
        ),
    )
    op.create_index("ix_customer_credit_accounts_tenant_id", "customer_credit_accounts", ["tenant_id"])
    op.create_index(
        "ix_customer_credit_accounts_customer_profile_id",
        "customer_credit_accounts",
        ["customer_profile_id"],
    )

    op.create_table(
        "customer_credit_lots",
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
            sa.ForeignKey("customer_credit_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference_id", sa.String(length=64), nullable=True),
        sa.Column("original_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("remaining_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("issued_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index("ix_customer_credit_lots_tenant_id", "customer_credit_lots", ["tenant_id"])
    op.create_index(
        "ix_customer_credit_lots_customer_profile_id",
        "customer_credit_lots",
        ["customer_profile_id"],
    )
    op.create_index("ix_customer_credit_lots_created_at", "customer_credit_lots", ["created_at"])

    op.create_table(
        "customer_credit_ledger_entries",
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
            sa.ForeignKey("customer_credit_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lot_id",
            sa.String(length=32),
            sa.ForeignKey("customer_credit_lots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference_id", sa.String(length=64), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("running_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index(
        "ix_customer_credit_ledger_entries_tenant_id",
        "customer_credit_ledger_entries",
        ["tenant_id"],
    )
    op.create_index(
        "ix_customer_credit_ledger_entries_customer_profile_id",
        "customer_credit_ledger_entries",
        ["customer_profile_id"],
    )
    op.create_index(
        "ix_customer_credit_ledger_entries_created_at",
        "customer_credit_ledger_entries",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_credit_ledger_entries_created_at", table_name="customer_credit_ledger_entries")
    op.drop_index("ix_customer_credit_ledger_entries_customer_profile_id", table_name="customer_credit_ledger_entries")
    op.drop_index("ix_customer_credit_ledger_entries_tenant_id", table_name="customer_credit_ledger_entries")
    op.drop_table("customer_credit_ledger_entries")

    op.drop_index("ix_customer_credit_lots_created_at", table_name="customer_credit_lots")
    op.drop_index("ix_customer_credit_lots_customer_profile_id", table_name="customer_credit_lots")
    op.drop_index("ix_customer_credit_lots_tenant_id", table_name="customer_credit_lots")
    op.drop_table("customer_credit_lots")

    op.drop_index("ix_customer_credit_accounts_customer_profile_id", table_name="customer_credit_accounts")
    op.drop_index("ix_customer_credit_accounts_tenant_id", table_name="customer_credit_accounts")
    op.drop_table("customer_credit_accounts")
