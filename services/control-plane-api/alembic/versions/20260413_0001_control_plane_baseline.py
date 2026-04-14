"""control plane baseline

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13 07:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("external_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_external_subject", "users", ["external_subject"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "platform_admin_accounts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_platform_admin_accounts_user_id", "platform_admin_accounts", ["user_id"], unique=True)

    op.create_table(
        "app_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_app_sessions_user_id", "app_sessions", ["user_id"], unique=False)
    op.create_index("ix_app_sessions_token", "app_sessions", ["token"], unique=True)

    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("onboarding_status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "branches",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("gstin", sa.String(length=32), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_branches_tenant_id", "branches", ["tenant_id"], unique=False)

    op.create_table(
        "owner_invites",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("invited_by_user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("accepted_by_user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_owner_invites_tenant_id", "owner_invites", ["tenant_id"], unique=False)
    op.create_index("ix_owner_invites_email", "owner_invites", ["email"], unique=False)

    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("invite_email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"], unique=False)
    op.create_index("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"], unique=False)
    op.create_index("ix_tenant_memberships_invite_email", "tenant_memberships", ["invite_email"], unique=False)

    op.create_table(
        "branch_memberships",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("invite_email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_branch_memberships_tenant_id", "branch_memberships", ["tenant_id"], unique=False)
    op.create_index("ix_branch_memberships_branch_id", "branch_memberships", ["branch_id"], unique=False)
    op.create_index("ix_branch_memberships_user_id", "branch_memberships", ["user_id"], unique=False)
    op.create_index("ix_branch_memberships_invite_email", "branch_memberships", ["invite_email"], unique=False)

    op.create_table(
        "role_definitions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("role_name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_role_definitions_scope", "role_definitions", ["scope"], unique=False)
    op.create_index("ix_role_definitions_role_name", "role_definitions", ["role_name"], unique=True)

    op.create_table(
        "role_capabilities",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("role_definition_id", sa.String(length=32), sa.ForeignKey("role_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capability", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_role_capabilities_role_definition_id", "role_capabilities", ["role_definition_id"], unique=False)
    op.create_index("ix_role_capabilities_capability", "role_capabilities", ["capability"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("branch_id", sa.String(length=32), sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("actor_user_id", sa.String(length=32), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"], unique=False)
    op.create_index("ix_audit_events_branch_id", "audit_events", ["branch_id"], unique=False)
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_events_action", "audit_events", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_branch_id", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_role_capabilities_capability", table_name="role_capabilities")
    op.drop_index("ix_role_capabilities_role_definition_id", table_name="role_capabilities")
    op.drop_table("role_capabilities")

    op.drop_index("ix_role_definitions_role_name", table_name="role_definitions")
    op.drop_index("ix_role_definitions_scope", table_name="role_definitions")
    op.drop_table("role_definitions")

    op.drop_index("ix_branch_memberships_invite_email", table_name="branch_memberships")
    op.drop_index("ix_branch_memberships_user_id", table_name="branch_memberships")
    op.drop_index("ix_branch_memberships_branch_id", table_name="branch_memberships")
    op.drop_index("ix_branch_memberships_tenant_id", table_name="branch_memberships")
    op.drop_table("branch_memberships")

    op.drop_index("ix_tenant_memberships_invite_email", table_name="tenant_memberships")
    op.drop_index("ix_tenant_memberships_user_id", table_name="tenant_memberships")
    op.drop_index("ix_tenant_memberships_tenant_id", table_name="tenant_memberships")
    op.drop_table("tenant_memberships")

    op.drop_index("ix_owner_invites_email", table_name="owner_invites")
    op.drop_index("ix_owner_invites_tenant_id", table_name="owner_invites")
    op.drop_table("owner_invites")

    op.drop_index("ix_branches_tenant_id", table_name="branches")
    op.drop_table("branches")

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")

    op.drop_index("ix_app_sessions_token", table_name="app_sessions")
    op.drop_index("ix_app_sessions_user_id", table_name="app_sessions")
    op.drop_table("app_sessions")

    op.drop_index("ix_platform_admin_accounts_user_id", table_name="platform_admin_accounts")
    op.drop_table("platform_admin_accounts")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_external_subject", table_name="users")
    op.drop_table("users")
