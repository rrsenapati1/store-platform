from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _create_owner_context(*, slug: str) -> tuple[TestClient, str, dict[str, str]]:
    database_url = sqlite_test_database_url(slug)
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
        json={"name": "Acme Retail", "slug": slug},
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
    return client, tenant_id, owner_headers


def _open_cashier_session(
    client: TestClient,
    *,
    tenant_id: str,
    branch_id: str,
    owner_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> dict[str, str]:
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
    return {
        "cashier_session_id": cashier_session.json()["id"],
        "staff_profile_id": staff_profile_id,
        "device_id": device_id,
    }


def _seed_management_context(*, slug: str) -> dict[str, object]:
    client, tenant_id, owner_headers = _create_owner_context(slug=slug)

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Masala Tea",
            "sku_code": "tea-masala-250g",
            "barcode": "8901234567890",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "mrp": 120.0,
            "category_code": "TEA",
            "selling_price": 100.0,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    branch_catalog_item = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        json={
            "product_id": product_id,
            "selling_price_override": None,
            "availability_status": "ACTIVE",
            "reorder_point": 10.0,
            "target_stock": 20.0,
        },
    )
    assert branch_catalog_item.status_code == 200

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    received_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 6, "unit_cost": 40.0}],
        },
    )
    assert received_purchase_order.status_code == 200
    received_purchase_order_id = received_purchase_order.json()["id"]

    submitted_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{received_purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Need replenishment before the weekend rush"},
    )
    assert submitted_purchase_order.status_code == 200

    approved_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{received_purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for branch restock"},
    )
    assert approved_purchase_order.status_code == 200

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": received_purchase_order_id},
    )
    assert goods_receipt.status_code == 200
    goods_receipt_id = goods_receipt.json()["id"]

    purchase_invoice = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers=owner_headers,
        json={"goods_receipt_id": goods_receipt_id},
    )
    assert purchase_invoice.status_code == 200

    session_context = _open_cashier_session(
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
            "cashier_session_id": session_context["cashier_session_id"],
            "customer_name": "Walk In",
            "customer_gstin": None,
            "payment_method": "CASH",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200

    pending_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 5, "unit_cost": 40.0}],
        },
    )
    assert pending_purchase_order.status_code == 200
    pending_purchase_order_id = pending_purchase_order.json()["id"]

    submitted_pending_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{pending_purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Follow-up restock"},
    )
    assert submitted_pending_purchase_order.status_code == 200

    approved_pending_purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{pending_purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for follow-up restock"},
    )
    assert approved_pending_purchase_order.status_code == 200

    restock_task = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/restock-tasks",
        headers=owner_headers,
        json={
            "product_id": product_id,
            "requested_quantity": 3.0,
            "source_posture": "BACKROOM_AVAILABLE",
            "note": "Backroom top-up",
        },
    )
    assert restock_task.status_code == 200

    return {
        "client": client,
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "owner_headers": owner_headers,
        "cashier_headers": cashier_headers,
        "product_id": product_id,
    }


def test_branch_management_dashboard_summarizes_trade_exceptions_and_reorder_recommendations() -> None:
    context = _seed_management_context(slug="branch-management-dashboard")
    client = context["client"]

    dashboard = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/management-dashboard",
        headers=context["owner_headers"],
    )
    assert dashboard.status_code == 200
    body = dashboard.json()

    assert body["branch_id"] == context["branch_id"]
    assert body["branch_name"] == "Bengaluru Flagship"
    assert body["trade"]["sales_today_count"] == 1
    assert body["trade"]["sales_today_total"] == 420.0
    assert body["trade"]["sales_7d_total"] == 420.0
    assert body["trade"]["returns_7d_total"] == 0.0
    assert body["trade"]["average_basket_value_7d"] == 420.0

    assert body["workforce"]["open_shift_count"] == 0
    assert body["workforce"]["open_attendance_count"] == 1
    assert body["workforce"]["open_cashier_count"] == 1

    assert body["operations"]["low_stock_count"] == 1
    assert body["operations"]["restock_open_count"] == 1
    assert body["operations"]["receiving_ready_count"] == 1
    assert body["operations"]["receiving_variance_count"] == 0
    assert body["operations"]["stock_count_open_count"] == 0
    assert body["operations"]["expiring_soon_count"] == 0
    assert body["operations"]["supplier_blocker_count"] == 0
    assert body["operations"]["overdue_supplier_invoice_count"] == 0
    assert body["operations"]["queued_operations_job_count"] == 0

    assert body["procurement"]["approval_pending_count"] == 0
    assert body["procurement"]["approved_pending_receipt_count"] == 1
    assert body["procurement"]["approved_pending_receipt_total"] == 210.0
    assert body["procurement"]["outstanding_payables_total"] == 252.0
    assert body["procurement"]["blocked_release_total"] == 0.0

    assert body["recommendations"] == [
        {
            "product_id": context["product_id"],
            "product_name": "Masala Tea",
            "sku_code": "tea-masala-250g",
            "stock_on_hand": 2.0,
            "reorder_point": 10.0,
            "target_stock": 20.0,
            "suggested_reorder_quantity": 18.0,
            "open_restock_quantity": 3.0,
            "open_purchase_order_quantity": 5.0,
            "net_recommended_order_quantity": 10.0,
            "latest_purchase_unit_cost": 40.0,
            "estimated_purchase_cost": 400.0,
            "recommendation_status": "ORDER_NOW",
        }
    ]


def test_branch_management_dashboard_requires_reports_or_purchase_access() -> None:
    context = _seed_management_context(slug="branch-management-dashboard-access")
    client = context["client"]

    dashboard = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/management-dashboard",
        headers=context["cashier_headers"],
    )
    assert dashboard.status_code == 403
    assert dashboard.json()["detail"] == "Scoped capability required"
