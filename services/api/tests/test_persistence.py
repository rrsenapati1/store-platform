from pathlib import Path

from fastapi.testclient import TestClient

from store_api.main import create_app


def _bootstrap_operational_state(state_file: Path) -> dict[str, str]:
    client = TestClient(create_app(state_file=state_file))

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
        json={"note": "Ready for persisted receipt"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for persisted receipt"},
    )

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    ).json()

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "product_id": product["id"],
        "goods_receipt_id": goods_receipt["id"],
    }


def test_restart_reloads_documents_for_follow_up_purchase_and_sales_flow(tmp_path: Path):
    state_file = tmp_path / "store-api-state.json"
    context = _bootstrap_operational_state(state_file)

    restarted_client = TestClient(create_app(state_file=state_file))

    purchase_invoice = restarted_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices",
        headers={"x-actor-role": "inventory_admin"},
        json={"goods_receipt_id": context["goods_receipt_id"]},
    )

    assert purchase_invoice.status_code == 200
    assert purchase_invoice.json()["invoice_number"] == "SPINV-2526-000001"

    sale = restarted_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["product_id"], "quantity": 2}],
            "payment_amount": 236,
        },
    )

    assert sale.status_code == 200
    assert sale.json()["invoice"]["invoice_number"] == "SINV-2526-000001"


def test_restart_preserves_invoice_sequence_progress(tmp_path: Path):
    state_file = tmp_path / "store-api-state.json"
    context = _bootstrap_operational_state(state_file)

    first_client = TestClient(create_app(state_file=state_file))
    first_sale = first_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["product_id"], "quantity": 1}],
            "payment_amount": 118,
        },
    )

    assert first_sale.status_code == 200
    assert first_sale.json()["invoice"]["invoice_number"] == "SINV-2526-000001"

    restarted_client = TestClient(create_app(state_file=state_file))
    second_sale = restarted_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["product_id"], "quantity": 1}],
            "payment_amount": 118,
        },
    )

    assert second_sale.status_code == 200
    assert second_sale.json()["invoice"]["invoice_number"] == "SINV-2526-000002"


def test_restart_preserves_queued_print_jobs(tmp_path: Path):
    state_file = tmp_path / "store-api-state.json"
    context = _bootstrap_operational_state(state_file)

    first_client = TestClient(create_app(state_file=state_file))
    device = first_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers={"x-actor-role": "store_manager"},
        json={"device_name": "Counter Desktop 1", "session_surface": "store_desktop"},
    ).json()

    sale = first_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["product_id"], "quantity": 1}],
            "payment_amount": 118,
        },
    ).json()

    print_job = first_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/print-jobs/invoices",
        headers={"x-actor-role": "cashier"},
        json={"invoice_id": sale["invoice"]["id"], "device_id": device["id"], "copies": 1},
    )

    assert print_job.status_code == 200

    restarted_client = TestClient(create_app(state_file=state_file))
    queued_jobs = restarted_client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices/{device['id']}/print-jobs",
        headers={"x-actor-role": "cashier"},
    )

    assert queued_jobs.status_code == 200
    assert [record["id"] for record in queued_jobs.json()["records"]] == [print_job.json()["id"]]


def test_restart_preserves_batch_lots_for_expiry_reporting(tmp_path: Path):
    state_file = tmp_path / "store-api-state.json"
    context = _bootstrap_operational_state(state_file)

    first_client = TestClient(create_app(state_file=state_file))
    batch_lots = first_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/goods-receipts/{context['goods_receipt_id']}/batch-lots",
        headers={"x-actor-role": "stock_clerk"},
        json={
            "lots": [
                {
                    "product_id": context["product_id"],
                    "batch_number": "BATCH-A",
                    "quantity": 6,
                    "expiry_date": "2099-01-01",
                }
            ]
        },
    )

    assert batch_lots.status_code == 200

    restarted_client = TestClient(create_app(state_file=state_file))
    report = restarted_client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/batch-expiry-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json()["records"][0]["batch_number"] == "BATCH-A"
