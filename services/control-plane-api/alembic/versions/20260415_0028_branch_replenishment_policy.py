"""add branch replenishment policy

Revision ID: 20260415_0028
Revises: 20260415_0027
Create Date: 2026-04-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260415_0028"
down_revision = "20260415_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("branch_catalog_items", sa.Column("reorder_point", sa.Float(), nullable=True))
    op.add_column("branch_catalog_items", sa.Column("target_stock", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("branch_catalog_items", "target_stock")
    op.drop_column("branch_catalog_items", "reorder_point")
