"""add cashier session governance

Revision ID: 20260417_0041
Revises: 20260417_0040
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0041"
down_revision = "20260417_0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branch_cashier_sessions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("device_registration_id", sa.String(length=32), nullable=False),
        sa.Column("staff_profile_id", sa.String(length=32), nullable=False),
        sa.Column("runtime_user_id", sa.String(length=32), nullable=True),
        sa.Column("opened_by_user_id", sa.String(length=32), nullable=True),
        sa.Column("closed_by_user_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("session_number", sa.String(length=64), nullable=False),
        sa.Column("opening_float_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("opening_note", sa.String(length=1024), nullable=True),
        sa.Column("closing_note", sa.String(length=1024), nullable=True),
        sa.Column("force_close_reason", sa.String(length=1024), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_registration_id"], ["device_registrations.id"]),
        sa.ForeignKeyConstraint(["staff_profile_id"], ["staff_profiles.id"]),
        sa.ForeignKeyConstraint(["runtime_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "session_number", name="uq_branch_cashier_sessions_branch_number"),
    )
    op.create_index(op.f("ix_branch_cashier_sessions_tenant_id"), "branch_cashier_sessions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_branch_id"), "branch_cashier_sessions", ["branch_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_device_registration_id"), "branch_cashier_sessions", ["device_registration_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_staff_profile_id"), "branch_cashier_sessions", ["staff_profile_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_runtime_user_id"), "branch_cashier_sessions", ["runtime_user_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_opened_by_user_id"), "branch_cashier_sessions", ["opened_by_user_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_closed_by_user_id"), "branch_cashier_sessions", ["closed_by_user_id"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_status"), "branch_cashier_sessions", ["status"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_session_number"), "branch_cashier_sessions", ["session_number"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_opened_at"), "branch_cashier_sessions", ["opened_at"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_closed_at"), "branch_cashier_sessions", ["closed_at"], unique=False)
    op.create_index(op.f("ix_branch_cashier_sessions_last_activity_at"), "branch_cashier_sessions", ["last_activity_at"], unique=False)

    op.add_column("sales", sa.Column("cashier_session_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_sales_cashier_session_id",
        "sales",
        "branch_cashier_sessions",
        ["cashier_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_sales_cashier_session_id"), "sales", ["cashier_session_id"], unique=False)

    op.add_column("sale_returns", sa.Column("cashier_session_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_sale_returns_cashier_session_id",
        "sale_returns",
        "branch_cashier_sessions",
        ["cashier_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_sale_returns_cashier_session_id"), "sale_returns", ["cashier_session_id"], unique=False)

    op.add_column("checkout_payment_sessions", sa.Column("cashier_session_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_checkout_payment_sessions_cashier_session_id",
        "checkout_payment_sessions",
        "branch_cashier_sessions",
        ["cashier_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_checkout_payment_sessions_cashier_session_id"),
        "checkout_payment_sessions",
        ["cashier_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_checkout_payment_sessions_cashier_session_id"), table_name="checkout_payment_sessions")
    op.drop_constraint("fk_checkout_payment_sessions_cashier_session_id", "checkout_payment_sessions", type_="foreignkey")
    op.drop_column("checkout_payment_sessions", "cashier_session_id")

    op.drop_index(op.f("ix_sale_returns_cashier_session_id"), table_name="sale_returns")
    op.drop_constraint("fk_sale_returns_cashier_session_id", "sale_returns", type_="foreignkey")
    op.drop_column("sale_returns", "cashier_session_id")

    op.drop_index(op.f("ix_sales_cashier_session_id"), table_name="sales")
    op.drop_constraint("fk_sales_cashier_session_id", "sales", type_="foreignkey")
    op.drop_column("sales", "cashier_session_id")

    op.drop_index(op.f("ix_branch_cashier_sessions_last_activity_at"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_closed_at"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_opened_at"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_session_number"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_status"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_closed_by_user_id"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_opened_by_user_id"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_runtime_user_id"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_staff_profile_id"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_device_registration_id"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_branch_id"), table_name="branch_cashier_sessions")
    op.drop_index(op.f("ix_branch_cashier_sessions_tenant_id"), table_name="branch_cashier_sessions")
    op.drop_table("branch_cashier_sessions")
