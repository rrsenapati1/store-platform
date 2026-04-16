"""add restock task sessions

Revision ID: 20260416_0029
Revises: 20260415_0028
Create Date: 2026-04-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260416_0029"
down_revision = "20260415_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restock_task_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(length=32), sa.ForeignKey("catalog_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("stock_on_hand_snapshot", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reorder_point_snapshot", sa.Float(), nullable=False, server_default="0"),
        sa.Column("target_stock_snapshot", sa.Float(), nullable=False, server_default="0"),
        sa.Column("suggested_quantity_snapshot", sa.Float(), nullable=False, server_default="0"),
        sa.Column("requested_quantity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("picked_quantity", sa.Float(), nullable=True),
        sa.Column("source_posture", sa.String(length=64), nullable=False),
        sa.Column("note", sa.String(length=1024), nullable=True),
        sa.Column("completion_note", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("branch_id", "task_number", name="uq_restock_task_sessions_branch_number"),
    )
    op.create_index("ix_restock_task_sessions_tenant_id", "restock_task_sessions", ["tenant_id"])
    op.create_index("ix_restock_task_sessions_branch_id", "restock_task_sessions", ["branch_id"])
    op.create_index("ix_restock_task_sessions_product_id", "restock_task_sessions", ["product_id"])
    op.create_index("ix_restock_task_sessions_task_number", "restock_task_sessions", ["task_number"])
    op.create_index("ix_restock_task_sessions_status", "restock_task_sessions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_restock_task_sessions_status", table_name="restock_task_sessions")
    op.drop_index("ix_restock_task_sessions_task_number", table_name="restock_task_sessions")
    op.drop_index("ix_restock_task_sessions_product_id", table_name="restock_task_sessions")
    op.drop_index("ix_restock_task_sessions_branch_id", table_name="restock_task_sessions")
    op.drop_index("ix_restock_task_sessions_tenant_id", table_name="restock_task_sessions")
    op.drop_table("restock_task_sessions")
