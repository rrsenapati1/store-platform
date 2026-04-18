from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable
from uuid import uuid4

from fastapi.testclient import TestClient

from .main import create_app
from .performance_validation import PerformanceSample, launch_foundation_budgets


@dataclass(slots=True)
class LaunchFoundationContext:
    client: TestClient
    tenant_id: str
    branch_id: str
    owner_headers: dict[str, str]
    cashier_headers: dict[str, str]
    product_id: str
    supplier_id: str
    cashier_session_id: str
    cashier_user_id: str
    hub_device_headers: dict[str, str]


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    response.raise_for_status()
    return response.json()


def _get_json(client: TestClient, path: str, *, headers: dict[str, str]) -> dict[str, object]:
    response = client.get(path, headers=headers)
    response.raise_for_status()
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def _post_json(client: TestClient, path: str, *, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
    response = client.post(path, headers=headers, json=payload)
    response.raise_for_status()
    body = response.json()
    assert isinstance(body, dict)
    return body


def _bootstrap_launch_foundation_context(client: TestClient) -> LaunchFoundationContext:
    unique_suffix = uuid4().hex[:8]

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = _post_json(
        client,
        "/v1/platform/tenants",
        headers=admin_headers,
        payload={"name": "Acme Retail", "slug": f"acme-retail-perf-{unique_suffix}"},
    )
    tenant_id = str(tenant["id"])

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
        payload={"name": "Bengaluru Flagship", "code": f"blr-{unique_suffix}", "gstin": "29ABCDE1234F1Z5"},
    )
    branch_id = str(branch["id"])

    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        payload={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )

    staff_profile = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        payload={
            "email": "cashier@acme.local",
            "full_name": "Counter Cashier",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    staff_profile_id = str(staff_profile["id"])

    product = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        payload={
            "name": "Classic Tea",
            "sku_code": f"tea-classic-{unique_suffix}",
            "barcode": f"89012345{unique_suffix}",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "mrp": 120.0,
            "category_code": "TEA",
            "selling_price": 92.5,
        },
    )
    product_id = str(product["id"])

    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        payload={
            "product_id": product_id,
            "selling_price_override": None,
            "availability_status": "ACTIVE",
            "reorder_point": 25.0,
            "target_stock": 150.0,
        },
    )

    supplier = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        payload={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    supplier_id = str(supplier["id"])

    initial_purchase_order = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        payload={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 400, "unit_cost": 61.5}],
        },
    )
    initial_purchase_order_id = str(initial_purchase_order["id"])

    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{initial_purchase_order_id}/submit-approval",
        headers=owner_headers,
        payload={"note": "Initial performance bootstrap approval"},
    )
    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{initial_purchase_order_id}/approve",
        headers=owner_headers,
        payload={"note": "Approved for performance bootstrap"},
    )
    initial_goods_receipt = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        payload={"purchase_order_id": initial_purchase_order_id},
    )

    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers=owner_headers,
        payload={"goods_receipt_id": str(initial_goods_receipt["id"])},
    )

    hub_device = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        payload={
            "device_name": "Branch Hub",
            "device_code": f"BLR-HUB-{unique_suffix}",
            "session_surface": "store_desktop",
            "is_branch_hub": True,
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    hub_device_id = str(hub_device["id"])
    hub_device_headers = {
        "x-store-device-id": hub_device_id,
        "x-store-device-secret": str(hub_device["sync_access_secret"]),
    }

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
    cashier_actor = _get_json(client, "/v1/auth/me", headers=cashier_headers)

    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/attendance-sessions",
        headers=cashier_headers,
        payload={
            "device_registration_id": hub_device_id,
            "staff_profile_id": staff_profile_id,
            "clock_in_note": "Performance attendance bootstrap",
        },
    )
    cashier_runtime_session = _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        payload={
            "device_registration_id": hub_device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Performance bootstrap",
        },
    )
    cashier_session_id = str(cashier_runtime_session["id"])

    _post_json(
        client,
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        payload={
            "cashier_session_id": cashier_session_id,
            "customer_name": "Seed Walk In",
            "customer_gstin": None,
            "payment_method": "CASH",
            "lines": [{"product_id": product_id, "quantity": 2}],
        },
    )

    return LaunchFoundationContext(
        client=client,
        tenant_id=tenant_id,
        branch_id=branch_id,
        owner_headers=owner_headers,
        cashier_headers=cashier_headers,
        product_id=product_id,
        supplier_id=supplier_id,
        cashier_session_id=cashier_session_id,
        cashier_user_id=str(cashier_actor["user_id"]),
        hub_device_headers=hub_device_headers,
    )


def _measure_scenario(action: Callable[[int], None], *, iterations: int) -> list[PerformanceSample]:
    samples: list[PerformanceSample] = []
    for iteration in range(iterations):
        started_at = perf_counter()
        try:
            action(iteration)
        except Exception as exc:  # pragma: no cover - exercised via report status
            samples.append(
                PerformanceSample(
                    duration_ms=(perf_counter() - started_at) * 1000.0,
                    success=False,
                    error_message=str(exc),
                )
            )
        else:
            samples.append(
                PerformanceSample(
                    duration_ms=(perf_counter() - started_at) * 1000.0,
                    success=True,
                )
            )
    return samples


