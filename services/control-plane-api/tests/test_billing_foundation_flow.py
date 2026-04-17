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


def test_cashier_creates_gst_invoice_and_posts_sale_ledger():
    database_url = sqlite_test_database_url("billing-foundation")
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
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["invoice_number"] == "SINV-BLRFLAGSHIP-0001"
    assert sale.json()["invoice_kind"] == "B2B"
    assert sale.json()["irn_status"] == "IRN_PENDING"
    assert sale.json()["subtotal"] == 370.0
    assert sale.json()["cgst_total"] == 9.25
    assert sale.json()["sgst_total"] == 9.25
    assert sale.json()["igst_total"] == 0.0
    assert sale.json()["grand_total"] == 388.5
    assert [tax_line["tax_type"] for tax_line in sale.json()["tax_lines"]] == ["CGST", "SGST"]

    sales_register = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"][0]["invoice_number"] == "SINV-BLRFLAGSHIP-0001"
    assert sales_register.json()["records"][0]["payment_method"] == "UPI"
    assert sales_register.json()["records"][0]["grand_total"] == 388.5

    inventory_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 20.0

    inventory_ledger = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger",
        headers=owner_headers,
    )
    assert inventory_ledger.status_code == 200
    assert [record["entry_type"] for record in inventory_ledger.json()["records"]] == [
        "PURCHASE_RECEIPT",
        "SALE",
    ]


def test_sale_creation_rejects_missing_cashier_session_id() -> None:
    database_url = sqlite_test_database_url("billing-foundation-cashier-session-required")
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
        json={"name": "Acme Retail", "slug": "acme-retail-sale-session-required"},
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
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 422


def test_sale_creation_persists_cashier_session_id() -> None:
    database_url = sqlite_test_database_url("billing-foundation-cashier-session-link")
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
        json={"name": "Acme Retail", "slug": "acme-retail-sale-session-link"},
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
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 2}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["cashier_session_id"] == session_context["cashier_session_id"]


def test_checkout_payment_session_does_not_create_sale_until_payment_confirms():
    database_url = sqlite_test_database_url("billing-foundation-checkout-payment")
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
    session_context = _open_cashier_session(
        client,
        tenant_id=tenant_id,
        branch_id=branch_id,
        owner_headers=owner_headers,
        cashier_headers=cashier_headers,
    )

    payment_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/checkout-payment-sessions",
        headers=cashier_headers,
        json={
            "provider_name": "cashfree",
            "cashier_session_id": session_context["cashier_session_id"],
            "payment_method": "CASHFREE_UPI_QR",
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert payment_session.status_code == 200
    assert payment_session.json()["lifecycle_status"] == "ACTION_READY"
    assert payment_session.json()["handoff_surface"] == "BRANDED_UPI_QR"

    sales_register = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"] == []

    inventory_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 24.0


def test_sale_and_checkout_payment_session_can_link_customer_profile():
    database_url = sqlite_test_database_url("billing-foundation-customer-profile")
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
        json={"name": "Acme Retail", "slug": "acme-retail-customer-link"},
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
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
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [{"product_id": product_id, "quantity": 2}],
        },
    )
    assert sale.status_code == 200
    assert sale.json().get("customer_profile_id") == customer_profile_id

    payment_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/checkout-payment-sessions",
        headers=cashier_headers,
        json={
            "provider_name": "cashfree",
            "cashier_session_id": session_context["cashier_session_id"],
            "payment_method": "CASHFREE_UPI_QR",
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert payment_session.status_code == 200
    assert payment_session.json().get("customer_profile_id") == customer_profile_id


def test_sale_can_partially_redeem_store_credit_for_a_linked_customer_profile() -> None:
    database_url = sqlite_test_database_url("billing-foundation-store-credit-sale")
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
        json={"name": "Acme Retail", "slug": "acme-retail-store-credit-sale"},
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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

    issued_credit = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
        headers=owner_headers,
        json={"amount": 250.0, "note": "Manual issue"},
    )
    assert issued_credit.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
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
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "store_credit_amount": 120.0,
            "lines": [{"product_id": product_id, "quantity": 4}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["customer_profile_id"] == customer_profile_id
    assert sale.json()["store_credit_amount"] == 120.0
    assert sale.json()["payment"]["payment_method"] == "MIXED"

    sales_register = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
    )
    assert sales_register.status_code == 200
    assert sales_register.json()["records"][0]["payment_method"] == "MIXED"

    credit_summary = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit",
        headers=owner_headers,
    )
    assert credit_summary.status_code == 200
    assert credit_summary.json()["available_balance"] == 130.0
    assert credit_summary.json()["redeemed_total"] == 120.0


