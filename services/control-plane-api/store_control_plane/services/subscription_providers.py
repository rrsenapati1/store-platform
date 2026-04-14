from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings


@dataclass(slots=True)
class StubSubscriptionProvider:
    provider_name: str
    checkout_base_url: str

    def create_subscription_checkout(self, *, tenant_id: str, plan_code: str, tenant_name: str) -> dict[str, str]:
        tenant_key = tenant_id.replace("-", "_")
        plan_key = plan_code.replace("-", "_")
        return {
            "provider_name": self.provider_name,
            "provider_customer_id": f"{self.provider_name}_customer_{tenant_key}",
            "provider_subscription_id": f"{self.provider_name}_sub_{tenant_key}_{plan_key}",
            "checkout_url": f"{self.checkout_base_url}/{self.provider_name}/{tenant_id}/{plan_code}",
            "mandate_status": "PENDING_SETUP",
            "tenant_name": tenant_name,
        }

    def normalize_webhook_payload(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "provider_name": self.provider_name,
            "provider_event_id": str(payload["event_id"]),
            "event_type": str(payload["event_type"]),
            "tenant_id": payload.get("tenant_id"),
            "provider_customer_id": payload.get("provider_customer_id"),
            "provider_subscription_id": payload.get("provider_subscription_id"),
            "current_period_started_at": payload.get("current_period_started_at"),
            "current_period_ends_at": payload.get("current_period_ends_at"),
            "grace_until": payload.get("grace_until"),
            "payload": payload,
        }


def build_subscription_provider(provider_name: str, settings: Settings) -> StubSubscriptionProvider:
    normalized_provider = provider_name.strip().lower()
    if normalized_provider not in {"cashfree", "razorpay"}:
        raise ValueError(f"Unsupported subscription provider: {provider_name}")
    return StubSubscriptionProvider(
        provider_name=normalized_provider,
        checkout_base_url=settings.subscription_checkout_base_url.rstrip("/"),
    )
