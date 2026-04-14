from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from .main import create_app
from .services.operations_worker import OperationsWorkerService
from .utils import utc_now


@dataclass(slots=True)
class ControlPlaneSmokeResult:
    tenant_id: str
    branch_id: str
    runtime_device_id: str
    allocated_barcode: str
    barcode_price_label: str
    scanned_product_name: str
    goods_receipt_number: str
    tracked_batch_lot_count: int
    expiring_batch_lot_count: int
    batch_write_off_status: str
    batch_write_off_remaining_quantity: float
    sale_invoice_number: str
    gst_export_status: str
    attached_irn: str
    customer_directory_count: int
    customer_history_sales_count: int
    customer_report_repeat_count: int
    queued_print_job_count: int
    queued_print_job_types: list[str]
    heartbeat_job_count: int
    completed_print_job_status: str
    failed_print_job_status: str
    inventory_stock_on_hand: float
    ledger_entry_types: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    response.raise_for_status()
    return response.json()


def _post_json(client: TestClient, path: str, *, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(path, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def _get_json(client: TestClient, path: str, *, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get(path, headers=headers)
    response.raise_for_status()
    return response.json()


async def _run_worker_once(client: TestClient) -> dict[str, int]:
    async with client.app.state.session_factory() as session:
        worker_service = OperationsWorkerService(session)
        return await worker_service.process_due_jobs(limit=10, now=utc_now())


def run_control_plane_smoke(*, database_url: str, platform_admin_email: str = "admin@store.local") -> ControlPlaneSmokeResult:
    with TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=[platform_admin_email],
        )
    ) as client:
        smoke_suffix = uuid4().hex[:8]
        admin_session = _exchange(client, subject="platform-admin-1", email=platform_admin_email, name="Platform Admin")
        admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

        tenant = _post_json(
            client,
            "/v1/platform/tenants",
            headers=admin_headers,
            payload={"name": "Acme Retail", "slug": f"acme-retail-smoke-{smoke_suffix}"},
        )
        tenant_id = tenant["id"]

        _post_json(
            client,
            f"/v1/platform/tenants/{tenant_id}/owner-invites",
            headers=admin_headers,
            payload={"email": "owner@acme.local", "full_name": "Acme Owner"},
        )

        owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
        owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

        branch = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches",
            headers=owner_headers,
            payload={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
        )
        branch_id = branch["id"]

        product = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/catalog/products",
            headers=owner_headers,
            payload={
                "name": "Classic Tea",
                "sku_code": "tea-classic-250g",
                "barcode": "",
                "hsn_sac_code": "0902",
                "gst_rate": 5.0,
                "selling_price": 92.5,
            },
        )
        product_id = product["id"]

        _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
            headers=owner_headers,
            payload={"product_id": product_id, "selling_price_override": None, "availability_status": "ACTIVE"},
        )
        barcode_allocation = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/catalog/products/{product_id}/barcode-allocation",
            headers=owner_headers,
            payload={},
        )
        barcode_preview = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/barcode-label-preview/{product_id}",
            headers=owner_headers,
        )

        supplier = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/suppliers",
            headers=owner_headers,
            payload={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
        )
        supplier_id = supplier["id"]

        purchase_order = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
            headers=owner_headers,
            payload={
                "supplier_id": supplier_id,
                "lines": [{"product_id": product_id, "quantity": 24, "unit_cost": 61.5}],
            },
        )
        purchase_order_id = purchase_order["id"]

        _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
            headers=owner_headers,
            payload={"note": "Smoke-test approval submission"},
        )
        _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
            headers=owner_headers,
            payload={"note": "Smoke-test approval"},
        )

        goods_receipt = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
            headers=owner_headers,
            payload={"purchase_order_id": purchase_order_id},
        )
        today = utc_now().date()
        batch_lots = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt['id']}/batch-lots",
            headers=owner_headers,
            payload={
                "lots": [
                    {
                        "product_id": product_id,
                        "batch_number": "BATCH-A",
                        "quantity": 12,
                        "expiry_date": (today + timedelta(days=5)).isoformat(),
                    },
                    {
                        "product_id": product_id,
                        "batch_number": "BATCH-B",
                        "quantity": 12,
                        "expiry_date": (today + timedelta(days=60)).isoformat(),
                    },
                ]
            },
        )
        batch_expiry_report = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
            headers=owner_headers,
        )
        batch_write_off = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-lots/{batch_lots['records'][0]['id']}/expiry-write-offs",
            headers=owner_headers,
            payload={"quantity": 2, "reason": "Smoke expiry control"},
        )

        device = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
            headers=owner_headers,
            payload={
                "device_name": "Counter Desktop 1",
                "device_code": "counter-1",
                "session_surface": "store_desktop",
                "assigned_staff_profile_id": None,
            },
        )
        device_id = device["id"]

        _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
            headers=owner_headers,
            payload={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
        )

        cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
        cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

        runtime_devices = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices",
            headers=cashier_headers,
        )
        assert runtime_devices["records"][0]["id"] == device_id
        scan_lookup = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-scan/{barcode_allocation['barcode']}",
            headers=cashier_headers,
        )

        sale = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
            headers=cashier_headers,
            payload={
                "customer_name": "Acme Traders",
                "customer_gstin": "29AAEPM0111C1Z3",
                "payment_method": "UPI",
                "lines": [{"product_id": product_id, "quantity": 4}],
            },
        )
        sale_id = sale["id"]
        gst_export = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports",
            headers=owner_headers,
            payload={"sale_id": sale_id},
        )
        asyncio.run(_run_worker_once(client))
        irn_attachment = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports/{gst_export['id']}/attach-irn",
            headers=owner_headers,
            payload={"irn": "IRN-SMOKE-001", "ack_no": "ACK-SMOKE-001", "signed_qr_payload": "signed-qr-smoke-001"},
        )

        invoice_print_job = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sales/{sale_id}",
            headers=cashier_headers,
            payload={"device_id": device_id, "copies": 1},
        )

        heartbeat = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/heartbeat",
            headers=cashier_headers,
            payload={},
        )

        completed_job = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs/{invoice_print_job['id']}/complete",
            headers=cashier_headers,
            payload={"status": "COMPLETED"},
        )

        _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/barcode-labels/{product_id}",
            headers=owner_headers,
            payload={"device_id": device_id, "copies": 2},
        )

        queued_jobs = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs",
            headers=cashier_headers,
        )

        sale_return = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns",
            headers=cashier_headers,
            payload={
                "refund_amount": 97.12,
                "refund_method": "UPI",
                "lines": [{"product_id": product_id, "quantity": 1}],
            },
        )

        customer_directory = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/customers",
            headers=owner_headers,
        )
        customer_id = customer_directory["records"][0]["customer_id"]
        customer_history = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/customers/{customer_id}/history",
            headers=owner_headers,
        )
        branch_customer_report = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/customer-report",
            headers=owner_headers,
        )

        credit_note_print_job = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sale-returns/{sale_return['id']}",
            headers=cashier_headers,
            payload={"device_id": device_id, "copies": 1},
        )

        failed_job = _post_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs/{credit_note_print_job['id']}/complete",
            headers=cashier_headers,
            payload={"status": "FAILED", "failure_reason": "Verification retry"},
        )

        inventory_snapshot = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
            headers=owner_headers,
        )
        inventory_ledger = _get_json(
            client,
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger",
            headers=owner_headers,
        )

        return ControlPlaneSmokeResult(
            tenant_id=tenant_id,
            branch_id=branch_id,
            runtime_device_id=device_id,
            allocated_barcode=barcode_allocation["barcode"],
            barcode_price_label=barcode_preview["price_label"],
            scanned_product_name=scan_lookup["product_name"],
            goods_receipt_number=goods_receipt["goods_receipt_number"],
            tracked_batch_lot_count=batch_expiry_report["tracked_lot_count"],
            expiring_batch_lot_count=batch_expiry_report["expiring_soon_count"],
            batch_write_off_status=batch_write_off["status"],
            batch_write_off_remaining_quantity=batch_write_off["remaining_quantity"],
            sale_invoice_number=sale["invoice_number"],
            gst_export_status=irn_attachment["status"],
            attached_irn=irn_attachment["irn"],
            customer_directory_count=len(customer_directory["records"]),
            customer_history_sales_count=customer_history["sales_summary"]["sales_count"],
            customer_report_repeat_count=branch_customer_report["repeat_customer_count"],
            queued_print_job_count=len(queued_jobs["records"]),
            queued_print_job_types=[record["job_type"] for record in queued_jobs["records"]],
            heartbeat_job_count=heartbeat["queued_job_count"],
            completed_print_job_status=completed_job["status"],
            failed_print_job_status=failed_job["status"],
            inventory_stock_on_hand=inventory_snapshot["records"][0]["stock_on_hand"],
            ledger_entry_types=[record["entry_type"] for record in inventory_ledger["records"]],
        )
