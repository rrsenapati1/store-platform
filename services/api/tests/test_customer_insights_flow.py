from fastapi.testclient import TestClient

from store_api.main import create_app


def test_branch_customer_report_flow():
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
        json={"note": "Ready for customer insights stock"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for customer insights stock"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )

    acme = client.post(
        f"/v1/tenants/{tenant_id}/customers",
        headers={"x-actor-role": "cashier"},
        json={"name": "Acme Traders", "phone": "9876543210", "gstin": "29BBBBB2222B1Z5"},
    ).json()
    beta = client.post(
        f"/v1/tenants/{tenant_id}/customers",
        headers={"x-actor-role": "cashier"},
        json={"name": "Beta Stores", "phone": "9876500000", "gstin": "29CCCCC3333C1Z5"},
    ).json()

    sale_one = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_id": acme["id"],
            "customer_name": "Acme Traders",
            "customer_gstin": "29BBBBB2222B1Z5",
            "lines": [{"product_id": product["id"], "quantity": 2}],
            "payment_amount": 236,
        },
    ).json()
    sale_two = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_id": acme["id"],
            "customer_name": "Acme Traders",
            "customer_gstin": "29BBBBB2222B1Z5",
            "lines": [{"product_id": product["id"], "quantity": 1}],
            "payment_amount": 118,
        },
    ).json()
    sale_three = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_id": beta["id"],
            "customer_name": "Beta Stores",
            "customer_gstin": "29CCCCC3333C1Z5",
            "lines": [{"product_id": product["id"], "quantity": 1}],
            "payment_amount": 118,
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": product["id"], "quantity": 1}],
            "payment_amount": 118,
        },
    )

    sale_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_one['sale_id']}/returns",
        headers={"x-actor-role": "store_manager"},
        json={"lines": [{"product_id": product["id"], "quantity": 1}], "refund_amount": 118},
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_two['sale_id']}/exchanges",
        headers={"x-actor-role": "store_manager"},
        json={
            "return_lines": [{"product_id": product["id"], "quantity": 1}],
            "replacement_lines": [{"product_id": product["id"], "quantity": 1}],
        },
    )

    report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/customer-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": branch_id,
        "customer_count": 2,
        "repeat_customer_count": 1,
        "anonymous_sales_count": 1,
        "anonymous_sales_total": 118.0,
        "top_customers": [
            {
                "customer_id": acme["id"],
                "customer_name": "Acme Traders",
                "sales_count": 2,
                "sales_total": 354.0,
                "last_invoice_number": sale_two["invoice"]["invoice_number"],
            },
            {
                "customer_id": beta["id"],
                "customer_name": "Beta Stores",
                "sales_count": 1,
                "sales_total": 118.0,
                "last_invoice_number": sale_three["invoice"]["invoice_number"],
            },
        ],
        "return_activity": [
            {
                "customer_id": acme["id"],
                "customer_name": "Acme Traders",
                "return_count": 1,
                "credit_note_total": sale_return["credit_note"]["grand_total"],
                "exchange_count": 1,
            }
        ],
    }
