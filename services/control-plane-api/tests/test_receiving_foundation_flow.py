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


def test_owner_receives_approved_purchase_order_into_inventory_ledger():
    database_url = sqlite_test_database_url("receiving-foundation")
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

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [
                {
                    "product_id": product_id,
                    "quantity": 24,
                    "unit_cost": 61.5,
                }
            ],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    approve = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for branch restock"},
    )
    assert approve.status_code == 400

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Need replenishment before the weekend rush"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for branch restock"},
    )
    assert approved.status_code == 200

    receiving_before = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/receiving-board",
        headers=owner_headers,
    )
    assert receiving_before.status_code == 200
    assert receiving_before.json()["ready_count"] == 1

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200
    goods_receipt_id = goods_receipt.json()["id"]
    assert goods_receipt.json()["goods_receipt_number"] == "GRN-BLRFLAGSHIP-0001"

    duplicate_goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert duplicate_goods_receipt.status_code == 400

    goods_receipts = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
    )
    assert goods_receipts.status_code == 200
    assert goods_receipts.json()["records"][0]["goods_receipt_id"] == goods_receipt_id

    receiving_after = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/receiving-board",
        headers=owner_headers,
    )
    assert receiving_after.status_code == 200
    assert receiving_after.json()["received_count"] == 1
    assert receiving_after.json()["records"][0]["receiving_status"] == "RECEIVED"

    inventory_ledger = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger",
        headers=owner_headers,
    )
    assert inventory_ledger.status_code == 200
    assert inventory_ledger.json()["records"][0]["entry_type"] == "PURCHASE_RECEIPT"
    assert inventory_ledger.json()["records"][0]["quantity"] == 24.0

    inventory_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["product_id"] == product_id
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 24.0
