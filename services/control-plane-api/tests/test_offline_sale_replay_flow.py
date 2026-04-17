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


def _bootstrap_replay_context(client: TestClient) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-offline-sales"},
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
    cashier_actor = client.get("/v1/auth/me", headers=cashier_headers)
    assert cashier_actor.status_code == 200

    hub = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Branch Hub",
            "device_code": "BLR-HUB-01",
            "session_surface": "store_desktop",
            "is_branch_hub": True,
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert hub.status_code == 200
    hub_payload = hub.json()

    cashier_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": hub_payload["id"],
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 150.0,
            "opening_note": "Branch hub opening float",
        },
    )
    assert cashier_session.status_code == 200

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "product_id": product_id,
        "owner_access_token": owner_session["access_token"],
        "cashier_user_id": cashier_actor.json()["user_id"],
        "cashier_session_id": cashier_session.json()["id"],
        "hub_device_id": hub_payload["id"],
        "hub_device_secret": hub_payload["sync_access_secret"],
    }


def _offline_sale_payload(context: dict[str, str], *, quantity: float) -> dict[str, object]:
    return {
        "continuity_sale_id": "offline-sale-1",
        "continuity_invoice_number": "OFF-BLRFLAGSHIP-0001",
        "idempotency_key": "offline-replay-offline-sale-1",
        "issued_offline_at": "2026-04-14T18:00:00.000Z",
        "cashier_session_id": context["cashier_session_id"],
        "staff_actor_id": context["cashier_user_id"],
        "customer_name": "Acme Traders",
        "customer_gstin": "29AAEPM0111C1Z3",
        "payment_method": "UPI",
        "subtotal": 370.0 if quantity == 4 else 2775.0,
        "cgst_total": 9.25 if quantity == 4 else 69.38,
        "sgst_total": 9.25 if quantity == 4 else 69.37,
        "igst_total": 0.0,
        "grand_total": 388.5 if quantity == 4 else 2913.75,
        "lines": [
            {
                "product_id": context["product_id"],
                "quantity": quantity,
            }
        ],
    }


def test_branch_hub_replays_offline_sale_once_and_returns_duplicate_result() -> None:
    database_url = sqlite_test_database_url("offline-sale-replay")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_replay_context(client)
    device_headers = {
        "x-store-device-id": context["hub_device_id"],
        "x-store-device-secret": context["hub_device_secret"],
    }
    payload = _offline_sale_payload(context, quantity=4)

    accepted = client.post("/v1/sync/offline-sales/replay", headers=device_headers, json=payload)
    assert accepted.status_code == 200
    assert accepted.json()["result"] == "accepted"
    assert accepted.json()["duplicate"] is False
    assert accepted.json()["sale_id"]
    assert accepted.json()["invoice_number"] == "SINV-BLRFLAGSHIP-0001"

    sales = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"authorization": f"Bearer {context['owner_access_token']}"},
    )
    assert sales.status_code == 200
    assert sales.json()["records"][0]["cashier_session_id"] == context["cashier_session_id"]

    duplicate = client.post("/v1/sync/offline-sales/replay", headers=device_headers, json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["result"] == "accepted"
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["sale_id"] == accepted.json()["sale_id"]


def test_branch_hub_replay_records_conflict_when_cloud_stock_has_diverged() -> None:
    database_url = sqlite_test_database_url("offline-sale-replay-conflict")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_replay_context(client)
    device_headers = {
        "x-store-device-id": context["hub_device_id"],
        "x-store-device-secret": context["hub_device_secret"],
    }

    conflict = client.post(
        "/v1/sync/offline-sales/replay",
        headers=device_headers,
        json=_offline_sale_payload(context, quantity=30),
    )
    assert conflict.status_code == 200
    assert conflict.json()["result"] == "conflict_review_required"
    assert conflict.json()["duplicate"] is False
    assert conflict.json()["conflict_id"]


def test_branch_hub_replay_rejects_suspended_commercial_access() -> None:
    database_url = sqlite_test_database_url("offline-sale-replay-suspended")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_replay_context(client)
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    suspend = client.post(
        f"/v1/platform/tenants/{context['tenant_id']}/billing/suspend",
        headers=admin_headers,
        json={"reason": "Billing hold"},
    )
    assert suspend.status_code == 200

    device_headers = {
        "x-store-device-id": context["hub_device_id"],
        "x-store-device-secret": context["hub_device_secret"],
    }

    replay = client.post(
        "/v1/sync/offline-sales/replay",
        headers=device_headers,
        json=_offline_sale_payload(context, quantity=4),
    )

    assert replay.status_code == 402
    assert replay.json()["detail"] == "Commercial access is suspended for this tenant. Ask the owner to update billing."
