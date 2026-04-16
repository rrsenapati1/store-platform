"""extend checkout payment sessions for orchestration handoff flows

Revision ID: 20260415_0024
Revises: 20260415_0023
Create Date: 2026-04-15 17:55:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260415_0024"
down_revision = "20260415_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "checkout_payment_sessions",
        sa.Column(
            "handoff_surface",
            sa.String(length=32),
            nullable=False,
            server_default="BRANDED_UPI_QR",
        ),
    )
    op.add_column(
        "checkout_payment_sessions",
        sa.Column(
            "provider_payment_mode",
            sa.String(length=64),
            nullable=False,
            server_default="cashfree_upi",
        ),
    )
    op.add_column(
        "checkout_payment_sessions",
        sa.Column(
            "action_payload",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "checkout_payment_sessions",
        sa.Column("action_expires_at", sa.DateTime(timezone=False), nullable=True),
    )
    op.add_column(
        "checkout_payment_sessions",
        sa.Column("last_reconciled_at", sa.DateTime(timezone=False), nullable=True),
    )
    op.create_index(
        "ix_checkout_payment_sessions_action_expires_at",
        "checkout_payment_sessions",
        ["action_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_checkout_payment_sessions_action_expires_at", table_name="checkout_payment_sessions")
    op.drop_column("checkout_payment_sessions", "last_reconciled_at")
    op.drop_column("checkout_payment_sessions", "action_expires_at")
    op.drop_column("checkout_payment_sessions", "action_payload")
    op.drop_column("checkout_payment_sessions", "provider_payment_mode")
    op.drop_column("checkout_payment_sessions", "handoff_surface")
