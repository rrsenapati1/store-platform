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


def test_promotion_campaign_can_be_created_updated_and_listed() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-campaign-create")

    created = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Diwali Welcome",
            "status": "ACTIVE",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "minimum_order_amount": 100.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": 500,
        },
    )
    assert created.status_code == 200
    campaign_id = created.json()["id"]
    assert created.json()["name"] == "Diwali Welcome"
    assert created.json()["discount_type"] == "FLAT_AMOUNT"
    assert created.json()["discount_value"] == 20.0
    assert created.json()["status"] == "ACTIVE"

    updated = client.patch(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}",
        headers=owner_headers,
        json={
            "name": "Diwali Welcome Updated",
            "minimum_order_amount": 150.0,
            "redemption_limit_total": 750,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Diwali Welcome Updated"
    assert updated.json()["minimum_order_amount"] == 150.0
    assert updated.json()["redemption_limit_total"] == 750

    listed = client.get(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert [record["id"] for record in listed.json()["records"]] == [campaign_id]
    assert listed.json()["records"][0]["name"] == "Diwali Welcome Updated"


def test_shared_promotion_codes_track_duplicates_and_campaign_status() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-code-duplicate")

    campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Weekend Percentage",
            "status": "ACTIVE",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": 200.0,
            "maximum_discount_amount": 40.0,
            "redemption_limit_total": None,
        },
    )
    assert campaign.status_code == 200
    campaign_id = campaign.json()["id"]

    code = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={
            "code": "WEEKEND10",
            "status": "ACTIVE",
            "redemption_limit_per_code": 100,
        },
    )
    assert code.status_code == 200
    assert code.json()["code"] == "WEEKEND10"
    assert code.json()["redemption_limit_per_code"] == 100
    assert code.json()["redemption_count"] == 0

    duplicate = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={
            "code": "WEEKEND10",
            "status": "ACTIVE",
            "redemption_limit_per_code": None,
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Promotion code already exists"

    disabled = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/disable",
        headers=owner_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"

    reactivated = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/reactivate",
        headers=owner_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"
