"""saas billing plans, subscriptions, entitlements, and webhook events

Revision ID: 20260414_0022
Revises: 20260414_0021
Create Date: 2026-04-14 23:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260414_0022"
down_revision = "20260414_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("billing_cadence", sa.String(length=32), nullable=False),
        sa.Column("currency_code", sa.String(length=8), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("branch_limit", sa.Integer(), nullable=False),
        sa.Column("device_limit", sa.Integer(), nullable=False),
        sa.Column("offline_runtime_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grace_window_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feature_flags", sa.JSON(), nullable=False),
        sa.Column("provider_plan_refs", sa.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("code", name="uq_billing_plans_code"),
    )
    op.create_index("ix_billing_plans_code", "billing_plans", ["code"])
    op.create_index("ix_billing_plans_is_default", "billing_plans", ["is_default"])
    op.create_index("ix_billing_plans_status", "billing_plans", ["status"])

    op.create_table(
        "tenant_subscriptions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("billing_plan_id", sa.String(length=32), sa.ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider_name", sa.String(length=32), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("mandate_status", sa.String(length=64), nullable=True),
        sa.Column("trial_started_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("current_period_started_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("current_period_ends_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("grace_until", sa.DateTime(timezone=False), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("last_provider_event_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_tenant_subscriptions_tenant_id", "tenant_subscriptions", ["tenant_id"])
    op.create_index("ix_tenant_subscriptions_billing_plan_id", "tenant_subscriptions", ["billing_plan_id"])
    op.create_index("ix_tenant_subscriptions_provider_name", "tenant_subscriptions", ["provider_name"])
    op.create_index("ix_tenant_subscriptions_provider_subscription_id", "tenant_subscriptions", ["provider_subscription_id"])
    op.create_index("ix_tenant_subscriptions_lifecycle_status", "tenant_subscriptions", ["lifecycle_status"])
    op.create_index("ix_tenant_subscriptions_trial_ends_at", "tenant_subscriptions", ["trial_ends_at"])
    op.create_index("ix_tenant_subscriptions_current_period_ends_at", "tenant_subscriptions", ["current_period_ends_at"])
    op.create_index("ix_tenant_subscriptions_grace_until", "tenant_subscriptions", ["grace_until"])
    op.create_index("ix_tenant_subscriptions_canceled_at", "tenant_subscriptions", ["canceled_at"])

    op.create_table(
        "tenant_entitlements",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("billing_plan_id", sa.String(length=32), sa.ForeignKey("billing_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("active_plan_code", sa.String(length=64), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("branch_limit", sa.Integer(), nullable=False),
        sa.Column("device_limit", sa.Integer(), nullable=False),
        sa.Column("offline_runtime_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grace_until", sa.DateTime(timezone=False), nullable=True),
        sa.Column("suspend_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("feature_flags", sa.JSON(), nullable=False),
        sa.Column("policy_source", sa.String(length=64), nullable=False),
        sa.Column("policy_metadata", sa.JSON(), nullable=False),
        sa.Column("last_policy_change_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_entitlements_tenant_id"),
    )
    op.create_index("ix_tenant_entitlements_tenant_id", "tenant_entitlements", ["tenant_id"])
    op.create_index("ix_tenant_entitlements_billing_plan_id", "tenant_entitlements", ["billing_plan_id"])
    op.create_index("ix_tenant_entitlements_lifecycle_status", "tenant_entitlements", ["lifecycle_status"])
    op.create_index("ix_tenant_entitlements_grace_until", "tenant_entitlements", ["grace_until"])
    op.create_index("ix_tenant_entitlements_suspend_at", "tenant_entitlements", ["suspend_at"])

    op.create_table(
        "subscription_webhook_events",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("provider_name", sa.String(length=32), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="RECEIVED"),
        sa.Column("received_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.UniqueConstraint("provider_name", "provider_event_id", name="uq_subscription_webhook_events_provider_event"),
    )
    op.create_index("ix_subscription_webhook_events_provider_name", "subscription_webhook_events", ["provider_name"])
    op.create_index("ix_subscription_webhook_events_tenant_id", "subscription_webhook_events", ["tenant_id"])
    op.create_index("ix_subscription_webhook_events_event_type", "subscription_webhook_events", ["event_type"])
    op.create_index("ix_subscription_webhook_events_processing_status", "subscription_webhook_events", ["processing_status"])
    op.create_index("ix_subscription_webhook_events_received_at", "subscription_webhook_events", ["received_at"])

    op.create_table(
        "tenant_billing_overrides",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("tenant_id", sa.String(length=32), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("grants_lifecycle_status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("branch_limit_override", sa.Integer(), nullable=True),
        sa.Column("device_limit_override", sa.Integer(), nullable=True),
        sa.Column("offline_runtime_hours_override", sa.Integer(), nullable=True),
        sa.Column("feature_flags_override", sa.JSON(), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_tenant_billing_overrides_tenant_id", "tenant_billing_overrides", ["tenant_id"])
    op.create_index("ix_tenant_billing_overrides_created_by_user_id", "tenant_billing_overrides", ["created_by_user_id"])
    op.create_index("ix_tenant_billing_overrides_expires_at", "tenant_billing_overrides", ["expires_at"])
    op.create_index("ix_tenant_billing_overrides_revoked_at", "tenant_billing_overrides", ["revoked_at"])
    op.create_index("ix_tenant_billing_overrides_status", "tenant_billing_overrides", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tenant_billing_overrides_status", table_name="tenant_billing_overrides")
    op.drop_index("ix_tenant_billing_overrides_revoked_at", table_name="tenant_billing_overrides")
    op.drop_index("ix_tenant_billing_overrides_expires_at", table_name="tenant_billing_overrides")
    op.drop_index("ix_tenant_billing_overrides_created_by_user_id", table_name="tenant_billing_overrides")
    op.drop_index("ix_tenant_billing_overrides_tenant_id", table_name="tenant_billing_overrides")
    op.drop_table("tenant_billing_overrides")

    op.drop_index("ix_subscription_webhook_events_received_at", table_name="subscription_webhook_events")
    op.drop_index("ix_subscription_webhook_events_processing_status", table_name="subscription_webhook_events")
    op.drop_index("ix_subscription_webhook_events_event_type", table_name="subscription_webhook_events")
    op.drop_index("ix_subscription_webhook_events_tenant_id", table_name="subscription_webhook_events")
    op.drop_index("ix_subscription_webhook_events_provider_name", table_name="subscription_webhook_events")
    op.drop_table("subscription_webhook_events")

    op.drop_index("ix_tenant_entitlements_suspend_at", table_name="tenant_entitlements")
    op.drop_index("ix_tenant_entitlements_grace_until", table_name="tenant_entitlements")
    op.drop_index("ix_tenant_entitlements_lifecycle_status", table_name="tenant_entitlements")
    op.drop_index("ix_tenant_entitlements_billing_plan_id", table_name="tenant_entitlements")
    op.drop_index("ix_tenant_entitlements_tenant_id", table_name="tenant_entitlements")
    op.drop_table("tenant_entitlements")

    op.drop_index("ix_tenant_subscriptions_canceled_at", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_grace_until", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_current_period_ends_at", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_trial_ends_at", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_lifecycle_status", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_provider_subscription_id", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_provider_name", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_billing_plan_id", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_tenant_id", table_name="tenant_subscriptions")
    op.drop_table("tenant_subscriptions")

    op.drop_index("ix_billing_plans_status", table_name="billing_plans")
    op.drop_index("ix_billing_plans_is_default", table_name="billing_plans")
    op.drop_index("ix_billing_plans_code", table_name="billing_plans")
    op.drop_table("billing_plans")
