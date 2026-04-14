from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from ..utils import utc_now


class BillingPlan(Base, TimestampMixin):
    __tablename__ = "billing_plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    billing_cadence: Mapped[str] = mapped_column(String(32))
    currency_code: Mapped[str] = mapped_column(String(8))
    amount_minor: Mapped[int] = mapped_column(Integer)
    trial_days: Mapped[int] = mapped_column(Integer, default=0)
    branch_limit: Mapped[int] = mapped_column(Integer)
    device_limit: Mapped[int] = mapped_column(Integer)
    offline_runtime_hours: Mapped[int] = mapped_column(Integer, default=0)
    grace_window_days: Mapped[int] = mapped_column(Integer, default=0)
    feature_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    provider_plan_refs: Mapped[dict] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)


class TenantSubscription(Base, TimestampMixin):
    __tablename__ = "tenant_subscriptions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    billing_plan_id: Mapped[str] = mapped_column(ForeignKey("billing_plans.id", ondelete="RESTRICT"), index=True)
    provider_name: Mapped[str | None] = mapped_column(String(32), default=None, index=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), default=None)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), default=None, index=True)
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="TRIALING", index=True)
    mandate_status: Mapped[str | None] = mapped_column(String(64), default=None)
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    current_period_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    current_period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    last_provider_event_id: Mapped[str | None] = mapped_column(String(255), default=None)
    last_provider_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class TenantEntitlement(Base, TimestampMixin):
    __tablename__ = "tenant_entitlements"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True)
    billing_plan_id: Mapped[str | None] = mapped_column(ForeignKey("billing_plans.id", ondelete="SET NULL"), default=None, index=True)
    active_plan_code: Mapped[str] = mapped_column(String(64))
    lifecycle_status: Mapped[str] = mapped_column(String(32), index=True)
    branch_limit: Mapped[int] = mapped_column(Integer)
    device_limit: Mapped[int] = mapped_column(Integer)
    offline_runtime_hours: Mapped[int] = mapped_column(Integer, default=0)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    suspend_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    feature_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    policy_source: Mapped[str] = mapped_column(String(64), default="subscription")
    policy_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    last_policy_change_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utc_now)


class SubscriptionWebhookEvent(Base):
    __tablename__ = "subscription_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider_name", "provider_event_id", name="uq_subscription_webhook_events_provider_event"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(32), index=True)
    provider_event_id: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), default=None, index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    processing_status: Mapped[str] = mapped_column(String(32), default="RECEIVED", index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utc_now, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    error_message: Mapped[str | None] = mapped_column(String(1024), default=None)


class TenantBillingOverride(Base, TimestampMixin):
    __tablename__ = "tenant_billing_overrides"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), default=None, index=True)
    grants_lifecycle_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    branch_limit_override: Mapped[int | None] = mapped_column(Integer, default=None)
    device_limit_override: Mapped[int | None] = mapped_column(Integer, default=None)
    offline_runtime_hours_override: Mapped[int | None] = mapped_column(Integer, default=None)
    feature_flags_override: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(String(512))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
