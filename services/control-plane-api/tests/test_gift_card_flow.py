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


def _create_branch_catalog_and_cashier(
    client: TestClient,
    *,
    tenant_id: str,
    owner_headers: dict[str, str],
) -> tuple[str, str, dict[str, str]]:
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
    return branch_id, product_id, cashier_headers


def test_gift_card_can_be_issued_adjusted_and_status_toggled() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="gift-card-issue")

    issued = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards",
        headers=owner_headers,
        json={
            "display_name": "Festive Gift Card",
            "gift_card_code": "GIFT-1000",
            "initial_amount": 1000.0,
            "note": "Issued at customer desk",
        },
    )
    assert issued.status_code == 200
    assert issued.json()["gift_card_code"] == "GIFT-1000"
    assert issued.json()["display_name"] == "Festive Gift Card"
    assert issued.json()["available_balance"] == 1000.0
    assert issued.json()["issued_total"] == 1000.0
    assert issued.json()["status"] == "ACTIVE"
    assert [entry["entry_type"] for entry in issued.json()["ledger_entries"]] == ["ISSUED"]

    listing = client.get(
        f"/v1/tenants/{tenant_id}/gift-cards?query=GIFT-1000",
        headers=owner_headers,
    )
    assert listing.status_code == 200
    assert listing.json()["records"][0]["gift_card_code"] == "GIFT-1000"
    assert listing.json()["records"][0]["available_balance"] == 1000.0

    looked_up = client.get(
        f"/v1/tenants/{tenant_id}/gift-cards/code/GIFT-1000",
        headers=owner_headers,
    )
    assert looked_up.status_code == 200
    assert looked_up.json()["id"] == issued.json()["id"]

    adjusted = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards/{issued.json()['id']}/adjust",
        headers=owner_headers,
        json={"amount_delta": -125.0, "note": "Counter correction"},
    )
    assert adjusted.status_code == 200
    assert adjusted.json()["available_balance"] == 875.0
    assert adjusted.json()["adjusted_total"] == -125.0
    assert [entry["entry_type"] for entry in adjusted.json()["ledger_entries"]] == ["ISSUED", "ADJUSTED"]

    disabled = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards/{issued.json()['id']}/disable",
        headers=owner_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"

    reactivated = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards/{issued.json()['id']}/reactivate",
        headers=owner_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"


def test_sale_can_redeem_gift_card_and_reduce_balance() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="gift-card-sale")
    branch_id, product_id, cashier_headers = _create_branch_catalog_and_cashier(
        client,
        tenant_id=tenant_id,
        owner_headers=owner_headers,
    )

    issued = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards",
        headers=owner_headers,
        json={
            "display_name": "Tea Lover Card",
            "gift_card_code": "GIFT-SALE-1",
            "initial_amount": 150.0,
            "note": "Issued for redemption testing",
        },
    )
    assert issued.status_code == 200
    gift_card_id = issued.json()["id"]

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "customer_name": "Walk-in Customer",
            "customer_gstin": None,
            "payment_method": "CASH",
            "gift_card_code": "GIFT-SALE-1",
            "gift_card_amount": 100.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["gift_card_id"] == gift_card_id
    assert sale.json()["gift_card_code"] == "GIFT-SALE-1"
    assert sale.json()["gift_card_amount"] == 97.12
    assert sale.json()["payment"]["payment_method"] == "GIFT_CARD"
    assert sale.json()["payment"]["amount"] == 97.12

    gift_card = client.get(
        f"/v1/tenants/{tenant_id}/gift-cards/{gift_card_id}",
        headers=owner_headers,
    )
    assert gift_card.status_code == 200
    assert gift_card.json()["available_balance"] == 52.88
    assert gift_card.json()["redeemed_total"] == 97.12
    assert [entry["entry_type"] for entry in gift_card.json()["ledger_entries"]] == ["ISSUED", "REDEEMED"]
    assert gift_card.json()["ledger_entries"][1]["source_type"] == "SALE_REDEMPTION"
    assert gift_card.json()["ledger_entries"][1]["source_reference_id"] == sale.json()["sale_id"]


def test_checkout_payment_session_uses_gift_card_in_payment_amount_without_redeeming_early() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="gift-card-checkout-session")
    branch_id, product_id, cashier_headers = _create_branch_catalog_and_cashier(
        client,
        tenant_id=tenant_id,
        owner_headers=owner_headers,
    )

    issued = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards",
        headers=owner_headers,
        json={
            "display_name": "Hosted Checkout Card",
            "gift_card_code": "GIFT-QR-1",
            "initial_amount": 75.0,
            "note": "Issued before hosted checkout",
        },
    )
    assert issued.status_code == 200
    gift_card_id = issued.json()["id"]

    payment_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/checkout-payment-sessions",
        headers=cashier_headers,
        json={
            "provider_name": "cashfree",
            "payment_method": "CASHFREE_UPI_QR",
            "customer_name": "Walk-in Customer",
            "customer_gstin": None,
            "gift_card_code": "GIFT-QR-1",
            "gift_card_amount": 50.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert payment_session.status_code == 200
    assert payment_session.json()["gift_card_id"] == gift_card_id
    assert payment_session.json()["gift_card_code"] == "GIFT-QR-1"
    assert payment_session.json()["gift_card_amount"] == 50.0
    assert payment_session.json()["order_amount"] == 47.12

    gift_card = client.get(
        f"/v1/tenants/{tenant_id}/gift-cards/{gift_card_id}",
        headers=owner_headers,
    )
    assert gift_card.status_code == 200
    assert gift_card.json()["available_balance"] == 75.0
    assert [entry["entry_type"] for entry in gift_card.json()["ledger_entries"]] == ["ISSUED"]


def test_gift_card_redemption_rejects_amounts_above_available_balance() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="gift-card-insufficient")
    branch_id, product_id, cashier_headers = _create_branch_catalog_and_cashier(
        client,
        tenant_id=tenant_id,
        owner_headers=owner_headers,
    )

    issued = client.post(
        f"/v1/tenants/{tenant_id}/gift-cards",
        headers=owner_headers,
        json={
            "display_name": "Small Balance Card",
            "gift_card_code": "GIFT-SMALL-1",
            "initial_amount": 20.0,
            "note": "Small balance test",
        },
    )
    assert issued.status_code == 200

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "customer_name": "Walk-in Customer",
            "customer_gstin": None,
            "payment_method": "CASH",
            "gift_card_code": "GIFT-SMALL-1",
            "gift_card_amount": 30.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale.status_code == 400
    assert sale.json()["detail"] == "Gift card balance is insufficient"
