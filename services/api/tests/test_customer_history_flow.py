from fastapi.testclient import TestClient

from store_api.main import create_app


def test_customer_search_and_history_flow():
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
        json={"note": "Ready for customer history stock"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for customer history stock"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )

    customer = client.post(
        f"/v1/tenants/{tenant_id}/customers",
        headers={"x-actor-role": "cashier"},
        json={
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
        },
    ).json()
    customer_id = customer["id"]

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
    ).json()

    sale_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale['sale_id']}/returns",
        headers={"x-actor-role": "store_manager"},
        json={"lines": [{"product_id": product["id"], "quantity": 1}], "refund_amount": 118},
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sale-returns/{sale_return['id']}/approve-refund",
        headers={"x-actor-role": "finance_admin"},
        json={"note": "Approved for loyal customer"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale['sale_id']}/exchanges",
        headers={"x-actor-role": "store_manager"},
        json={
            "return_lines": [{"product_id": product["id"], "quantity": 1}],
            "replacement_lines": [{"product_id": product["id"], "quantity": 1}],
        },
    )

    customer_search = client.get(
        f"/v1/tenants/{tenant_id}/customers",
        headers={"x-actor-role": "cashier"},
        params={"query": "3210"},
    )

    assert customer_search.status_code == 200
    assert customer_search.json()["records"] == [
        {
            "customer_id": customer_id,
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
            "visit_count": 1,
            "lifetime_value": 236.0,
            "last_sale_id": sale["sale_id"],
            "last_invoice_number": sale["invoice"]["invoice_number"],
            "last_branch_id": branch_id,
        }
    ]

    customer_history = client.get(
        f"/v1/tenants/{tenant_id}/customers/{customer_id}/history",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert customer_history.status_code == 200
    assert customer_history.json() == {
        "customer": {
            "customer_id": customer_id,
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
            "visit_count": 1,
            "lifetime_value": 236.0,
            "last_sale_id": sale["sale_id"],
        },
        "sales_summary": {
            "sales_count": 1,
            "sales_total": 236.0,
            "return_count": 1,
            "credit_note_total": 118.0,
            "exchange_count": 1,
        },
        "sales": [
            {
                "sale_id": sale["sale_id"],
                "branch_id": branch_id,
                "invoice_id": sale["invoice"]["id"],
                "invoice_number": sale["invoice"]["invoice_number"],
                "grand_total": 236.0,
                "payment_method": "cash",
            }
        ],
        "returns": [
            {
                "sale_return_id": sale_return["id"],
                "sale_id": sale["sale_id"],
                "branch_id": branch_id,
                "credit_note_id": sale_return["credit_note"]["id"],
                "credit_note_number": sale_return["credit_note"]["credit_note_number"],
                "grand_total": 118.0,
                "refund_amount": 118.0,
                "status": "REFUND_APPROVED",
            }
        ],
        "exchanges": [
            {
                "exchange_order_id": customer_history.json()["exchanges"][0]["exchange_order_id"],
                "sale_id": sale["sale_id"],
                "branch_id": branch_id,
                "return_total": 118.0,
                "replacement_total": 118.0,
                "balance_direction": "EVEN",
                "balance_amount": 0.0,
            }
        ],
    }
