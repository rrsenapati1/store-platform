from datetime import date, timedelta

from fastapi.testclient import TestClient

from store_api.main import create_app


def test_batch_lots_expiry_report_and_write_off_flow():
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

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": 10, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for lot intake"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for lot intake"},
    )

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    ).json()

    soon_expiry = (date.today() + timedelta(days=7)).isoformat()
    fresh_expiry = (date.today() + timedelta(days=90)).isoformat()

    batch_lots = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt['id']}/batch-lots",
        headers={"x-actor-role": "stock_clerk"},
        json={
            "lots": [
                {"product_id": product["id"], "batch_number": "BATCH-A", "quantity": 6, "expiry_date": soon_expiry},
                {"product_id": product["id"], "batch_number": "BATCH-B", "quantity": 4, "expiry_date": fresh_expiry},
            ]
        },
    )

    assert batch_lots.status_code == 200
    assert [record["batch_number"] for record in batch_lots.json()["records"]] == ["BATCH-A", "BATCH-B"]

    initial_report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert initial_report.status_code == 200
    assert initial_report.json()["tracked_lot_count"] == 2
    assert initial_report.json()["expiring_soon_count"] == 1
    assert initial_report.json()["untracked_stock_quantity"] == 0.0

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": product["id"], "quantity": 5}],
            "payment_amount": 590,
        },
    )

    report_after_sale = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report_after_sale.status_code == 200
    assert report_after_sale.json()["records"][0]["batch_number"] == "BATCH-A"
    assert report_after_sale.json()["records"][0]["remaining_quantity"] == 1.0
    assert report_after_sale.json()["records"][1]["remaining_quantity"] == 4.0

    write_off = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-lots/{batch_lots.json()['records'][0]['id']}/expiry-write-offs",
        headers={"x-actor-role": "stock_clerk"},
        json={"quantity": 1, "reason": "Expired on shelf"},
    )

    assert write_off.status_code == 200
    assert write_off.json()["written_off_quantity"] == 1.0
    assert write_off.json()["remaining_quantity"] == 0.0

    report_after_write_off = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report_after_write_off.status_code == 200
    assert report_after_write_off.json()["tracked_lot_count"] == 1
    assert report_after_write_off.json()["records"] == [
        {
            "batch_lot_id": batch_lots.json()["records"][1]["id"],
            "product_id": product["id"],
            "product_name": "Notebook",
            "batch_number": "BATCH-B",
            "expiry_date": fresh_expiry,
            "days_to_expiry": 90,
            "received_quantity": 4.0,
            "written_off_quantity": 0.0,
            "remaining_quantity": 4.0,
            "status": "FRESH",
        }
    ]
