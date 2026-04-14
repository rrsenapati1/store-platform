from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BillingPlanCreateRequest(BaseModel):
    code: str
    display_name: str
    billing_cadence: str
    currency_code: str
    amount_minor: int
    trial_days: int
    branch_limit: int
    device_limit: int
    offline_runtime_hours: int
    grace_window_days: int
    feature_flags: dict[str, Any] = Field(default_factory=dict)
    provider_plan_refs: dict[str, str] = Field(default_factory=dict)
    is_default: bool = False


class BillingPlanResponse(BaseModel):
    id: str
    code: str
    display_name: str
    billing_cadence: str
    currency_code: str
    amount_minor: int
    trial_days: int
    branch_limit: int
    device_limit: int
    offline_runtime_hours: int
    grace_window_days: int
    feature_flags: dict[str, Any]
    provider_plan_refs: dict[str, str]
    is_default: bool
    status: str


class BillingPlanListResponse(BaseModel):
    records: list[BillingPlanResponse]


class TenantSubscriptionSummaryResponse(BaseModel):
    id: str
    tenant_id: str
    billing_plan_id: str
    provider_name: str | None = None
    provider_customer_id: str | None = None
    provider_subscription_id: str | None = None
    lifecycle_status: str
    mandate_status: str | None = None
    trial_started_at: str | None = None
    trial_ends_at: str | None = None
    current_period_started_at: str | None = None
    current_period_ends_at: str | None = None
    grace_until: str | None = None
    canceled_at: str | None = None


class TenantEntitlementResponse(BaseModel):
    id: str
    tenant_id: str
    billing_plan_id: str | None = None
    active_plan_code: str
    lifecycle_status: str
    branch_limit: int
    device_limit: int
    offline_runtime_hours: int
    grace_until: str | None = None
    suspend_at: str | None = None
    feature_flags: dict[str, Any]
    policy_source: str
    policy_metadata: dict[str, Any]


class TenantBillingOverrideRequest(BaseModel):
    grants_lifecycle_status: str = "ACTIVE"
    branch_limit_override: int | None = None
    device_limit_override: int | None = None
    offline_runtime_hours_override: int | None = None
    feature_flags_override: dict[str, Any] = Field(default_factory=dict)
    reason: str
    expires_at: str


class TenantBillingOverrideResponse(BaseModel):
    id: str
    tenant_id: str
    grants_lifecycle_status: str
    branch_limit_override: int | None = None
    device_limit_override: int | None = None
    offline_runtime_hours_override: int | None = None
    feature_flags_override: dict[str, Any]
    reason: str
    expires_at: str
    status: str


class TenantLifecycleSummaryResponse(BaseModel):
    tenant_id: str
    subscription: TenantSubscriptionSummaryResponse
    entitlement: TenantEntitlementResponse
    active_override: TenantBillingOverrideResponse | None = None


class SubscriptionBootstrapRequest(BaseModel):
    provider_name: str


class SubscriptionBootstrapResponse(BaseModel):
    provider_name: str
    provider_customer_id: str
    provider_subscription_id: str
    checkout_url: str
    mandate_status: str


class SubscriptionWebhookResponse(BaseModel):
    status: str
    event: dict[str, Any]
    subscription: dict[str, Any] | None = None
    entitlement: dict[str, Any] | None = None
