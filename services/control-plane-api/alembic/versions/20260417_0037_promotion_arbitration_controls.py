"""add promotion arbitration controls

Revision ID: 20260417_0037
Revises: 20260417_0036
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0037"
down_revision = "20260417_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "promotion_campaigns",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
    )
    op.add_column(
        "promotion_campaigns",
        sa.Column("stacking_rule", sa.String(length=32), nullable=False, server_default="STACKABLE"),
    )


def downgrade() -> None:
    op.drop_column("promotion_campaigns", "stacking_rule")
    op.drop_column("promotion_campaigns", "priority")
