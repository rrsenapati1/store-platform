import hashlib
import hmac
import json

from fastapi import HTTPException
from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.services.billing import BillingService


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _seed_checkout_context(client: TestClient) -> dict[str, object]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail"},
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

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "product_id": product_id,
        "owner_headers": owner_headers,
        "cashier_headers": cashier_headers,
    }


def _payment_session_payload(
    *,
    product_id: str,
    payment_method: str = "CASHFREE_UPI_QR",
    handoff_surface: str | None = None,
    provider_payment_mode: str | None = None,
    customer_profile_id: str | None = None,
    loyalty_points_to_redeem: int = 0,
) -> dict[str, object]:
    return {
        "provider_name": "cashfree",
        "payment_method": payment_method,
        "handoff_surface": handoff_surface,
        "provider_payment_mode": provider_payment_mode,
        "customer_profile_id": customer_profile_id,
        "customer_name": "Acme Traders",
        "customer_gstin": "29AAEPM0111C1Z3",
        "loyalty_points_to_redeem": loyalty_points_to_redeem,
        "lines": [{"product_id": product_id, "quantity": 4}],
    }


def _cashfree_success_webhook(*, provider_order_id: str) -> dict[str, object]:
    return {
        "data": {
            "order": {
                "order_id": provider_order_id,
                "order_amount": 388.5,
                "order_currency": "INR",
                "order_tags": None,
            },
            "payment": {
                "cf_payment_id": "cfpay_123456",
                "payment_status": "SUCCESS",
                "payment_amount": 388.5,
                "payment_currency": "INR",
                "payment_message": "Payment completed",
                "payment_time": "2026-04-15T12:10:00+05:30",
                "bank_reference": "UTR1234567",
                "auth_id": None,
                "payment_method": {
                    "upi": {
                        "channel": "qrcode",
                        "upi_id": "customer@upi",
                    }
                },
                "payment_group": "upi",
            },
            "customer_details": {
                "customer_name": "Acme Traders",
                "customer_id": "customer_1",
                "customer_email": "cashier@acme.local",
                "customer_phone": "9999999999",
            },
        },
        "event_time": "2026-04-15T12:10:03+05:30",
        "type": "PAYMENT_SUCCESS_WEBHOOK",
    }


def _cashfree_failure_webhook(*, provider_order_id: str, webhook_type: str, payment_status: str) -> dict[str, object]:
    return {
        "data": {
            "order": {
                "order_id": provider_order_id,
                "order_amount": 388.5,
                "order_currency": "INR",
                "order_tags": None,
            },
            "payment": {
                "cf_payment_id": f"cfpay_{payment_status.lower()}",
                "payment_status": payment_status,
                "payment_amount": 388.5,
                "payment_currency": "INR",
                "payment_message": "Payment not completed",
                "payment_time": "2026-04-15T12:10:00+05:30",
                "bank_reference": None,
                "auth_id": None,
                "payment_method": {
                    "upi": {
                        "channel": "qrcode",
                        "upi_id": "customer@upi",
                    }
                },
                "payment_group": "upi",
            },
            "customer_details": {
                "customer_name": "Acme Traders",
                "customer_id": "customer_1",
                "customer_email": "cashier@acme.local",
                "customer_phone": "9999999999",
            },
        },
        "event_time": "2026-04-15T12:10:03+05:30",
        "type": webhook_type,
    }


def _cashfree_signature(secret: str, payload: bytes, timestamp: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}{payload.decode('utf-8')}".encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def test_cashier_creates_checkout_payment_session_and_receives_qr_ready_state(monkeypatch) -> None:
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", "cashfree-secret")
    database_url = sqlite_test_database_url("checkout-payment-session-create")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)

    response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"])),
    )

    assert response.status_code == 200
    assert response.json()["provider_name"] == "cashfree"
    assert response.json()["payment_method"] == "CASHFREE_UPI_QR"
    assert response.json()["handoff_surface"] == "BRANDED_UPI_QR"
    assert response.json()["provider_payment_mode"] == "cashfree_upi"
    assert response.json()["lifecycle_status"] == "ACTION_READY"
    assert response.json()["order_amount"] == 388.5
    assert response.json()["action_payload"]["kind"] == "upi_qr"
    assert response.json()["qr_payload"]["format"] == "upi_qr"
    assert response.json()["qr_payload"]["value"].startswith("upi://")

    sales_register = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"] == []

    inventory_snapshot = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/inventory-snapshot",
        headers=context["owner_headers"],
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 24.0


