from fastapi.testclient import TestClient

from store_api.main import create_app


def _seed_tenant_with_branch_activity(client: TestClient) -> dict[str, str]:
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
            "lines": [{"product_id": product["id"], "quantity": 6, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for seeded receipt"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for seeded receipt"},
    )

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers={"x-actor-role": "inventory_admin"},
        json={"goods_receipt_id": goods_receipt["id"]},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": product["id"], "quantity": 2}],
            "payment_amount": 236,
        },
    )

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "product_id": product["id"],
    }


def test_platform_admin_can_list_tenants_and_open_support_session():
    client = TestClient(create_app())
    context = _seed_tenant_with_branch_activity(client)

    listed = client.get(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
    )

    assert listed.status_code == 200
    assert listed.json()["records"] == [
        {
            "tenant_id": context["tenant_id"],
            "tenant_name": "Acme Retail",
            "status": "ACTIVE",
            "branch_count": 1,
            "sales_invoice_total": 236,
            "purchase_invoice_total": 354,
        }
    ]

    overview = client.get(
        f"/v1/platform/tenants/{context['tenant_id']}/overview",
        headers={"x-actor-role": "platform_super_admin"},
    )

    assert overview.status_code == 200
    assert overview.json()["tenant"] == {
        "tenant_id": context["tenant_id"],
        "tenant_name": "Acme Retail",
        "status": "ACTIVE",
        "suspension_reason": None,
    }
    assert overview.json()["branches"] == [
        {
            "branch_id": context["branch_id"],
            "branch_name": "Bengaluru Flagship",
            "sales_invoice_total": 236,
            "purchase_invoice_total": 354,
            "pending_irn_invoices": 0,
        }
    ]

    support_session = client.post(
        "/v1/platform/support-sessions",
        headers={"x-actor-role": "platform_super_admin"},
        json={"tenant_id": context["tenant_id"], "branch_ids": [context["branch_id"]]},
    )

    assert support_session.status_code == 200
    assert support_session.json()["access_mode"] == "READ_ONLY"
    assert support_session.json()["tenant_id"] == context["tenant_id"]
    assert support_session.json()["branch_ids"] == [context["branch_id"]]


def test_suspended_tenant_blocks_store_operations_until_reactivated():
    client = TestClient(create_app())
    context = _seed_tenant_with_branch_activity(client)

    suspended = client.post(
        f"/v1/platform/tenants/{context['tenant_id']}/status",
        headers={"x-actor-role": "platform_super_admin"},
        json={"status": "SUSPENDED", "reason": "Chargeback review"},
    )

    assert suspended.status_code == 200
    assert suspended.json()["status"] == "SUSPENDED"
    assert suspended.json()["suspension_reason"] == "Chargeback review"

    blocked_sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["product_id"], "quantity": 1}],
            "payment_amount": 118,
        },
    )

    assert blocked_sale.status_code == 423
    assert blocked_sale.json()["detail"] == "Tenant is suspended"

    reactivated = client.post(
        f"/v1/platform/tenants/{context['tenant_id']}/status",
        headers={"x-actor-role": "platform_super_admin"},
        json={"status": "ACTIVE"},
    )

    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"
    assert reactivated.json()["suspension_reason"] is None

    resumed_sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["product_id"], "quantity": 1}],
            "payment_amount": 118,
        },
    )

    assert resumed_sale.status_code == 200
