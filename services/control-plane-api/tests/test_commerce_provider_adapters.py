from store_control_plane.config.settings import build_settings
from store_control_plane.services.subscription_providers import build_subscription_provider


def test_stub_subscription_providers_build_deterministic_checkout_payloads() -> None:
    settings = build_settings()
    cashfree = build_subscription_provider("cashfree", settings)
    razorpay = build_subscription_provider("razorpay", settings)

    cashfree_bootstrap = cashfree.create_subscription_checkout(
        tenant_id="tenant-1",
        plan_code="launch-starter",
        tenant_name="Acme Retail",
    )
    razorpay_bootstrap = razorpay.create_subscription_checkout(
        tenant_id="tenant-1",
        plan_code="launch-starter",
        tenant_name="Acme Retail",
    )

    assert cashfree_bootstrap["provider_name"] == "cashfree"
    assert cashfree_bootstrap["checkout_url"].startswith("https://payments.store.local/cashfree/")
    assert cashfree_bootstrap["provider_subscription_id"].startswith("cashfree_sub_")
    assert razorpay_bootstrap["provider_name"] == "razorpay"
    assert razorpay_bootstrap["checkout_url"].startswith("https://payments.store.local/razorpay/")
    assert razorpay_bootstrap["provider_subscription_id"].startswith("razorpay_sub_")


def test_stub_subscription_providers_normalize_webhook_payloads() -> None:
    settings = build_settings()
    cashfree = build_subscription_provider("cashfree", settings)

    normalized = cashfree.normalize_webhook_payload(
        {
            "event_id": "cf_evt_1",
            "event_type": "subscription.activated",
            "tenant_id": "tenant-1",
            "provider_customer_id": "cf_customer_tenant_1",
            "provider_subscription_id": "cf_sub_tenant_1",
        }
    )

    assert normalized["provider_name"] == "cashfree"
    assert normalized["provider_event_id"] == "cf_evt_1"
    assert normalized["event_type"] == "subscription.activated"
    assert normalized["tenant_id"] == "tenant-1"
