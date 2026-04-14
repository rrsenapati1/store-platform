from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def test_runtime_print_queue_flows_through_device_polling() -> None:
    database_url = sqlite_test_database_url("runtime-print")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-runtime-print"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "8901234567890",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "selling_price": 92.5,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    branch_catalog_item = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        json={"product_id": product_id, "selling_price_override": None, "availability_status": "ACTIVE"},
    )
    assert branch_catalog_item.status_code == 200

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 24, "unit_cost": 61.5}],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Need replenishment before the weekend rush"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for branch restock"},
    )
    assert approved.status_code == 200

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "counter-1",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": None,
        },
    )
    assert device.status_code == 200
    device_id = device.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    runtime_devices = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices",
        headers=cashier_headers,
    )
    assert runtime_devices.status_code == 200
    assert runtime_devices.json()["records"][0]["id"] == device_id

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200
    sale_id = sale.json()["id"]

    invoice_print_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sales/{sale_id}",
        headers=cashier_headers,
        json={"device_id": device_id, "copies": 1},
    )
    assert invoice_print_job.status_code == 200
    assert invoice_print_job.json()["job_type"] == "SALES_INVOICE"
    assert invoice_print_job.json()["status"] == "QUEUED"
    assert invoice_print_job.json()["payload"]["receipt_lines"][0] == "STORE TAX INVOICE"

    sale_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns",
        headers=cashier_headers,
        json={
            "refund_amount": 97.12,
            "refund_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale_return.status_code == 200
    sale_return_id = sale_return.json()["id"]

    credit_note_print_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sale-returns/{sale_return_id}",
        headers=cashier_headers,
        json={"device_id": device_id, "copies": 1},
    )
    assert credit_note_print_job.status_code == 200
    assert credit_note_print_job.json()["job_type"] == "CREDIT_NOTE"
    assert credit_note_print_job.json()["payload"]["receipt_lines"][0] == "STORE CREDIT NOTE"

    heartbeat = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/heartbeat",
        headers=cashier_headers,
    )
    assert heartbeat.status_code == 200
    assert heartbeat.json()["queued_job_count"] == 2

    queued_jobs = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs",
        headers=cashier_headers,
    )
    assert queued_jobs.status_code == 200
    assert [record["id"] for record in queued_jobs.json()["records"]] == [
        invoice_print_job.json()["id"],
        credit_note_print_job.json()["id"],
    ]

    completed_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs/{invoice_print_job.json()['id']}/complete",
        headers=cashier_headers,
        json={"status": "COMPLETED"},
    )
    assert completed_job.status_code == 200
    assert completed_job.json()["status"] == "COMPLETED"

    failed_job = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs/{credit_note_print_job.json()['id']}/complete",
        headers=cashier_headers,
        json={"status": "FAILED", "failure_reason": "Paper jam"},
    )
    assert failed_job.status_code == 200
    assert failed_job.json()["status"] == "FAILED"
    assert failed_job.json()["failure_reason"] == "Paper jam"

    queued_after_completion = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs",
        headers=cashier_headers,
    )
    assert queued_after_completion.status_code == 200
    assert queued_after_completion.json()["records"] == []
