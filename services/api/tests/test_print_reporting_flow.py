from fastapi.testclient import TestClient

from store_api.main import create_app


def test_branch_print_health_report_and_platform_exceptions_flow():
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

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29BBBBB2222B1Z5",
            "lines": [{"product_id": product["id"], "quantity": 1}],
            "payment_amount": 118,
        },
    ).json()

    invoice_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/print-jobs/invoices",
        headers={"x-actor-role": "cashier"},
        json={"invoice_id": sale["invoice"]["id"], "device_id": device["id"], "copies": 1},
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device['id']}/print-jobs/{invoice_job['id']}/complete",
        headers={"x-actor-role": "cashier"},
        json={"status": "COMPLETED"},
    )

    barcode_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/print-jobs/barcode-labels",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": product["id"], "device_id": device["id"], "copies": 1},
    ).json()

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device['id']}/print-jobs/{barcode_job['id']}/complete",
        headers={"x-actor-role": "cashier"},
        json={"status": "FAILED", "failure_reason": "Paper jam"},
    )

    branch_report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/print-health-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert branch_report.status_code == 200
    assert branch_report.json() == {
        "branch_id": branch_id,
        "device_count": 1,
        "queued_jobs": 0,
        "completed_jobs": 1,
        "failed_jobs": 1,
        "records": [
            {
                "device_id": device["id"],
                "device_name": "Counter Desktop 1",
                "session_surface": "store_desktop",
                "queued_jobs": 0,
                "completed_jobs": 1,
                "failed_jobs": 1,
                "latest_status": "FAILED",
                "last_failure_reason": "Paper jam",
                "success_rate": 50.0,
                "health_status": "ATTENTION",
            }
        ],
    }

    platform_report = client.get(
        "/v1/platform/print-exceptions",
        headers={"x-actor-role": "platform_super_admin"},
    )

    assert platform_report.status_code == 200
    assert platform_report.json() == {
        "failed_device_count": 1,
        "records": [
            {
                "tenant_id": tenant_id,
                "tenant_name": "Acme Retail",
                "branch_id": branch_id,
                "branch_name": "Bengaluru Flagship",
                "device_id": device["id"],
                "device_name": "Counter Desktop 1",
                "session_surface": "store_desktop",
                "queued_jobs": 0,
                "completed_jobs": 1,
                "failed_jobs": 1,
                "last_failure_reason": "Paper jam",
                "success_rate": 50.0,
            }
        ],
    }