def test_cashier_can_create_hosted_terminal_and_phone_checkout_payment_sessions(monkeypatch) -> None:
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", "cashfree-secret")
    database_url = sqlite_test_database_url("checkout-payment-session-hosted-actions")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)

    terminal_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"]), payment_method="CASHFREE_HOSTED_TERMINAL"),
    )
    assert terminal_response.status_code == 200
    assert terminal_response.json()["handoff_surface"] == "HOSTED_TERMINAL"
    assert terminal_response.json()["provider_payment_mode"] == "cashfree_checkout"
    assert terminal_response.json()["lifecycle_status"] == "ACTION_READY"
    assert terminal_response.json()["action_payload"]["kind"] == "hosted_url"
    assert terminal_response.json()["action_payload"]["value"].startswith("https://")
    assert terminal_response.json()["qr_payload"] is None

    phone_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"]), payment_method="CASHFREE_HOSTED_PHONE"),
    )
    assert phone_response.status_code == 200
    assert phone_response.json()["handoff_surface"] == "HOSTED_PHONE"
    assert phone_response.json()["provider_payment_mode"] == "cashfree_checkout"
    assert phone_response.json()["lifecycle_status"] == "ACTION_READY"
    assert phone_response.json()["action_payload"]["kind"] == "hosted_url"
    assert phone_response.json()["action_payload"]["value"].startswith("https://")
    assert phone_response.json()["qr_payload"]["format"] == "hosted_url"
    assert phone_response.json()["qr_payload"]["value"].startswith("https://")


def test_confirmed_cashfree_checkout_session_finalizes_single_sale_and_decrements_stock_once(monkeypatch) -> None:
    secret = "cashfree-secret"
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", secret)
    database_url = sqlite_test_database_url("checkout-payment-session-confirm")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)
    create_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"])),
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    provider_order_id = create_response.json()["provider_order_id"]

    payload = _cashfree_success_webhook(provider_order_id=provider_order_id)
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = "1744699200000"
    signature = _cashfree_signature(secret, payload_bytes, timestamp)

    webhook_first = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": signature,
            "x-webhook-timestamp": timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=payload_bytes,
    )
    assert webhook_first.status_code == 200

    webhook_second = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": signature,
            "x-webhook-timestamp": timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=payload_bytes,
    )
    assert webhook_second.status_code == 200

    session_response = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{session_id}",
        headers=context["cashier_headers"],
    )
    assert session_response.status_code == 200
    assert session_response.json()["lifecycle_status"] == "FINALIZED"
    assert session_response.json()["sale"]["invoice_number"] == "SINV-BLRFLAGSHIP-0001"

    sales_register = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
    )
    assert sales_register.status_code == 200
    assert len(sales_register.json()["records"]) == 1
    assert sales_register.json()["records"][0]["invoice_number"] == "SINV-BLRFLAGSHIP-0001"
    assert sales_register.json()["records"][0]["payment_method"] == "CASHFREE_UPI_QR"

    inventory_snapshot = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/inventory-snapshot",
        headers=context["owner_headers"],
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 20.0


