import asyncio

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.services.operations_worker import OperationsWorkerService
from store_control_plane.utils import utc_now


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _open_cashier_session(
    client: TestClient,
    *,
    tenant_id: str,
    branch_id: str,
    owner_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> str:
    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "cashier@acme.local",
            "full_name": "Counter Cashier",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    device_id = device.json()["id"]

    attendance_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "clock_in_note": "Morning shift attendance",
        },
    )
    assert attendance_session.status_code == 200

    cashier_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Morning shift",
        },
    )
    assert cashier_session.status_code == 200
    return cashier_session.json()["id"]


def _seed_sale_context(client: TestClient) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-async-compliance"},
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

    assert client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Need replenishment before the weekend rush"},
    ).status_code == 200
    assert client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for branch restock"},
    ).status_code == 200
    assert client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    ).status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
    cashier_session_id = _open_cashier_session(
        client,
        tenant_id=tenant_id,
        branch_id=branch_id,
        owner_headers=owner_headers,
        cashier_headers=cashier_headers,
    )

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "cashier_session_id": cashier_session_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "sale_id": sale.json()["id"],
        "owner_access_token": owner_session["access_token"],
    }


async def _run_worker_once(client: TestClient) -> dict[str, int]:
    async with client.app.state.session_factory() as session:
        worker_service = OperationsWorkerService(session, settings=client.app.state.settings)
        return await worker_service.process_due_jobs(limit=10, now=utc_now())


def test_gst_export_request_enqueues_async_preparation_and_worker_completes_it() -> None:
    database_url = sqlite_test_database_url("compliance-async-jobs")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
            compliance_secret_key="4YwWqS6E2m2Gf2m74tNw-KH6nB5c1ETb8T-WcC1wh6g=",
            compliance_irp_mode="stub",
        )
    )
    context = _seed_sale_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    profile = client.put(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/provider-profile",
        headers=owner_headers,
        json={
            "provider_name": "iris_direct",
            "api_username": "acme-irp-user",
            "api_password": "super-secret",
        },
    )
    assert profile.status_code == 200

    export_job = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/gst-exports",
        headers=owner_headers,
        json={"sale_id": context["sale_id"]},
    )
    assert export_job.status_code == 200
    assert export_job.json()["status"] == "QUEUED"

    duplicate = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/gst-exports",
        headers=owner_headers,
        json={"sale_id": context["sale_id"]},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == export_job.json()["id"]

    processed = asyncio.run(_run_worker_once(client))
    assert processed["completed"] == 1
    assert processed["dead_lettered"] == 0

    refreshed_report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/gst-exports",
        headers=owner_headers,
    )
    assert refreshed_report.status_code == 200
    assert refreshed_report.json()["records"][0]["status"] == "IRN_ATTACHED"
    assert refreshed_report.json()["records"][0]["provider_status"] == "SUBMITTED"
