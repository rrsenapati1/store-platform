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


def _create_owner_context(*, slug: str) -> tuple[TestClient, str, dict[str, str], str]:
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

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    return client, tenant_id, owner_headers, branch_id


def test_price_tiers_can_be_created_updated_and_listed() -> None:
    client, tenant_id, owner_headers, _ = _create_owner_context(slug="price-tier-flow")

    created = client.post(
        f"/v1/tenants/{tenant_id}/price-tiers",
        headers=owner_headers,
        json={"code": "VIP", "display_name": "VIP Price", "status": "ACTIVE"},
    )
    assert created.status_code == 200
    price_tier_id = created.json()["id"]
    assert created.json()["code"] == "VIP"
    assert created.json()["display_name"] == "VIP Price"
    assert created.json()["status"] == "ACTIVE"

    updated = client.patch(
        f"/v1/tenants/{tenant_id}/price-tiers/{price_tier_id}",
        headers=owner_headers,
        json={"display_name": "VIP Tier", "status": "DISABLED"},
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "VIP Tier"
    assert updated.json()["status"] == "DISABLED"

    listed = client.get(f"/v1/tenants/{tenant_id}/price-tiers", headers=owner_headers)
    assert listed.status_code == 200
    assert listed.json()["records"] == [
        {
            "id": price_tier_id,
            "tenant_id": tenant_id,
            "code": "VIP",
            "display_name": "VIP Tier",
            "status": "DISABLED",
            "created_at": updated.json()["created_at"],
            "updated_at": updated.json()["updated_at"],
        }
    ]


def test_branch_price_tier_prices_can_be_upserted_and_listed() -> None:
    client, tenant_id, owner_headers, branch_id = _create_owner_context(slug="branch-price-tier-prices")

    price_tier = client.post(
        f"/v1/tenants/{tenant_id}/price-tiers",
        headers=owner_headers,
        json={"code": "VIP", "display_name": "VIP Price", "status": "ACTIVE"},
    )
    assert price_tier.status_code == 200
    price_tier_id = price_tier.json()["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "8901234567890",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "mrp": 120.0,
            "category_code": "TEA",
            "selling_price": 92.5,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    branch_catalog_item = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        json={
            "product_id": product_id,
            "selling_price_override": 89.0,
            "availability_status": "ACTIVE",
        },
    )
    assert branch_catalog_item.status_code == 200

    upserted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/price-tier-prices",
        headers=owner_headers,
        json={"product_id": product_id, "price_tier_id": price_tier_id, "selling_price": 84.0},
    )
    assert upserted.status_code == 200
    assert upserted.json()["price_tier_code"] == "VIP"
    assert upserted.json()["product_name"] == "Classic Tea"
    assert upserted.json()["base_selling_price"] == 92.5
    assert upserted.json()["effective_base_selling_price"] == 89.0
    assert upserted.json()["selling_price"] == 84.0

    listed = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/price-tier-prices",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["records"] == [
        {
            "id": upserted.json()["id"],
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "product_id": product_id,
            "product_name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "price_tier_id": price_tier_id,
            "price_tier_code": "VIP",
            "price_tier_display_name": "VIP Price",
            "base_selling_price": 92.5,
            "effective_base_selling_price": 89.0,
            "selling_price": 84.0,
            "created_at": upserted.json()["created_at"],
            "updated_at": upserted.json()["updated_at"],
        }
    ]
