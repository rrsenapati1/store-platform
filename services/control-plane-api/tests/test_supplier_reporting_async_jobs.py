import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.models import OperationsJob
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


def _bootstrap_owner_context(client: TestClient) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-supplier-async"},
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

    return {
        "tenant_id": tenant_id,
        "branch_id": branch.json()["id"],
        "owner_access_token": owner_session["access_token"],
    }


def _create_purchase_flow(
    client: TestClient,
    *,
    owner_headers: dict[str, str],
    tenant_id: str,
    branch_id: str,
) -> dict[str, str]:
    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "hsn_sac_code": "4820",
            "gst_rate": 18.0,
            "selling_price": 100,
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
        json={"name": "Paper Supply Co", "gstin": "29AAAAA1111A1Z5", "payment_terms_days": 30},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={"supplier_id": supplier_id, "lines": [{"product_id": product_id, "quantity": 6, "unit_cost": 50}]},
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    assert client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Ready for supplier reporting"},
    ).status_code == 200
    assert client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for supplier reporting"},
    ).status_code == 200

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200

    return {
        "supplier_id": supplier_id,
        "goods_receipt_id": goods_receipt.json()["id"],
    }


async def _run_worker_once(client: TestClient) -> dict[str, int]:
    async with client.app.state.session_factory() as session:
        worker_service = OperationsWorkerService(session)
        return await worker_service.process_due_jobs(limit=10, now=utc_now())


async def _list_operations_jobs(client: TestClient) -> list[OperationsJob]:
    async with client.app.state.session_factory() as session:
        result = await session.scalars(select(OperationsJob).order_by(OperationsJob.created_at.asc(), OperationsJob.id.asc()))
        return list(result.all())


def test_supplier_reporting_dirty_snapshot_queues_refresh_until_worker_rebuilds_it() -> None:
    database_url = sqlite_test_database_url("supplier-reporting-async-jobs")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )
    context = _bootstrap_owner_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}
    purchase_flow = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
    )
    as_of_date = str(utc_now().date())

    initial_board = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-dispute-board",
        headers=owner_headers,
        params={"as_of_date": as_of_date},
    )
    assert initial_board.status_code == 200
    assert initial_board.json()["snapshot_status"] == "CURRENT"
    assert initial_board.json()["open_count"] == 0

    dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers=owner_headers,
        json={
            "goods_receipt_id": purchase_flow["goods_receipt_id"],
            "dispute_type": "SHORT_SUPPLY",
            "note": "Two cartons missing",
        },
    )
    assert dispute.status_code == 200

    stale_board = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-dispute-board",
        headers=owner_headers,
        params={"as_of_date": as_of_date},
    )
    assert stale_board.status_code == 200
    assert stale_board.json()["snapshot_status"] == "STALE_REFRESH_QUEUED"
    assert stale_board.json()["open_count"] == 0
    assert stale_board.json()["snapshot_job_id"]

    queued_jobs = asyncio.run(_list_operations_jobs(client))
    assert len(queued_jobs) == 1
    assert queued_jobs[0].job_type == "SUPPLIER_REPORT_REFRESH"

    processed = asyncio.run(_run_worker_once(client))
    assert processed["completed"] >= 1
    assert processed["dead_lettered"] == 0

    refreshed_board = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-dispute-board",
        headers=owner_headers,
        params={"as_of_date": as_of_date},
    )
    assert refreshed_board.status_code == 200
    assert refreshed_board.json()["snapshot_status"] == "CURRENT"
    assert refreshed_board.json()["open_count"] == 1
