"""extend goods receipts for reviewed receiving

Revision ID: 20260415_0025
Revises: 20260415_0024
Create Date: 2026-04-15 23:05:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260415_0025"
down_revision = "20260415_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "goods_receipts",
        sa.Column("note", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "goods_receipt_lines",
        sa.Column(
            "ordered_quantity",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "goods_receipt_lines",
        sa.Column("discrepancy_note", sa.String(length=1024), nullable=True),
    )
    op.execute("UPDATE goods_receipt_lines SET ordered_quantity = quantity")


def downgrade() -> None:
    op.drop_column("goods_receipt_lines", "discrepancy_note")
    op.drop_column("goods_receipt_lines", "ordered_quantity")
    op.drop_column("goods_receipts", "note")
