"""checkout payment sessions for branch Cashfree QR flows

Revision ID: 20260415_0023
Revises: 20260414_0022
Create Date: 2026-04-15 16:05:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260415_0023"
down_revision = "20260414_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkout_payment_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider_name", sa.String(length=32), nullable=False),
        sa.Column("provider_order_id", sa.String(length=255), nullable=False),
        sa.Column("provider_payment_session_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("payment_method", sa.String(length=64), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("provider_status", sa.String(length=64), nullable=False),
        sa.Column("order_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=8), nullable=False, server_default="INR"),
        sa.Column("cart_summary_hash", sa.String(length=64), nullable=False),
        sa.Column("cart_snapshot", sa.JSON(), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_gstin", sa.String(length=32), nullable=True),
        sa.Column("qr_payload", sa.JSON(), nullable=False),
        sa.Column("qr_expires_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("provider_response_payload", sa.JSON(), nullable=False),
        sa.Column("last_error_message", sa.String(length=1024), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("finalized_sale_id", sa.String(length=32), sa.ForeignKey("sales.id", ondelete="SET NULL"), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("provider_name", "provider_order_id", name="uq_checkout_payment_sessions_provider_order"),
    )
    op.create_index("ix_checkout_payment_sessions_tenant_id", "checkout_payment_sessions", ["tenant_id"])
    op.create_index("ix_checkout_payment_sessions_branch_id", "checkout_payment_sessions", ["branch_id"])
    op.create_index("ix_checkout_payment_sessions_actor_user_id", "checkout_payment_sessions", ["actor_user_id"])
    op.create_index("ix_checkout_payment_sessions_provider_name", "checkout_payment_sessions", ["provider_name"])
    op.create_index("ix_checkout_payment_sessions_provider_order_id", "checkout_payment_sessions", ["provider_order_id"])
    op.create_index("ix_checkout_payment_sessions_provider_payment_session_id", "checkout_payment_sessions", ["provider_payment_session_id"])
    op.create_index("ix_checkout_payment_sessions_provider_payment_id", "checkout_payment_sessions", ["provider_payment_id"])
    op.create_index("ix_checkout_payment_sessions_lifecycle_status", "checkout_payment_sessions", ["lifecycle_status"])
    op.create_index("ix_checkout_payment_sessions_provider_status", "checkout_payment_sessions", ["provider_status"])
    op.create_index("ix_checkout_payment_sessions_cart_summary_hash", "checkout_payment_sessions", ["cart_summary_hash"])
    op.create_index("ix_checkout_payment_sessions_qr_expires_at", "checkout_payment_sessions", ["qr_expires_at"])
    op.create_index("ix_checkout_payment_sessions_finalized_sale_id", "checkout_payment_sessions", ["finalized_sale_id"])


def downgrade() -> None:
    op.drop_index("ix_checkout_payment_sessions_finalized_sale_id", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_qr_expires_at", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_cart_summary_hash", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_provider_status", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_lifecycle_status", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_provider_payment_id", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_provider_payment_session_id", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_provider_order_id", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_provider_name", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_actor_user_id", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_branch_id", table_name="checkout_payment_sessions")
    op.drop_index("ix_checkout_payment_sessions_tenant_id", table_name="checkout_payment_sessions")
    op.drop_table("checkout_payment_sessions")
