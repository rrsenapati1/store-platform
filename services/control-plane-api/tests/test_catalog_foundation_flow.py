from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def test_owner_bootstraps_catalog_and_branch_assignments():
    database_url = sqlite_test_database_url("catalog-foundation")
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
        json={"name": "Acme Retail", "slug": "acme-retail"},
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

    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "8901234567890",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "selling_price": 92.5,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    products = client.get(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
    )
    assert products.status_code == 200
    assert products.json()["records"][0]["sku_code"] == "tea-classic-250g"

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
    assert branch_catalog_item.json()["effective_selling_price"] == 89.0

    branch_catalog = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
    )
    assert branch_catalog.status_code == 200
    assert branch_catalog.json()["records"][0]["product_name"] == "Classic Tea"
    assert branch_catalog.json()["records"][0]["barcode"] == "8901234567890"
    assert branch_catalog.json()["records"][0]["effective_selling_price"] == 89.0
