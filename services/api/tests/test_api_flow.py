from fastapi.testclient import TestClient

from store_api.main import create_app


def test_wave_one_operational_flow():
    client = TestClient(create_app())

    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()
    tenant_id = tenant["id"]

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Bengaluru Flagship", "gstin": "29ABCDE1234F1Z5"},
    ).json()
    branch_id = branch["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "selling_price": 100,
            "tax_rate_percent": 18,
            "hsn_sac_code": "4820",
        },
    ).json()

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co", "gstin": "29AAAAA1111A1Z5"},
    ).json()

    po = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": 10, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{po['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for receipt"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{po['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for receipt"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": po["id"]},
    )

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29BBBBB2222B1Z5",
            "lines": [{"product_id": product["id"], "quantity": 2}],
            "payment_amount": 236,
        },
    ).json()

    export_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports",
        headers={"x-actor-role": "finance_admin"},
        json={"invoice_id": sale["invoice"]["id"]},
    ).json()

    assert export_job["status"] == "IRN_PENDING"

    irn = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports/{export_job['id']}/attach-irn",
        headers={"x-actor-role": "finance_admin"},
        json={"irn": "7d07f5f1", "ack_no": "12345", "signed_qr_payload": "qr-payload"},
    ).json()

    assert irn["irn"] == "7d07f5f1"

    returned = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale['sale_id']}/returns",
        headers={"x-actor-role": "store_manager"},
        json={"lines": [{"product_id": product["id"], "quantity": 1}], "refund_amount": 118},
    ).json()

    assert returned["stock_after_return"] == 9


def test_branch_catalog_override_changes_sale_pricing():
    client = TestClient(create_app())

    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()
    tenant_id = tenant["id"]

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Mysuru Branch", "gstin": "29ABCDE1234F1Z5"},
    ).json()
    branch_id = branch["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "selling_price": 100,
            "tax_rate_percent": 18,
            "hsn_sac_code": "4820",
        },
    ).json()

    override = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-overrides",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": product["id"], "selling_price": 112, "is_active": True},
    )

    assert override.status_code == 200

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": product["id"], "quantity": 2}],
            "payment_amount": 264.32,
        },
    ).json()

    assert sale["invoice"]["lines"][0]["unit_price"] == 112
    assert sale["invoice"]["grand_total"] == 264.32


def test_transfer_and_stock_count_reconcile_branch_inventory():
    client = TestClient(create_app())

    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()
    tenant_id = tenant["id"]

    source_branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Warehouse", "gstin": "29ABCDE1234F1Z5"},
    ).json()
    destination_branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Indiranagar", "gstin": "29ABCDE1234F1Z5"},
    ).json()

    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "selling_price": 100,
            "tax_rate_percent": 18,
            "hsn_sac_code": "4820",
        },
    ).json()

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co"},
    ).json()

    po = client.post(
        f"/v1/tenants/{tenant_id}/branches/{source_branch['id']}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": 10, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{source_branch['id']}/purchase-orders/{po['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Warehouse restock ready"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{source_branch['id']}/purchase-orders/{po['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approve inbound stock"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{source_branch['id']}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": po["id"]},
    )

    transfer = client.post(
        f"/v1/tenants/{tenant_id}/transfers",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "source_branch_id": source_branch["id"],
            "destination_branch_id": destination_branch["id"],
            "lines": [{"product_id": product["id"], "quantity": 4}],
        },
    )

    assert transfer.status_code == 200
    assert transfer.json()["lines"][0]["source_stock_after"] == 6
    assert transfer.json()["lines"][0]["destination_stock_after"] == 4

    stock_count = client.post(
        f"/v1/tenants/{tenant_id}/branches/{destination_branch['id']}/stock-counts",
        headers={"x-actor-role": "stock_clerk"},
        json={
            "reason": "Cycle count",
            "lines": [{"product_id": product["id"], "counted_quantity": 3}],
        },
    )

    assert stock_count.status_code == 200
    assert stock_count.json()["lines"][0] == {
        "product_id": product["id"],
        "expected_quantity": 4,
        "counted_quantity": 3,
        "variance_quantity": -1,
        "closing_stock": 3,
    }


def test_customer_dashboard_and_audit_log_flow():
    client = TestClient(create_app())

    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()
    tenant_id = tenant["id"]

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Bengaluru Flagship", "gstin": "29ABCDE1234F1Z5"},
    ).json()
    branch_id = branch["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "selling_price": 100,
            "tax_rate_percent": 18,
            "hsn_sac_code": "4820",
        },
    ).json()

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co"},
    ).json()

    po = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": 6, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{po['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for dashboard flow"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{po['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for stock intake"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": po["id"]},
    )

    customer = client.post(
        f"/v1/tenants/{tenant_id}/customers",
        headers={"x-actor-role": "cashier"},
        json={
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
        },
    )

    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_id": customer_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29BBBBB2222B1Z5",
            "lines": [{"product_id": product["id"], "quantity": 2}],
            "payment_amount": 236,
        },
    )

    assert sale.status_code == 200

    customer_summary = client.get(
        f"/v1/tenants/{tenant_id}/customers/{customer_id}",
        headers={"x-actor-role": "cashier"},
    )
    dashboard = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/dashboard",
        headers={"x-actor-role": "tenant_owner"},
    )
    audit_log = client.get(
        f"/v1/tenants/{tenant_id}/audit-logs",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert customer_summary.status_code == 200
    assert customer_summary.json()["visit_count"] == 1
    assert customer_summary.json()["lifetime_value"] == 236
    assert customer_summary.json()["last_sale_id"] == sale.json()["sale_id"]

    assert dashboard.status_code == 200
    assert dashboard.json() == {
        "branch_id": branch_id,
        "sales_count": 1,
        "gross_sales_total": 236,
        "pending_irn_invoices": 1,
        "customer_count": 1,
        "low_stock_products": [
            {
                "product_id": product["id"],
                "product_name": "Notebook",
                "stock_on_hand": 4,
            }
        ],
    }

    assert audit_log.status_code == 200
    actions = [entry["action"] for entry in audit_log.json()["records"]]
    assert "customer.created" in actions
    assert "sale.created" in actions
