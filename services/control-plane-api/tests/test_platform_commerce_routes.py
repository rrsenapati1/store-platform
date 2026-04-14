from datetime import timedelta

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.utils import utc_now


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def test_platform_admin_manages_billing_plans_tenant_lifecycle_and_overrides() -> None:
    database_url = sqlite_test_database_url("platform-commerce-routes")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    plan_create = client.post(
        "/v1/platform/billing/plans",
        headers=admin_headers,
        json={
            "code": "scale-growth",
            "display_name": "Scale Growth",
            "billing_cadence": "monthly",
            "currency_code": "INR",
            "amount_minor": 349900,
            "trial_days": 14,
            "branch_limit": 8,
            "device_limit": 20,
            "offline_runtime_hours": 72,
            "grace_window_days": 7,
            "feature_flags": {"offline_continuity": True},
            "provider_plan_refs": {"cashfree": "cf_plan_scale_growth", "razorpay": "rp_plan_scale_growth"},
            "is_default": False,
        },
    )
    assert plan_create.status_code == 200
    assert plan_create.json()["code"] == "scale-growth"

    plans = client.get("/v1/platform/billing/plans", headers=admin_headers)
    assert plans.status_code == 200
    assert {record["code"] for record in plans.json()["records"]} >= {"launch-starter", "scale-growth"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    lifecycle_summary = client.get(
        f"/v1/platform/tenants/{tenant_id}/billing-lifecycle",
        headers=admin_headers,
    )
    assert lifecycle_summary.status_code == 200
    assert lifecycle_summary.json()["subscription"]["lifecycle_status"] == "TRIALING"
    assert lifecycle_summary.json()["entitlement"]["lifecycle_status"] == "TRIALING"
    assert lifecycle_summary.json()["entitlement"]["active_plan_code"] == "launch-starter"

    suspend = client.post(
        f"/v1/platform/tenants/{tenant_id}/billing/suspend",
        headers=admin_headers,
        json={"reason": "Billing review hold"},
    )
    assert suspend.status_code == 200
    assert suspend.json()["entitlement"]["lifecycle_status"] == "SUSPENDED"

    reactivate = client.post(
        f"/v1/platform/tenants/{tenant_id}/billing/reactivate",
        headers=admin_headers,
    )
    assert reactivate.status_code == 200
    assert reactivate.json()["entitlement"]["lifecycle_status"] == "TRIALING"

    override = client.post(
        f"/v1/platform/tenants/{tenant_id}/billing/overrides",
        headers=admin_headers,
        json={
            "grants_lifecycle_status": "ACTIVE",
            "device_limit_override": 10,
            "feature_flags_override": {"manual_recovery": True},
            "reason": "Launch support window",
            "expires_at": (utc_now() + timedelta(days=2)).isoformat(),
        },
    )
    assert override.status_code == 200
    assert override.json()["active_override"]["device_limit_override"] == 10
    assert override.json()["entitlement"]["lifecycle_status"] == "ACTIVE"


def test_owner_bootstrap_and_provider_webhook_activate_subscription() -> None:
    database_url = sqlite_test_database_url("owner-commerce-routes")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Orbit Retail", "slug": "orbit-retail"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@orbit.local", "full_name": "Orbit Owner"},
    )
    assert invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@orbit.local", name="Orbit Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    bootstrap = client.post(
        f"/v1/tenants/{tenant_id}/billing/subscription-bootstrap",
        headers=owner_headers,
        json={"provider_name": "razorpay"},
    )
    assert bootstrap.status_code == 200
    provider_subscription_id = bootstrap.json()["provider_subscription_id"]
    provider_customer_id = bootstrap.json()["provider_customer_id"]

    webhook = client.post(
        "/v1/billing/webhooks/razorpay",
        json={
            "event_id": "rp_evt_activate_1",
            "event_type": "subscription.activated",
            "tenant_id": tenant_id,
            "provider_customer_id": provider_customer_id,
            "provider_subscription_id": provider_subscription_id,
            "current_period_started_at": utc_now().isoformat(),
            "current_period_ends_at": (utc_now() + timedelta(days=30)).isoformat(),
        },
    )
    assert webhook.status_code == 200
    assert webhook.json()["status"] == "ok"

    lifecycle_summary = client.get(
        f"/v1/platform/tenants/{tenant_id}/billing-lifecycle",
        headers=admin_headers,
    )
    assert lifecycle_summary.status_code == 200
    assert lifecycle_summary.json()["subscription"]["lifecycle_status"] == "ACTIVE"
    assert lifecycle_summary.json()["subscription"]["provider_name"] == "razorpay"
    assert lifecycle_summary.json()["entitlement"]["lifecycle_status"] == "ACTIVE"


def test_owner_reads_current_tenant_billing_lifecycle() -> None:
    database_url = sqlite_test_database_url("owner-commerce-lifecycle-read")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Northwind Retail", "slug": "northwind-retail"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@northwind.local", "full_name": "Northwind Owner"},
    )
    assert invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@northwind.local", name="Northwind Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    lifecycle_summary = client.get(
        f"/v1/tenants/{tenant_id}/billing/lifecycle",
        headers=owner_headers,
    )
    assert lifecycle_summary.status_code == 200
    assert lifecycle_summary.json()["subscription"]["lifecycle_status"] == "TRIALING"
    assert lifecycle_summary.json()["entitlement"]["active_plan_code"] == "launch-starter"
