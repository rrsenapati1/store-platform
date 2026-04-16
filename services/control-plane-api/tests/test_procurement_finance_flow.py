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


def test_owner_runs_procurement_finance_flow_on_control_plane() -> None:
    database_url = sqlite_test_database_url("procurement-finance")
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
        json={"name": "Acme Retail", "slug": "acme-retail-payables"},
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
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "hsn_sac_code": "4820",
            "gst_rate": 18.0,
            "selling_price": 100.0,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": "Paper Supply Co", "gstin": "29AAAAA1111A1Z5", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 6, "unit_cost": 50}],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Ready for supplier settlement"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for supplier settlement"},
    )
    assert approved.status_code == 200

    purchase_order_detail = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}",
        headers=owner_headers,
    )
    assert purchase_order_detail.status_code == 200
    assert purchase_order_detail.json()["id"] == purchase_order_id
    assert purchase_order_detail.json()["purchase_order_number"].startswith("PO-")
    assert purchase_order_detail.json()["lines"] == [
        {
            "product_id": product_id,
            "product_name": "Notebook",
            "sku_code": "SKU-001",
            "quantity": 6.0,
            "unit_cost": 50.0,
            "line_total": 300.0,
        }
    ]

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200
    goods_receipt_id = goods_receipt.json()["id"]

    purchase_invoice = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers=owner_headers,
        json={"goods_receipt_id": goods_receipt_id},
    )
    assert purchase_invoice.status_code == 200
    purchase_invoice_id = purchase_invoice.json()["id"]
    assert purchase_invoice.json()["goods_receipt_id"] == goods_receipt_id
    assert purchase_invoice.json()["grand_total"] == 354.0

    duplicate_purchase_invoice = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers=owner_headers,
        json={"goods_receipt_id": goods_receipt_id},
    )
    assert duplicate_purchase_invoice.status_code == 400

    supplier_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-returns",
        headers=owner_headers,
        json={"lines": [{"product_id": product_id, "quantity": 1}]},
    )
    assert supplier_return.status_code == 200
    assert supplier_return.json()["purchase_invoice_id"] == purchase_invoice_id
    assert supplier_return.json()["grand_total"] == 59.0

    supplier_payment = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-payments",
        headers=owner_headers,
        json={"amount": 200.0, "payment_method": "bank_transfer", "reference": "UTR-001"},
    )
    assert supplier_payment.status_code == 200
    assert supplier_payment.json()["purchase_invoice_id"] == purchase_invoice_id
    assert supplier_payment.json()["amount"] == 200.0

    payables_report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payables-report",
        headers=owner_headers,
    )
    assert payables_report.status_code == 200
    assert payables_report.json()["invoiced_total"] == 354.0
    assert payables_report.json()["credit_note_total"] == 59.0
    assert payables_report.json()["paid_total"] == 200.0
    assert payables_report.json()["outstanding_total"] == 95.0
    assert payables_report.json()["records"][0]["purchase_invoice_id"] == purchase_invoice_id
    assert payables_report.json()["records"][0]["settlement_status"] == "PARTIALLY_SETTLED"

    inventory_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 5.0

    inventory_ledger = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger",
        headers=owner_headers,
    )
    assert inventory_ledger.status_code == 200
    assert [record["entry_type"] for record in inventory_ledger.json()["records"]] == [
        "PURCHASE_RECEIPT",
        "SUPPLIER_RETURN",
    ]
