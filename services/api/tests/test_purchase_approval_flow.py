from fastapi.testclient import TestClient

from store_api.main import create_app


def test_purchase_order_can_move_through_approval_queue_and_report_status():
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
    )

    assert purchase_order.status_code == 200
    assert purchase_order.json()["approval_status"] == "NOT_REQUESTED"

    requested = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order.json()['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Need before school rush"},
    )

    assert requested.status_code == 200
    assert requested.json()["approval_status"] == "PENDING_APPROVAL"
    assert requested.json()["approval_requested_note"] == "Need before school rush"

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order.json()['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for dispatch"},
    )

    assert approved.status_code == 200
    assert approved.json()["approval_status"] == "APPROVED"
    assert approved.json()["approval_decision_note"] == "Approved for dispatch"

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order.json()["id"]},
    )

    assert goods_receipt.status_code == 200

    rejected_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": 2, "unit_cost": 50}],
        },
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{rejected_purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Reserve order"},
    )
    rejected = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{rejected_purchase_order['id']}/reject",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Hold until next month"},
    )

    assert rejected.status_code == 200
    assert rejected.json()["approval_status"] == "REJECTED"

    report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-approval-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": branch_id,
        "not_requested_count": 0,
        "pending_approval_count": 0,
        "approved_count": 1,
        "rejected_count": 1,
        "received_count": 1,
        "records": [
            {
                "purchase_order_id": purchase_order.json()["id"],
                "supplier_name": "Paper Supply Co",
                "approval_status": "APPROVED",
                "line_count": 1,
                "ordered_quantity": 6.0,
                "receiving_status": "RECEIVED",
                "approval_requested_note": "Need before school rush",
                "approval_decision_note": "Approved for dispatch",
                "goods_receipt_id": goods_receipt.json()["id"],
            },
            {
                "purchase_order_id": rejected_purchase_order["id"],
                "supplier_name": "Paper Supply Co",
                "approval_status": "REJECTED",
                "line_count": 1,
                "ordered_quantity": 2.0,
                "receiving_status": "BLOCKED",
                "approval_requested_note": "Reserve order",
                "approval_decision_note": "Hold until next month",
                "goods_receipt_id": None,
            },
        ],
    }
