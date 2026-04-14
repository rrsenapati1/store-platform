from fastapi.testclient import TestClient

from store_api.main import create_app


def test_catalog_visibility_and_inventory_snapshot_flow():
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
            "name": "Pen",
            "sku_code": "SKU-002",
            "barcode": "8901234567001",
            "selling_price": 20,
            "tax_rate_percent": 18,
            "hsn_sac_code": "9608",
        },
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-overrides",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": notebook["id"], "selling_price": 112, "is_active": True},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-overrides",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": pen["id"], "is_active": False},
    )

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co"},
    ).json()

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": notebook["id"], "quantity": 6, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for branch stock"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for branch stock"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": notebook["id"], "quantity": 2}],
            "payment_amount": 264.32,
        },
    )

    central_catalog = client.get(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
    )

    assert central_catalog.status_code == 200
    assert central_catalog.json()["records"] == [
        {
            "product_id": notebook["id"],
            "product_name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "selling_price": 100.0,
            "tax_rate_percent": 18.0,
            "hsn_sac_code": "4820",
        },
        {
            "product_id": pen["id"],
            "product_name": "Pen",
            "sku_code": "SKU-002",
            "barcode": "8901234567001",
            "selling_price": 20.0,
            "tax_rate_percent": 18.0,
            "hsn_sac_code": "9608",
        },
    ]

    branch_catalog = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog",
        headers={"x-actor-role": "cashier"},
    )

    assert branch_catalog.status_code == 200
    assert branch_catalog.json()["records"] == [
        {
            "product_id": notebook["id"],
            "product_name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "hsn_sac_code": "4820",
            "selling_price": 112.0,
            "stock_on_hand": 4.0,
            "is_active": True,
            "price_source": "OVERRIDE",
            "availability_status": "LOW_STOCK",
        },
        {
            "product_id": pen["id"],
            "product_name": "Pen",
            "sku_code": "SKU-002",
            "barcode": "8901234567001",
            "hsn_sac_code": "9608",
            "selling_price": 20.0,
            "stock_on_hand": 0.0,
            "is_active": False,
            "price_source": "MASTER",
            "availability_status": "INACTIVE",
        },
    ]

    inventory_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json() == {
        "branch_id": branch_id,
        "sku_count": 2,
        "low_stock_count": 1,
        "out_of_stock_count": 0,
        "inactive_count": 1,
        "records": [
            {
                "product_id": notebook["id"],
                "product_name": "Notebook",
                "stock_on_hand": 4.0,
                "availability_status": "LOW_STOCK",
            },
            {
                "product_id": pen["id"],
                "product_name": "Pen",
                "stock_on_hand": 0.0,
                "availability_status": "INACTIVE",
            },
        ],
    }
