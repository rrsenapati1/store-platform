from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _create_owner_context(*, slug: str) -> tuple[TestClient, str, dict[str, str]]:
    database_url = sqlite_test_database_url(slug)
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
        json={"name": "Acme Retail", "slug": slug},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}
    return client, tenant_id, owner_headers


def _create_customer_profile(client: TestClient, *, tenant_id: str, headers: dict[str, str]) -> str:
    response = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=headers,
        json={
            "full_name": "Acme Traders",
            "phone": "+919999999999",
            "email": "billing@acme.example",
            "gstin": "29AAEPM0111C1Z3",
            "default_note": "Wholesale customer",
            "tags": ["wholesale"],
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_loyalty_program_can_be_saved_and_loaded() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="loyalty-program")

    updated = client.put(
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
        json={
            "status": "ACTIVE",
            "earn_points_per_currency_unit": 0.1,
            "redeem_step_points": 100,
            "redeem_value_per_step": 10.0,
            "minimum_redeem_points": 200,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "ACTIVE"
    assert updated.json()["earn_points_per_currency_unit"] == 0.1
    assert updated.json()["redeem_step_points"] == 100
    assert updated.json()["redeem_value_per_step"] == 10.0
    assert updated.json()["minimum_redeem_points"] == 200

    loaded = client.get(
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
    )
    assert loaded.status_code == 200
    assert loaded.json() == updated.json()


def test_customer_loyalty_adjustment_updates_balance_and_ledger_history() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="loyalty-adjustment")
    customer_profile_id = _create_customer_profile(client, tenant_id=tenant_id, headers=owner_headers)

    program = client.put(
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
        json={
            "status": "ACTIVE",
            "earn_points_per_currency_unit": 0.1,
            "redeem_step_points": 100,
            "redeem_value_per_step": 10.0,
            "minimum_redeem_points": 200,
        },
    )
    assert program.status_code == 200

    adjusted = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty/adjust",
        headers=owner_headers,
        json={"points_delta": 250, "note": "Welcome bonus"},
    )
    assert adjusted.status_code == 200
    assert adjusted.json()["customer_profile_id"] == customer_profile_id
    assert adjusted.json()["available_points"] == 250
    assert adjusted.json()["earned_total"] == 0
    assert adjusted.json()["adjusted_total"] == 250
    assert [entry["entry_type"] for entry in adjusted.json()["ledger_entries"]] == ["ADJUSTED"]
    assert adjusted.json()["ledger_entries"][0]["points_delta"] == 250
    assert adjusted.json()["ledger_entries"][0]["balance_after"] == 250

    summary = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty",
        headers=owner_headers,
    )
    assert summary.status_code == 200
    assert summary.json() == adjusted.json()


def test_customer_loyalty_summary_is_empty_before_any_activity() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="loyalty-empty-summary")
    customer_profile_id = _create_customer_profile(client, tenant_id=tenant_id, headers=owner_headers)

    summary = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty",
        headers=owner_headers,
    )
    assert summary.status_code == 200
    assert summary.json()["customer_profile_id"] == customer_profile_id
    assert summary.json()["available_points"] == 0
    assert summary.json()["earned_total"] == 0
    assert summary.json()["redeemed_total"] == 0
    assert summary.json()["adjusted_total"] == 0
    assert summary.json()["ledger_entries"] == []
