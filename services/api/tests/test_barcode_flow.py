from fastapi.testclient import TestClient

from store_api.main import create_app


def test_barcode_allocation_lookup_and_label_preview_use_branch_pricing():
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

    allocation = client.post(
        f"/v1/tenants/{tenant_id}/barcode-allocations",
        headers={"x-actor-role": "catalog_admin"},
        json={"sku_code": "SKU-001"},
    )

    assert allocation.status_code == 200
    assert allocation.json() == {"barcode": "ACMESKU001", "source": "ALLOCATED"}

    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": allocation.json()["barcode"],
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
            "lines": [{"product_id": product["id"], "quantity": 6, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for barcode stock"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for receiving"},
    )
    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )
    assert goods_receipt.status_code == 200

    lookup = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/barcode-lookup/{allocation.json()['barcode']}",
        headers={"x-actor-role": "cashier"},
    )

    assert lookup.status_code == 200
    assert lookup.json() == {
        "product_id": product["id"],
        "product_name": "Notebook",
        "sku_code": "SKU-001",
        "barcode": "ACMESKU001",
        "selling_price": 112.0,
        "stock_on_hand": 6.0,
        "is_active": True,
    }

    labels = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/barcode-labels",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": product["id"], "copies": 2},
    )

    assert labels.status_code == 200
    assert labels.json() == {
        "product_id": product["id"],
        "copies": 2,
        "labels": [
            {
                "sku_code": "SKU-001",
                "product_name": "Notebook",
                "barcode": "ACMESKU001",
                "price_label": "Rs. 112.00",
            },
            {
                "sku_code": "SKU-001",
                "product_name": "Notebook",
                "barcode": "ACMESKU001",
                "price_label": "Rs. 112.00",
            },
        ],
    }
