"""add gift card foundation

Revision ID: 20260417_0040
Revises: 20260417_0039
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0040"
down_revision = "20260417_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gift_cards",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("gift_card_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("available_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("issued_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("redeemed_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("adjusted_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "gift_card_code", name="uq_gift_cards_tenant_code"),
    )
    op.create_index(op.f("ix_gift_cards_tenant_id"), "gift_cards", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_gift_cards_gift_card_code"), "gift_cards", ["gift_card_code"], unique=False)
    op.create_index(op.f("ix_gift_cards_status"), "gift_cards", ["status"], unique=False)

    op.create_table(
        "gift_card_ledger_entries",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("gift_card_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=True),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference_id", sa.String(length=64), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("balance_after", sa.Float(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gift_card_id"], ["gift_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gift_card_ledger_entries_branch_id"), "gift_card_ledger_entries", ["branch_id"], unique=False)
    op.create_index(op.f("ix_gift_card_ledger_entries_gift_card_id"), "gift_card_ledger_entries", ["gift_card_id"], unique=False)
    op.create_index(op.f("ix_gift_card_ledger_entries_tenant_id"), "gift_card_ledger_entries", ["tenant_id"], unique=False)

    op.add_column("sales", sa.Column("gift_card_id", sa.String(length=32), nullable=True))
    op.add_column("sales", sa.Column("gift_card_code", sa.String(length=64), nullable=True))
    op.add_column("sales", sa.Column("gift_card_amount", sa.Float(), nullable=False, server_default="0"))
    op.create_foreign_key(
        "fk_sales_gift_card_id",
        "sales",
        "gift_cards",
        ["gift_card_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_sales_gift_card_id"), "sales", ["gift_card_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sales_gift_card_id"), table_name="sales")
    op.drop_constraint("fk_sales_gift_card_id", "sales", type_="foreignkey")
    op.drop_column("sales", "gift_card_amount")
    op.drop_column("sales", "gift_card_code")
    op.drop_column("sales", "gift_card_id")

    op.drop_index(op.f("ix_gift_card_ledger_entries_tenant_id"), table_name="gift_card_ledger_entries")
    op.drop_index(op.f("ix_gift_card_ledger_entries_gift_card_id"), table_name="gift_card_ledger_entries")
    op.drop_index(op.f("ix_gift_card_ledger_entries_branch_id"), table_name="gift_card_ledger_entries")
    op.drop_table("gift_card_ledger_entries")

    op.drop_index(op.f("ix_gift_cards_status"), table_name="gift_cards")
    op.drop_index(op.f("ix_gift_cards_gift_card_code"), table_name="gift_cards")
    op.drop_index(op.f("ix_gift_cards_tenant_id"), table_name="gift_cards")
    op.drop_table("gift_cards")