def test_sale_rejects_store_credit_redemption_without_customer_profile_or_when_balance_is_insufficient() -> None:
    database_url = sqlite_test_database_url("billing-foundation-store-credit-guardrails")
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
        json={"name": "Acme Retail", "slug": "acme-retail-store-credit-guardrails"},
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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

    issued_credit = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
        headers=owner_headers,
        json={"amount": 50.0, "note": "Manual issue"},
    )
    assert issued_credit.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
    session_context = _open_cashier_session(
        client,
        tenant_id=tenant_id,
        branch_id=branch_id,
        owner_headers=owner_headers,
        cashier_headers=cashier_headers,
    )

    anonymous_redemption = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "cashier_session_id": session_context["cashier_session_id"],
            "customer_name": "Walk In",
            "payment_method": "UPI",
            "store_credit_amount": 10.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert anonymous_redemption.status_code == 400
    assert anonymous_redemption.json()["detail"] == "Customer profile is required for store credit redemption"

    excessive_redemption = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "cashier_session_id": session_context["cashier_session_id"],
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "store_credit_amount": 60.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert excessive_redemption.status_code == 400
    assert excessive_redemption.json()["detail"] == "Customer store credit balance is insufficient"


def test_sale_can_redeem_loyalty_points_for_a_linked_customer_profile() -> None:
    database_url = sqlite_test_database_url("billing-foundation-loyalty-redemption")
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
        json={"name": "Acme Retail", "slug": "acme-retail-loyalty"},
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty/adjust",
        headers=owner_headers,
        json={"points_delta": 300, "note": "Welcome points"},
    )
    assert loyalty_adjustment.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
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
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "loyalty_points_to_redeem": 200,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["loyalty_points_redeemed"] == 200
    assert sale.json()["loyalty_discount_amount"] == 20.0
    assert sale.json()["loyalty_points_earned"] == 77

    loyalty_summary = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty",
        headers=owner_headers,
    )
    assert loyalty_summary.status_code == 200
    assert loyalty_summary.json()["available_points"] == 177
    assert [entry["entry_type"] for entry in loyalty_summary.json()["ledger_entries"]] == [
        "ADJUSTED",
        "REDEEMED",
        "EARNED",
    ]


def test_sale_rejects_loyalty_redemption_without_customer_profile_or_when_points_are_invalid() -> None:
    database_url = sqlite_test_database_url("billing-foundation-loyalty-invalid")
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
        json={"name": "Acme Retail", "slug": "acme-retail-loyalty-invalid"},
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty/adjust",
        headers=owner_headers,
        json={"points_delta": 150, "note": "Starter points"},
    )
    assert loyalty_adjustment.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
    session_context = _open_cashier_session(
        client,
        tenant_id=tenant_id,
        branch_id=branch_id,
        owner_headers=owner_headers,
        cashier_headers=cashier_headers,
    )

    anonymous_redemption = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "cashier_session_id": session_context["cashier_session_id"],
            "customer_name": "Walk In",
            "payment_method": "UPI",
            "loyalty_points_to_redeem": 200,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert anonymous_redemption.status_code == 400
    assert anonymous_redemption.json()["detail"] == "Customer profile is required for loyalty redemption"

    insufficient_points = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "cashier_session_id": session_context["cashier_session_id"],
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "loyalty_points_to_redeem": 200,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert insufficient_points.status_code == 400
    assert insufficient_points.json()["detail"] == "Customer loyalty balance is insufficient"