def run_launch_foundation_workloads(*, database_url: str, iterations: int) -> dict[str, list[PerformanceSample]]:
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero")

    with TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    ) as client:
        context = _bootstrap_launch_foundation_context(client)

        def checkout_price_preview(iteration: int) -> None:
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/checkout-price-preview",
                headers=context.cashier_headers,
                payload={
                    "customer_name": f"Perf Preview {iteration}",
                    "customer_gstin": None,
                    "promotion_code": None,
                    "loyalty_points_to_redeem": 0,
                    "store_credit_amount": 0,
                    "lines": [{"product_id": context.product_id, "quantity": 1}],
                },
            )

        def direct_sale_creation(iteration: int) -> None:
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/sales",
                headers=context.cashier_headers,
                payload={
                    "cashier_session_id": context.cashier_session_id,
                    "customer_name": f"Perf Sale {iteration}",
                    "customer_gstin": None,
                    "payment_method": "CASH",
                    "lines": [{"product_id": context.product_id, "quantity": 1}],
                },
            )

        def checkout_payment_session_creation(iteration: int) -> None:
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/checkout-payment-sessions",
                headers=context.cashier_headers,
                payload={
                    "provider_name": "cashfree",
                    "cashier_session_id": context.cashier_session_id,
                    "payment_method": "CASHFREE_UPI_QR",
                    "customer_name": f"Perf Session {iteration}",
                    "customer_gstin": None,
                    "loyalty_points_to_redeem": 0,
                    "store_credit_amount": 0,
                    "lines": [{"product_id": context.product_id, "quantity": 1}],
                },
            )

        def offline_sale_replay(iteration: int) -> None:
            unique_id = f"offline-perf-{iteration}-{uuid4().hex[:8]}"
            payload = {
                "continuity_sale_id": unique_id,
                "continuity_invoice_number": f"OFF-{unique_id.upper()}",
                "idempotency_key": f"offline-replay-{unique_id}",
                "issued_offline_at": "2026-04-18T12:00:00.000Z",
                "staff_actor_id": context.cashier_user_id,
                "cashier_session_id": context.cashier_session_id,
                "customer_name": f"Offline Perf {iteration}",
                "customer_gstin": None,
                "payment_method": "UPI",
                "subtotal": 370.0,
                "cgst_total": 9.25,
                "sgst_total": 9.25,
                "igst_total": 0.0,
                "grand_total": 388.5,
                "lines": [{"product_id": context.product_id, "quantity": 4}],
            }
            _post_json(
                client,
                "/v1/sync/offline-sales/replay",
                headers=context.hub_device_headers,
                payload=payload,
            )

        def reviewed_receiving_creation(iteration: int) -> None:
            purchase_order = _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/purchase-orders",
                headers=context.owner_headers,
                payload={
                    "supplier_id": context.supplier_id,
                    "lines": [{"product_id": context.product_id, "quantity": 5, "unit_cost": 61.5}],
                },
            )
            purchase_order_id = str(purchase_order["id"])
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
                headers=context.owner_headers,
                payload={"note": f"Perf receiving submit {iteration}"},
            )
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/purchase-orders/{purchase_order_id}/approve",
                headers=context.owner_headers,
                payload={"note": f"Perf receiving approve {iteration}"},
            )
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/goods-receipts",
                headers=context.owner_headers,
                payload={"purchase_order_id": purchase_order_id},
            )

        def restock_task_lifecycle(iteration: int) -> None:
            task = _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/restock-tasks",
                headers=context.owner_headers,
                payload={
                    "product_id": context.product_id,
                    "requested_quantity": 3,
                    "source_posture": "BACKROOM_AVAILABLE",
                    "note": f"Perf restock create {iteration}",
                },
            )
            task_id = str(task["id"])
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/restock-tasks/{task_id}/pick",
                headers=context.owner_headers,
                payload={"picked_quantity": 3, "note": f"Perf restock pick {iteration}"},
            )
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/restock-tasks/{task_id}/complete",
                headers=context.owner_headers,
                payload={"completion_note": f"Perf restock complete {iteration}"},
            )

        def reviewed_stock_count_lifecycle(iteration: int) -> None:
            snapshot = _get_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/inventory-snapshot",
                headers=context.owner_headers,
            )
            current_stock = float(snapshot["records"][0]["stock_on_hand"])
            session = _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/stock-count-sessions",
                headers=context.owner_headers,
                payload={"product_id": context.product_id, "note": f"Perf stock count create {iteration}"},
            )
            session_id = str(session["id"])
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/stock-count-sessions/{session_id}/record",
                headers=context.owner_headers,
                payload={"counted_quantity": current_stock, "note": f"Perf stock count record {iteration}"},
            )
            _post_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/stock-count-sessions/{session_id}/approve",
                headers=context.owner_headers,
                payload={"review_note": f"Perf stock count approve {iteration}"},
            )

        def branch_reporting_dashboard_read(_: int) -> None:
            _get_json(
                client,
                f"/v1/tenants/{context.tenant_id}/branches/{context.branch_id}/management-dashboard",
                headers=context.owner_headers,
            )

        scenario_actions: dict[str, Callable[[int], None]] = {
            "checkout_price_preview": checkout_price_preview,
            "direct_sale_creation": direct_sale_creation,
            "checkout_payment_session_creation": checkout_payment_session_creation,
            "offline_sale_replay": offline_sale_replay,
            "reviewed_receiving_creation": reviewed_receiving_creation,
            "restock_task_lifecycle": restock_task_lifecycle,
            "reviewed_stock_count_lifecycle": reviewed_stock_count_lifecycle,
            "branch_reporting_dashboard_read": branch_reporting_dashboard_read,
        }

        budgets = launch_foundation_budgets()
        return {
            budget.scenario_name: _measure_scenario(scenario_actions[budget.scenario_name], iterations=iterations)
            for budget in budgets
        }
