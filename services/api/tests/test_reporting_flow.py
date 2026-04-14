from fastapi.testclient import TestClient

from store_api.main import create_app


def test_branch_commercial_report_rolls_up_sales_mix_products_and_stock_risk():
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
    eraser = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Eraser",
            "sku_code": "SKU-003",
            "barcode": "8901234567892",
            "selling_price": 10,
            "tax_rate_percent": 18,
            "hsn_sac_code": "4016",
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
                {"product_id": pen["id"], "quantity": 3, "unit_cost": 20},
                {"product_id": eraser["id"], "quantity": 1, "unit_cost": 5},
            ],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for reporting baseline"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for reporting baseline"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )

    sale_one = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": notebook["id"], "quantity": 2}],
            "payment_amount": 236,
            "payment_method": "cash",
        },
    )
    assert sale_one.status_code == 200

    sale_two = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [
                {"product_id": notebook["id"], "quantity": 1},
                {"product_id": pen["id"], "quantity": 2},
            ],
            "payment_amount": 236,
            "payment_method": "upi",
        },
    )
    assert sale_two.status_code == 200

    sale_three = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": eraser["id"], "quantity": 1}],
            "payment_amount": 11.8,
            "payment_method": "card",
        },
    )
    assert sale_three.status_code == 200

    sale_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_two.json()['sale_id']}/returns",
        headers={"x-actor-role": "cashier"},
        json={"lines": [{"product_id": pen["id"], "quantity": 1}], "refund_amount": 59},
    )
    assert sale_return.status_code == 200

    report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/commercial-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": branch_id,
        "sales_summary": {
            "sales_count": 3,
            "gross_sales_total": 483.8,
            "return_total": 59.0,
            "net_sales_total": 424.8,
            "average_basket_value": 161.27,
        },
        "payment_mix": [
            {"payment_method": "cash", "sales_count": 1, "gross_sales_total": 236.0},
            {"payment_method": "upi", "sales_count": 1, "gross_sales_total": 236.0},
            {"payment_method": "card", "sales_count": 1, "gross_sales_total": 11.8},
        ],
        "top_products": [
            {"product_id": notebook["id"], "product_name": "Notebook", "quantity_sold": 3.0, "sales_total": 300.0},
            {"product_id": pen["id"], "product_name": "Pen Pack", "quantity_sold": 2.0, "sales_total": 100.0},
            {"product_id": eraser["id"], "product_name": "Eraser", "quantity_sold": 1.0, "sales_total": 10.0},
        ],
        "stock_risk": {
            "low_stock_products": [
                {"product_id": notebook["id"], "product_name": "Notebook", "stock_on_hand": 3.0},
                {"product_id": pen["id"], "product_name": "Pen Pack", "stock_on_hand": 2.0},
            ],
            "out_of_stock_products": [
                {"product_id": eraser["id"], "product_name": "Eraser", "stock_on_hand": 0.0}
            ],
            "negative_stock_products": [],
        },
    }
