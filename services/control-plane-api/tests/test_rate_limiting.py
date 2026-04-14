from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def test_auth_exchange_rate_limit_throttles_repeated_requests() -> None:
    client = TestClient(
        create_app(
            database_url=sqlite_test_database_url("rate-limit-auth"),
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            rate_limit_window_seconds=60,
            rate_limit_auth_requests=2,
        )
    )

    for _ in range(2):
        response = client.post(
            "/v1/auth/oidc/exchange",
            json={"token": _stub_token(subject="platform-admin-1", email="admin@store.local", name="Platform Admin")},
        )
        assert response.status_code == 200

    throttled = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject="platform-admin-1", email="admin@store.local", name="Platform Admin")},
    )

    assert throttled.status_code == 429
    assert throttled.json()["detail"] == "Rate limit exceeded"


def test_webhook_rate_limit_throttles_repeated_requests() -> None:
    client = TestClient(
        create_app(
            database_url=sqlite_test_database_url("rate-limit-webhook"),
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            rate_limit_window_seconds=60,
            rate_limit_webhook_requests=2,
        )
    )

    for index in range(2):
        response = client.post(
            "/v1/billing/webhooks/razorpay",
            json={
                "event_id": f"rp_evt_{index}",
                "event_type": "subscription.activated",
                "tenant_id": "tenant-1",
                "provider_customer_id": "rp_cus_1",
                "provider_subscription_id": "rp_sub_1",
            },
        )
        assert response.status_code == 200

    throttled = client.post(
        "/v1/billing/webhooks/razorpay",
        json={
            "event_id": "rp_evt_3",
            "event_type": "subscription.activated",
            "tenant_id": "tenant-1",
            "provider_customer_id": "rp_cus_1",
            "provider_subscription_id": "rp_sub_1",
        },
    )

    assert throttled.status_code == 429
    assert throttled.json()["detail"] == "Rate limit exceeded"