def test_checkout_payment_session_applies_loyalty_redemption_before_provider_finalization(monkeypatch) -> None:
    secret = "cashfree-secret"
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", secret)
    database_url = sqlite_test_database_url("checkout-payment-session-loyalty")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)
    customer_profile = client.post(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles",
        headers=context["owner_headers"],
        json={
            "full_name": "Acme Traders",
            "phone": "+919999999999",
            "email": "billing@acme.example",
            "gstin": "29AAEPM0111C1Z3",
            "default_note": "Wholesale customer",
            "tags": ["wholesale"],
        },
    )
    assert customer_profile.status_code == 200
    customer_profile_id = customer_profile.json()["id"]

    loyalty_program = client.put(
        f"/v1/tenants/{context['tenant_id']}/loyalty-program",
        headers=context["owner_headers"],
        json={
            "status": "ACTIVE",
            "earn_points_per_currency_unit": 1.0,
            "redeem_step_points": 100,
            "redeem_value_per_step": 10.0,
            "minimum_redeem_points": 200,
        },
    )
    assert loyalty_program.status_code == 200

    loyalty_adjustment = client.post(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles/{customer_profile_id}/loyalty/adjust",
        headers=context["owner_headers"],
        json={"points_delta": 300, "note": "Welcome points"},
    )
    assert loyalty_adjustment.status_code == 200

    create_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(
            product_id=str(context["product_id"]),
            customer_profile_id=customer_profile_id,
            loyalty_points_to_redeem=200,
        ),
    )
    assert create_response.status_code == 200
    assert create_response.json()["order_amount"] == 368.5
    session_id = create_response.json()["id"]
    provider_order_id = create_response.json()["provider_order_id"]

    payload = _cashfree_success_webhook(provider_order_id=provider_order_id)
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = "1744699200001"
    signature = _cashfree_signature(secret, payload_bytes, timestamp)

    webhook = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": signature,
            "x-webhook-timestamp": timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=payload_bytes,
    )
    assert webhook.status_code == 200

    session_response = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{session_id}",
        headers=context["cashier_headers"],
    )
    assert session_response.status_code == 200
    assert session_response.json()["sale"]["loyalty_points_redeemed"] == 200
    assert session_response.json()["sale"]["loyalty_discount_amount"] == 20.0
    assert session_response.json()["sale"]["loyalty_points_earned"] == 368

    loyalty_summary = client.get(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles/{customer_profile_id}/loyalty",
        headers=context["owner_headers"],
    )
    assert loyalty_summary.status_code == 200
    assert loyalty_summary.json()["available_points"] == 468


def test_confirmed_checkout_payment_session_can_be_recovered_and_history_lists_recent_records(monkeypatch) -> None:
    secret = "cashfree-secret"
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", secret)
    database_url = sqlite_test_database_url("checkout-payment-session-recovery")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)
    create_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"])),
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    provider_order_id = create_response.json()["provider_order_id"]

    original_create_sale = BillingService.create_sale
    failed_once = {"value": False}

    async def fail_first_finalize(self, *args, **kwargs):
        if not failed_once["value"]:
            failed_once["value"] = True
            raise HTTPException(status_code=503, detail="Simulated sale finalization outage")
        return await original_create_sale(self, *args, **kwargs)

    monkeypatch.setattr(BillingService, "create_sale", fail_first_finalize)

    payload = _cashfree_success_webhook(provider_order_id=provider_order_id)
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = "1744699203000"
    signature = _cashfree_signature(secret, payload_bytes, timestamp)

    webhook = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": signature,
            "x-webhook-timestamp": timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=payload_bytes,
    )
    assert webhook.status_code == 200
    assert webhook.json()["lifecycle_status"] == "CONFIRMED"

    confirmed_session = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{session_id}",
        headers=context["cashier_headers"],
    )
    assert confirmed_session.status_code == 200
    assert confirmed_session.json()["lifecycle_status"] == "CONFIRMED"
    assert confirmed_session.json()["recovery_state"] == "FINALIZE_REQUIRED"
    assert confirmed_session.json()["sale"] is None

    finalized = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{session_id}/finalize",
        headers=context["cashier_headers"],
    )
    assert finalized.status_code == 200
    assert finalized.json()["lifecycle_status"] == "FINALIZED"
    assert finalized.json()["sale"]["invoice_number"] == "SINV-BLRFLAGSHIP-0001"

    history = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
    )
    assert history.status_code == 200
    assert history.json()["records"][0]["id"] == session_id
    assert history.json()["records"][0]["recovery_state"] == "CLOSED"
    assert history.json()["records"][0]["sale"]["invoice_number"] == "SINV-BLRFLAGSHIP-0001"


