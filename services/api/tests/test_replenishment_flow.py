from fastapi.testclient import TestClient

from store_api.main import create_app


def test_reorder_rules_drive_branch_replenishment_report():
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

    notebook = client.post(
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
    pen = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Pen Pack",
            "sku_code": "SKU-002",
            "barcode": "8901234567891",
            "selling_price": 50,
            "tax_rate_percent": 18,
            "hsn_sac_code": "9608",
        },
    ).json()

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co", "gstin": "29AAAAA1111A1Z5"},
    ).json()

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [
                {"product_id": notebook["id"], "quantity": 6, "unit_cost": 50},
                {"product_id": pen["id"], "quantity": 4, "unit_cost": 20},
            ],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for replenishment baseline"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for replenishment baseline"},
    )

    receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )
    assert receipt.status_code == 200

    notebook_rule = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/reorder-rules",
        headers={"x-actor-role": "inventory_admin"},
        json={"product_id": notebook["id"], "min_stock": 5, "target_stock": 12},
    )
    pen_rule = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/reorder-rules",
        headers={"x-actor-role": "inventory_admin"},
        json={"product_id": pen["id"], "min_stock": 2, "target_stock": 8},
    )

    assert notebook_rule.status_code == 200
    assert pen_rule.status_code == 200

    sale_one = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": notebook["id"], "quantity": 3}],
            "payment_amount": 354,
        },
    )
    sale_two = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": pen["id"], "quantity": 2}],
            "payment_amount": 118,
        },
    )

    assert sale_one.status_code == 200
    assert sale_two.status_code == 200

    report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/replenishment-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": branch_id,
        "rule_count": 2,
        "reorder_now_count": 1,
        "watch_count": 1,
        "records": [
            {
                "product_id": notebook["id"],
                "product_name": "Notebook",
                "stock_on_hand": 3.0,
                "min_stock": 5.0,
                "target_stock": 12.0,
                "reorder_quantity": 9.0,
                "status": "REORDER_NOW",
            },
            {
                "product_id": pen["id"],
                "product_name": "Pen Pack",
                "stock_on_hand": 2.0,
                "min_stock": 2.0,
                "target_stock": 8.0,
                "reorder_quantity": 6.0,
                "status": "WATCH",
            },
        ],
    }