def test_sale_applies_promotion_code_before_loyalty_and_store_credit() -> None:
    database_url = sqlite_test_database_url("billing-foundation-promotions")
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
        json={"name": "Acme Retail", "slug": "acme-retail-promotions"},
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty/adjust",
        headers=owner_headers,
        json={"points_delta": 300, "note": "Welcome points"},
    )
    assert loyalty_adjustment.status_code == 200

    credit_issue = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
        headers=owner_headers,
        json={"amount": 50.0, "note": "Return credit"},
    )
    assert credit_issue.status_code == 200

    campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Welcome Flat Discount",
            "status": "ACTIVE",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": 500,
        },
    )
    assert campaign.status_code == 200
    campaign_id = campaign.json()["id"]

    code = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={"code": "WELCOME20", "status": "ACTIVE", "redemption_limit_per_code": 100},
    )
    assert code.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
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
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "promotion_code": "WELCOME20",
            "loyalty_points_to_redeem": 200,
            "store_credit_amount": 10.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["promotion_campaign_id"] == campaign_id
    assert sale.json()["promotion_code"] == "WELCOME20"
    assert sale.json()["promotion_discount_amount"] == 20.0
    assert sale.json()["loyalty_discount_amount"] == 20.0
    assert sale.json()["store_credit_amount"] == 10.0
    assert sale.json()["grand_total"] == 56.12


def test_sale_rejects_unknown_promotion_code() -> None:
    database_url = sqlite_test_database_url("billing-foundation-promotions-invalid")
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
        json={"name": "Acme Retail", "slug": "acme-retail-promotions-invalid"},
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
    session_context = _open_cashier_session(
        client,
        tenant_id=tenant_id,
        branch_id=branch_id,
        owner_headers=owner_headers,
        cashier_headers=cashier_headers,
    )

    invalid = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=cashier_headers,
        json={
            "cashier_session_id": session_context["cashier_session_id"],
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "promotion_code": "UNKNOWN20",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Promotion code is invalid"


def test_sale_snapshots_automatic_discounts_before_code_loyalty_and_store_credit() -> None:
    database_url = sqlite_test_database_url("billing-foundation-automatic-discounts")
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
        json={"name": "Acme Retail", "slug": "acme-retail-automatic-discounts"},
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
            "mrp": 120.0,
            "category_code": "TEA",
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/loyalty-program",
        headers=owner_headers,
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
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/loyalty/adjust",
        headers=owner_headers,
        json={"points_delta": 300, "note": "Welcome points"},
    )
    assert loyalty_adjustment.status_code == 200

    credit_issue = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/store-credit/issue",
        headers=owner_headers,
        json={"amount": 50.0, "note": "Return credit"},
    )
    assert credit_issue.status_code == 200

    automatic_campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Tea automatic discount",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "ITEM_CATEGORY",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
            "target_category_codes": ["TEA"],
        },
    )
    assert automatic_campaign.status_code == 200

    code_campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Welcome Flat Discount",
            "status": "ACTIVE",
            "trigger_mode": "CODE",
            "scope": "CART",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": 500,
        },
    )
    assert code_campaign.status_code == 200
    code = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{code_campaign.json()['id']}/codes",
        headers=owner_headers,
        json={"code": "WELCOME20", "status": "ACTIVE", "redemption_limit_per_code": 100},
    )
    assert code.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
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
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "promotion_code": "WELCOME20",
            "loyalty_points_to_redeem": 200,
            "store_credit_amount": 10.0,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["automatic_campaign_name"] == "Tea automatic discount"
    assert sale.json()["automatic_discount_total"] == 9.25
    assert sale.json()["promotion_code_discount_total"] == 20.0
    assert sale.json()["total_discount"] == 49.25
    assert sale.json()["invoice_total"] == 66.41
    assert sale.json()["grand_total"] == 46.41
    assert sale.json()["lines"] == [
        {
            "product_id": product_id,
            "product_name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "hsn_sac_code": "0902",
            "quantity": 1.0,
            "mrp": 120.0,
            "unit_selling_price": 92.5,
            "unit_price": 92.5,
            "gst_rate": 5.0,
            "automatic_discount_amount": 9.25,
            "promotion_code_discount_amount": 20.0,
            "promotion_discount_source": "AUTOMATIC_ITEM_CATEGORY+CODE",
            "taxable_amount": 63.25,
            "tax_amount": 3.16,
            "line_subtotal": 92.5,
            "tax_total": 3.16,
            "line_total": 66.41,
        }
    ]


