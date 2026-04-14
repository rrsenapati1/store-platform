"""store desktop local auth metadata

Revision ID: 20260414_0016
Revises: 20260414_0015
Create Date: 2026-04-14 13:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0016"
down_revision = "20260414_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("store_desktop_activations", sa.Column("local_auth_token_hash", sa.String(length=128), nullable=True))
    op.add_column("store_desktop_activations", sa.Column("activation_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("store_desktop_activations", sa.Column("offline_valid_until", sa.DateTime(), nullable=True))
    op.add_column("store_desktop_activations", sa.Column("last_unlocked_at", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_store_desktop_activations_local_auth_token_hash",
        "store_desktop_activations",
        ["local_auth_token_hash"],
        unique=False,
    )
    op.alter_column("store_desktop_activations", "activation_version", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_store_desktop_activations_local_auth_token_hash", table_name="store_desktop_activations")
    op.drop_column("store_desktop_activations", "last_unlocked_at")
    op.drop_column("store_desktop_activations", "offline_valid_until")
    op.drop_column("store_desktop_activations", "activation_version")
    op.drop_column("store_desktop_activations", "local_auth_token_hash")
