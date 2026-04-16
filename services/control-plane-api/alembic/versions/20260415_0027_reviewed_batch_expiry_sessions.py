"""add reviewed batch expiry sessions

Revision ID: 20260415_0027
Revises: 20260415_0026
Create Date: 2026-04-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260415_0027"
down_revision = "20260415_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_expiry_review_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_lot_id", sa.String(length=32), sa.ForeignKey("batch_lots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("remaining_quantity_snapshot", sa.Float(), nullable=False, server_default="0"),
        sa.Column("proposed_quantity", sa.Float(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("review_note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("branch_id", "session_number", name="uq_batch_expiry_review_sessions_branch_number"),
    )
    op.create_index("ix_batch_expiry_review_sessions_tenant_id", "batch_expiry_review_sessions", ["tenant_id"])
    op.create_index("ix_batch_expiry_review_sessions_branch_id", "batch_expiry_review_sessions", ["branch_id"])
    op.create_index("ix_batch_expiry_review_sessions_batch_lot_id", "batch_expiry_review_sessions", ["batch_lot_id"])
    op.create_index("ix_batch_expiry_review_sessions_product_id", "batch_expiry_review_sessions", ["product_id"])
    op.create_index("ix_batch_expiry_review_sessions_session_number", "batch_expiry_review_sessions", ["session_number"])
    op.create_index("ix_batch_expiry_review_sessions_status", "batch_expiry_review_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_batch_expiry_review_sessions_status", table_name="batch_expiry_review_sessions")
    op.drop_index("ix_batch_expiry_review_sessions_session_number", table_name="batch_expiry_review_sessions")
    op.drop_index("ix_batch_expiry_review_sessions_product_id", table_name="batch_expiry_review_sessions")
    op.drop_index("ix_batch_expiry_review_sessions_batch_lot_id", table_name="batch_expiry_review_sessions")
    op.drop_index("ix_batch_expiry_review_sessions_branch_id", table_name="batch_expiry_review_sessions")
    op.drop_index("ix_batch_expiry_review_sessions_tenant_id", table_name="batch_expiry_review_sessions")
    op.drop_table("batch_expiry_review_sessions")
