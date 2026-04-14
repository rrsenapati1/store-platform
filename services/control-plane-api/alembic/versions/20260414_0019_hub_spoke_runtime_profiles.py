"""hub spoke runtime profiles

Revision ID: 20260414_0019
Revises: 20260414_0018
Create Date: 2026-04-14 18:55:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0019"
down_revision = "20260414_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hub_spoke_observations",
        sa.Column("runtime_profile", sa.String(length=64), nullable=False, server_default="desktop_spoke"),
    )
    op.alter_column("hub_spoke_observations", "runtime_profile", server_default=None)


def downgrade() -> None:
    op.drop_column("hub_spoke_observations", "runtime_profile")