def test_sale_snapshots_customer_voucher_and_marks_it_redeemed() -> None:
    database_url = sqlite_test_database_url("billing-foundation-customer-voucher")
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
        json={"name": "Acme Retail", "slug": "acme-retail-customer-voucher"},
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
            "mrp": 120.0,
            "category_code": "TEA",
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

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
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

    automatic_campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Tea automatic discount",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "ITEM_CATEGORY",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
            "target_category_codes": ["TEA"],
        },
    )
    assert automatic_campaign.status_code == 200

    voucher_campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Customer welcome voucher",
            "status": "ACTIVE",
            "trigger_mode": "ASSIGNED_VOUCHER",
            "scope": "CART",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 25.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert voucher_campaign.status_code == 200

    issued_voucher = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers",
        headers=owner_headers,
        json={"campaign_id": voucher_campaign.json()["id"]},
    )
    assert issued_voucher.status_code == 200
    voucher_id = issued_voucher.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}
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
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "customer_voucher_id": voucher_id,
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["automatic_campaign_name"] == "Tea automatic discount"
    assert sale.json()["customer_voucher_id"] == voucher_id
    assert sale.json()["customer_voucher_name"] == "Customer welcome voucher"
    assert sale.json()["customer_voucher_discount_total"] == 25.0
    assert sale.json()["total_discount"] == 34.25
    assert sale.json()["invoice_total"] == 61.16
    assert sale.json()["grand_total"] == 61.16
    assert sale.json()["lines"] == [
        {
            "product_id": product_id,
            "product_name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "hsn_sac_code": "0902",
            "quantity": 1.0,
            "mrp": 120.0,
            "unit_selling_price": 92.5,
            "unit_price": 92.5,
            "gst_rate": 5.0,
            "automatic_discount_amount": 9.25,
            "promotion_code_discount_amount": 0.0,
            "customer_voucher_discount_amount": 25.0,
            "promotion_discount_source": "AUTOMATIC_ITEM_CATEGORY+ASSIGNED_VOUCHER",
            "taxable_amount": 58.25,
            "tax_amount": 2.91,
            "line_subtotal": 92.5,
            "tax_total": 2.91,
            "line_total": 61.16,
        }
    ]

    vouchers = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers",
        headers=owner_headers,
    )
    assert vouchers.status_code == 200
    assert vouchers.json()["records"] == [
        {
            "id": voucher_id,
            "tenant_id": tenant_id,
            "campaign_id": voucher_campaign.json()["id"],
            "customer_profile_id": customer_profile_id,
            "voucher_code": issued_voucher.json()["voucher_code"],
            "voucher_name": "Customer welcome voucher",
            "voucher_amount": 25.0,
            "status": "REDEEMED",
            "issued_note": None,
            "redeemed_sale_id": sale.json()["sale_id"],
            "created_at": issued_voucher.json()["created_at"],
            "updated_at": vouchers.json()["records"][0]["updated_at"],
            "redeemed_at": vouchers.json()["records"][0]["redeemed_at"],
        }
    ]
