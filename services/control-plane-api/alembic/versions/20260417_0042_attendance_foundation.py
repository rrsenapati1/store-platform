"""add attendance session foundation

Revision ID: 20260417_0042
Revises: 20260417_0041
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0042"
down_revision = "20260417_0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branch_attendance_sessions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), nullable=False),
        sa.Column("branch_id", sa.String(length=32), nullable=False),
        sa.Column("device_registration_id", sa.String(length=32), nullable=False),
        sa.Column("staff_profile_id", sa.String(length=32), nullable=False),
        sa.Column("runtime_user_id", sa.String(length=32), nullable=True),
        sa.Column("opened_by_user_id", sa.String(length=32), nullable=True),
        sa.Column("closed_by_user_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("attendance_number", sa.String(length=64), nullable=False),
        sa.Column("clock_in_note", sa.String(length=1024), nullable=True),
        sa.Column("clock_out_note", sa.String(length=1024), nullable=True),
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
        sa.UniqueConstraint("branch_id", "attendance_number", name="uq_branch_attendance_sessions_branch_number"),
    )
    op.create_index(op.f("ix_branch_attendance_sessions_tenant_id"), "branch_attendance_sessions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_branch_id"), "branch_attendance_sessions", ["branch_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_device_registration_id"), "branch_attendance_sessions", ["device_registration_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_staff_profile_id"), "branch_attendance_sessions", ["staff_profile_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_runtime_user_id"), "branch_attendance_sessions", ["runtime_user_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_opened_by_user_id"), "branch_attendance_sessions", ["opened_by_user_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_closed_by_user_id"), "branch_attendance_sessions", ["closed_by_user_id"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_status"), "branch_attendance_sessions", ["status"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_attendance_number"), "branch_attendance_sessions", ["attendance_number"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_opened_at"), "branch_attendance_sessions", ["opened_at"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_closed_at"), "branch_attendance_sessions", ["closed_at"], unique=False)
    op.create_index(op.f("ix_branch_attendance_sessions_last_activity_at"), "branch_attendance_sessions", ["last_activity_at"], unique=False)

    op.add_column("branch_cashier_sessions", sa.Column("attendance_session_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_branch_cashier_sessions_attendance_session_id",
        "branch_cashier_sessions",
        "branch_attendance_sessions",
        ["attendance_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_branch_cashier_sessions_attendance_session_id"), "branch_cashier_sessions", ["attendance_session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_branch_cashier_sessions_attendance_session_id"), table_name="branch_cashier_sessions")
    op.drop_constraint("fk_branch_cashier_sessions_attendance_session_id", "branch_cashier_sessions", type_="foreignkey")
    op.drop_column("branch_cashier_sessions", "attendance_session_id")

    op.drop_index(op.f("ix_branch_attendance_sessions_last_activity_at"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_closed_at"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_opened_at"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_attendance_number"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_status"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_closed_by_user_id"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_opened_by_user_id"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_runtime_user_id"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_staff_profile_id"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_device_registration_id"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_branch_id"), table_name="branch_attendance_sessions")
    op.drop_index(op.f("ix_branch_attendance_sessions_tenant_id"), table_name="branch_attendance_sessions")
    op.drop_table("branch_attendance_sessions")
