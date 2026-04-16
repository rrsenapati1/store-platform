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


def _create_customer_profile(client: TestClient, *, tenant_id: str, headers: dict[str, str]) -> str:
    response = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=headers,
        json={
            "full_name": "Acme Traders",
            "phone": "+919999999999",
            "email": "billing@acme.example",
            "gstin": "29AAEPM0111C1Z3",
            "default_note": "Wholesale customer",
            "tags": ["wholesale"],
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_store_credit_can_be_issued_and_loaded_for_an_active_customer_profile() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="store-credit-issue")
    customer_profile_id = _create_customer_profile(client, tenant_id=tenant_id, headers=owner_headers)

    issued = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
        headers=owner_headers,
        json={"amount": 250.0, "note": "Manual welcome credit"},
    )
    assert issued.status_code == 200
    assert issued.json()["customer_profile_id"] == customer_profile_id
    assert issued.json()["available_balance"] == 250.0
    assert issued.json()["issued_total"] == 250.0
    assert issued.json()["redeemed_total"] == 0.0
    assert issued.json()["adjusted_total"] == 0.0
    assert len(issued.json()["lots"]) == 1
    assert issued.json()["lots"][0]["original_amount"] == 250.0
    assert issued.json()["lots"][0]["remaining_amount"] == 250.0
    assert issued.json()["lots"][0]["source_type"] == "MANUAL_ISSUE"
    assert [entry["entry_type"] for entry in issued.json()["ledger_entries"]] == ["ISSUED"]
    assert issued.json()["ledger_entries"][0]["amount"] == 250.0
    assert issued.json()["ledger_entries"][0]["running_balance"] == 250.0

    summary = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit",
        headers=owner_headers,
    )
    assert summary.status_code == 200
    assert summary.json() == issued.json()


def test_store_credit_adjustment_updates_balance_and_ledger_history() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="store-credit-adjustment")
    customer_profile_id = _create_customer_profile(client, tenant_id=tenant_id, headers=owner_headers)

    issued = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
        headers=owner_headers,
        json={"amount": 250.0, "note": "Manual balance"},
    )
    assert issued.status_code == 200

    adjusted = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/adjust",
        headers=owner_headers,
        json={"amount_delta": 40.0, "note": "Counter correction"},
    )
    assert adjusted.status_code == 200
    assert adjusted.json()["available_balance"] == 290.0
    assert adjusted.json()["issued_total"] == 250.0
    assert adjusted.json()["adjusted_total"] == 40.0
    assert [entry["entry_type"] for entry in adjusted.json()["ledger_entries"]] == ["ISSUED", "ADJUSTED"]
    assert [entry["running_balance"] for entry in adjusted.json()["ledger_entries"]] == [250.0, 290.0]
    assert adjusted.json()["ledger_entries"][1]["amount"] == 40.0
    assert len(adjusted.json()["lots"]) == 2
    assert adjusted.json()["lots"][1]["source_type"] == "MANUAL_ADJUSTMENT"
    assert adjusted.json()["lots"][1]["remaining_amount"] == 40.0


def test_approved_sale_return_can_issue_store_credit_for_a_linked_customer_profile() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="store-credit-return-refund")

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

    customer_profile_id = _create_customer_profile(client, tenant_id=tenant_id, headers=owner_headers)

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200
    sale_id = sale.json()["id"]

    sale_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns",
        headers=cashier_headers,
        json={
            "refund_amount": 97.12,
            "refund_method": "STORE_CREDIT",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale_return.status_code == 200
    assert sale_return.json()["status"] == "REFUND_PENDING_APPROVAL"

    before_approval = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit",
        headers=owner_headers,
    )
    assert before_approval.status_code == 200
    assert before_approval.json()["available_balance"] == 0.0

    approved_refund = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sale-returns/{sale_return.json()['id']}/approve-refund",
        headers=owner_headers,
        json={"note": "Approved to credit balance"},
    )
    assert approved_refund.status_code == 200
    assert approved_refund.json()["status"] == "REFUND_APPROVED"
    assert approved_refund.json()["refund_method"] == "STORE_CREDIT"

    after_approval = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit",
        headers=owner_headers,
    )
    assert after_approval.status_code == 200
    assert after_approval.json()["available_balance"] == 97.12
    assert after_approval.json()["issued_total"] == 97.12
    assert after_approval.json()["lots"][0]["source_type"] == "RETURN_REFUND"
    assert after_approval.json()["lots"][0]["source_reference_id"] == sale_return.json()["id"]
    assert after_approval.json()["ledger_entries"][0]["entry_type"] == "ISSUED"
    assert after_approval.json()["ledger_entries"][0]["source_type"] == "RETURN_REFUND"
