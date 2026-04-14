from fastapi.testclient import TestClient

from store_api.main import create_app


def test_invoice_and_barcode_print_jobs_flow_through_device_queue():
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

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers={"x-actor-role": "store_manager"},
        json={"device_name": "Counter Desktop 1", "session_surface": "store_desktop"},
    ).json()

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

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-overrides",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": product["id"], "selling_price": 112, "is_active": True},
    )

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
        json={"note": "Ready for print flow receipt"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for print flow receipt"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29BBBBB2222B1Z5",
            "lines": [{"product_id": product["id"], "quantity": 2}],
            "payment_amount": 264.32,
        },
    ).json()

    invoice_print_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/print-jobs/invoices",
        headers={"x-actor-role": "cashier"},
        json={"invoice_id": sale["invoice"]["id"], "device_id": device["id"], "copies": 1},
    )

    assert invoice_print_job.status_code == 200
    assert invoice_print_job.json()["job_type"] == "SALES_INVOICE"
    assert invoice_print_job.json()["status"] == "QUEUED"
    assert invoice_print_job.json()["payload"]["receipt_lines"][0] == "STORE TAX INVOICE"

    queued_invoice_jobs = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device['id']}/print-jobs",
        headers={"x-actor-role": "cashier"},
    )

    assert queued_invoice_jobs.status_code == 200
    assert [record["id"] for record in queued_invoice_jobs.json()["records"]] == [invoice_print_job.json()["id"]]

    completion = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device['id']}/print-jobs/{invoice_print_job.json()['id']}/complete",
        headers={"x-actor-role": "cashier"},
        json={"status": "COMPLETED"},
    )

    assert completion.status_code == 200
    assert completion.json()["status"] == "COMPLETED"

    barcode_print_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/print-jobs/barcode-labels",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": product["id"], "device_id": device["id"], "copies": 2},
    )

    assert barcode_print_job.status_code == 200
    assert barcode_print_job.json()["job_type"] == "BARCODE_LABEL"
    assert barcode_print_job.json()["payload"]["labels"] == [
        {
            "sku_code": "SKU-001",
            "product_name": "Notebook",
            "barcode": "8901234567890",
            "price_label": "Rs. 112.00",
        },
        {
            "sku_code": "SKU-001",
            "product_name": "Notebook",
            "barcode": "8901234567890",
            "price_label": "Rs. 112.00",
        },
    ]

    queued_label_jobs = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device['id']}/print-jobs",
        headers={"x-actor-role": "cashier"},
    )

    assert queued_label_jobs.status_code == 200
    assert [record["id"] for record in queued_label_jobs.json()["records"]] == [barcode_print_job.json()["id"]]
