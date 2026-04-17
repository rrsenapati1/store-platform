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


def test_customer_profiles_can_be_created_searched_updated_and_archived() -> None:
    database_url = sqlite_test_database_url("customer-profile-flow")
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
        json={"name": "Acme Retail", "slug": "acme-retail-customer-profiles"},
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

    created = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        json={
            "full_name": "Acme Traders",
            "phone": "+919999999999",
            "email": "accounts@acme.example",
            "gstin": "29AAEPM0111C1Z3",
            "default_note": "Preferred wholesale buyer",
            "tags": ["wholesale", "priority"],
        },
    )
    assert created.status_code == 200
    profile_id = created.json()["id"]
    assert created.json()["status"] == "ACTIVE"

    search_by_name = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        params={"query": "Acme"},
    )
    assert search_by_name.status_code == 200
    assert [record["id"] for record in search_by_name.json()["records"]] == [profile_id]

    search_by_gstin = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        params={"query": "29AAEPM0111C1Z3"},
    )
    assert search_by_gstin.status_code == 200
    assert [record["id"] for record in search_by_gstin.json()["records"]] == [profile_id]

    duplicate = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        json={
            "full_name": "Duplicate Acme",
            "phone": None,
            "email": None,
            "gstin": "29AAEPM0111C1Z3",
            "default_note": None,
            "tags": [],
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Customer GSTIN already exists"

    updated = client.patch(
        f"/v1/tenants/{tenant_id}/customer-profiles/{profile_id}",
        headers=owner_headers,
        json={
            "full_name": "Acme Traders LLP",
            "phone": "+918888888888",
            "email": "gst@acme.example",
            "default_note": "Updated credit note",
            "tags": ["wholesale"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Acme Traders LLP"
    assert updated.json()["phone"] == "+918888888888"
    assert updated.json()["email"] == "gst@acme.example"

    archived = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{profile_id}/archive",
        headers=owner_headers,
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"

    active_only = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        params={"status": "ACTIVE"},
    )
    assert active_only.status_code == 200
    assert active_only.json()["records"] == []

    reactivated = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{profile_id}/reactivate",
        headers=owner_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"

    fetched = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{profile_id}",
        headers=owner_headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == profile_id
    assert fetched.json()["full_name"] == "Acme Traders LLP"


def test_customer_profiles_can_assign_and_clear_default_price_tier() -> None:
    database_url = sqlite_test_database_url("customer-profile-default-price-tier")
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
        json={"name": "Acme Retail", "slug": "acme-retail-customer-price-tiers"},
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

    price_tier = client.post(
        f"/v1/tenants/{tenant_id}/price-tiers",
        headers=owner_headers,
        json={"code": "WHOLESALE", "display_name": "Wholesale", "status": "ACTIVE"},
    )
    assert price_tier.status_code == 200
    price_tier_id = price_tier.json()["id"]

    created = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        json={
            "full_name": "Acme Traders",
            "phone": None,
            "email": None,
            "gstin": None,
            "default_note": None,
            "tags": [],
            "default_price_tier_id": price_tier_id,
        },
    )
    assert created.status_code == 200
    profile_id = created.json()["id"]
    assert created.json()["default_price_tier_id"] == price_tier_id
    assert created.json()["default_price_tier_code"] == "WHOLESALE"
    assert created.json()["default_price_tier_display_name"] == "Wholesale"

    fetched = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{profile_id}",
        headers=owner_headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["default_price_tier_id"] == price_tier_id
    assert fetched.json()["default_price_tier_code"] == "WHOLESALE"

    cleared = client.patch(
        f"/v1/tenants/{tenant_id}/customer-profiles/{profile_id}",
        headers=owner_headers,
        json={"default_price_tier_id": None},
    )
    assert cleared.status_code == 200
    assert cleared.json()["default_price_tier_id"] is None
    assert cleared.json()["default_price_tier_code"] is None
    assert cleared.json()["default_price_tier_display_name"] is None
