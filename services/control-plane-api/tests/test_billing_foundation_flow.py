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


def test_cashier_creates_gst_invoice_and_posts_sale_ledger():
    database_url = sqlite_test_database_url("billing-foundation")
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

    branch_catalog_item = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        json={"product_id": product_id, "selling_price_override": None, "availability_status": "ACTIVE"},
    )
    assert branch_catalog_item.status_code == 200

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
            "lines": [{"product_id": product_id, "quantity": 24, "unit_cost": 61.5}],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

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

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["invoice_number"] == "SINV-BLRFLAGSHIP-0001"
    assert sale.json()["invoice_kind"] == "B2B"
    assert sale.json()["irn_status"] == "IRN_PENDING"
    assert sale.json()["subtotal"] == 370.0
    assert sale.json()["cgst_total"] == 9.25
    assert sale.json()["sgst_total"] == 9.25
    assert sale.json()["igst_total"] == 0.0
    assert sale.json()["grand_total"] == 388.5
    assert [tax_line["tax_type"] for tax_line in sale.json()["tax_lines"]] == ["CGST", "SGST"]

    sales_register = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"][0]["invoice_number"] == "SINV-BLRFLAGSHIP-0001"
    assert sales_register.json()["records"][0]["payment_method"] == "UPI"
    assert sales_register.json()["records"][0]["grand_total"] == 388.5

    inventory_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 20.0

    inventory_ledger = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger",
        headers=owner_headers,
    )
    assert inventory_ledger.status_code == 200
    assert [record["entry_type"] for record in inventory_ledger.json()["records"]] == [
        "PURCHASE_RECEIPT",
        "SALE",
    ]