def test_failed_checkout_payment_session_can_be_retried_into_a_fresh_session(monkeypatch) -> None:
    secret = "cashfree-secret"
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", secret)
    database_url = sqlite_test_database_url("checkout-payment-session-retry")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)
    create_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"]), payment_method="CASHFREE_HOSTED_PHONE"),
    )
    assert create_response.status_code == 200
    original_session_id = create_response.json()["id"]
    provider_order_id = create_response.json()["provider_order_id"]

    payload = _cashfree_failure_webhook(
        provider_order_id=provider_order_id,
        webhook_type="PAYMENT_FAILED_WEBHOOK",
        payment_status="FAILED",
    )
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = "1744699204000"
    signature = _cashfree_signature(secret, payload_bytes, timestamp)
    webhook = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": signature,
            "x-webhook-timestamp": timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=payload_bytes,
    )
    assert webhook.status_code == 200
    assert webhook.json()["lifecycle_status"] == "FAILED"

    retried = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{original_session_id}/retry",
        headers=context["cashier_headers"],
    )
    assert retried.status_code == 200
    assert retried.json()["id"] != original_session_id
    assert retried.json()["handoff_surface"] == "HOSTED_PHONE"
    assert retried.json()["action_payload"]["kind"] == "hosted_url"
    assert retried.json()["action_payload"]["value"].startswith("https://")

    original_status = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{original_session_id}",
        headers=context["cashier_headers"],
    )
    assert original_status.status_code == 200
    assert original_status.json()["lifecycle_status"] == "FAILED"
    assert original_status.json()["recovery_state"] == "RETRYABLE"


def test_failed_or_expired_checkout_payment_sessions_never_create_sales(monkeypatch) -> None:
    secret = "cashfree-secret"
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", secret)
    database_url = sqlite_test_database_url("checkout-payment-session-failure")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)

    first_session = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"])),
    )
    assert first_session.status_code == 200
    first_payload = _cashfree_failure_webhook(
        provider_order_id=first_session.json()["provider_order_id"],
        webhook_type="PAYMENT_FAILED_WEBHOOK",
        payment_status="FAILED",
    )
    first_payload_bytes = json.dumps(first_payload, separators=(",", ":")).encode("utf-8")
    first_timestamp = "1744699201000"
    first_signature = _cashfree_signature(secret, first_payload_bytes, first_timestamp)
    failed_webhook = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": first_signature,
            "x-webhook-timestamp": first_timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=first_payload_bytes,
    )
    assert failed_webhook.status_code == 200

    second_session = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"])),
    )
    assert second_session.status_code == 200
    second_payload = _cashfree_failure_webhook(
        provider_order_id=second_session.json()["provider_order_id"],
        webhook_type="PAYMENT_USER_DROPPED_WEBHOOK",
        payment_status="USER_DROPPED",
    )
    second_payload_bytes = json.dumps(second_payload, separators=(",", ":")).encode("utf-8")
    second_timestamp = "1744699202000"
    second_signature = _cashfree_signature(secret, second_payload_bytes, second_timestamp)
    expired_webhook = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": second_signature,
            "x-webhook-timestamp": second_timestamp,
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=second_payload_bytes,
    )
    assert expired_webhook.status_code == 200

    first_status = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{first_session.json()['id']}",
        headers=context["cashier_headers"],
    )
    assert first_status.status_code == 200
    assert first_status.json()["lifecycle_status"] == "FAILED"

    second_status = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions/{second_session.json()['id']}",
        headers=context["cashier_headers"],
    )
    assert second_status.status_code == 200
    assert second_status.json()["lifecycle_status"] == "EXPIRED"

    sales_register = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"] == []


def test_cashfree_checkout_webhook_rejects_bad_signature(monkeypatch) -> None:
    monkeypatch.setenv("STORE_CONTROL_PLANE_CASHFREE_PAYMENT_WEBHOOK_SECRET", "cashfree-secret")
    database_url = sqlite_test_database_url("checkout-payment-session-bad-signature")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_checkout_context(client)
    create_response = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-payment-sessions",
        headers=context["cashier_headers"],
        json=_payment_session_payload(product_id=str(context["product_id"])),
    )
    assert create_response.status_code == 200

    payload = _cashfree_success_webhook(provider_order_id=create_response.json()["provider_order_id"])
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    webhook = client.post(
        "/v1/billing/webhooks/cashfree/payments",
        headers={
            "x-webhook-signature": "invalid-signature",
            "x-webhook-timestamp": "1744699200000",
            "x-webhook-version": "2023-08-01",
            "content-type": "application/json",
        },
        content=payload_bytes,
    )
    assert webhook.status_code == 401

    sales_register = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"] == []
