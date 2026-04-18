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


def _create_client(database_name: str) -> TestClient:
    database_url = sqlite_test_database_url(database_name)
    return TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )


def _seed_serialized_checkout_context(client: TestClient) -> dict[str, object]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-serialized"},
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
            "name": "Serialized Phone",
            "sku_code": "phone-x1",
            "barcode": "8901234567001",
            "hsn_sac_code": "8517",
            "gst_rate": 18.0,
            "mrp": 15999.0,
            "category_code": "PHONES",
            "selling_price": 14999.0,
            "tracking_mode": "SERIALIZED",
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
        json={"name": "Acme Devices", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 2, "unit_cost": 12000.0}],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Need launch inventory"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for serialized launch stock"},
    )
    assert approved.status_code == 200

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

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

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Counter Cashier")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

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

    open_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Morning shift",
        },
    )
    assert open_session.status_code == 200

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "product_id": product_id,
        "supplier_id": supplier_id,
        "purchase_order_id": purchase_order_id,
        "owner_headers": owner_headers,
        "cashier_headers": cashier_headers,
        "cashier_session_id": open_session.json()["id"],
    }


def _receive_serialized_stock(
    client: TestClient,
    *,
    tenant_id: str,
    branch_id: str,
    purchase_order_id: str,
    product_id: str,
    owner_headers: dict[str, str],
    serial_numbers: list[str],
):
    return client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={
            "purchase_order_id": purchase_order_id,
            "lines": [
                {
                    "product_id": product_id,
                    "received_quantity": len(serial_numbers),
                    "serial_numbers": serial_numbers,
                }
            ],
        },
    )


def _create_branch_product_with_stock(
    client: TestClient,
    *,
    tenant_id: str,
    branch_id: str,
    supplier_id: str,
    owner_headers: dict[str, str],
    name: str,
    sku_code: str,
    barcode: str,
    category_code: str,
    selling_price: float,
    quantity: int,
    tracking_mode: str = "STANDARD",
    compliance_profile: str = "NONE",
    compliance_config: dict[str, object] | None = None,
    serial_numbers: list[str] | None = None,
) -> dict[str, object]:
    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": name,
            "sku_code": sku_code,
            "barcode": barcode,
            "hsn_sac_code": "3004" if category_code == "PHARMACY" else "2203",
            "gst_rate": 12.0 if category_code == "PHARMACY" else 28.0,
            "mrp": selling_price + 20.0,
            "category_code": category_code,
            "selling_price": selling_price,
            "tracking_mode": tracking_mode,
            "compliance_profile": compliance_profile,
            "compliance_config": compliance_config or {},
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

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": quantity, "unit_cost": max(selling_price - 10.0, 1.0)}],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": f"Stock for {name}"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": f"Approved stock for {name}"},
    )
    assert approved.status_code == 200

    receipt_line = {
        "product_id": product_id,
        "received_quantity": quantity,
    }
    if tracking_mode == "SERIALIZED":
        receipt_line["serial_numbers"] = serial_numbers or [f"{sku_code}-{index + 1:04d}" for index in range(quantity)]
    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={
            "purchase_order_id": purchase_order_id,
            "lines": [receipt_line],
        },
    )
    assert goods_receipt.status_code == 200

    return {
        "product_id": product_id,
        "purchase_order_id": purchase_order_id,
        "goods_receipt": goods_receipt.json(),
    }


def test_serialized_goods_receipt_and_sale_capture_exact_serial_numbers():
    client = _create_client("serialized-inventory-foundation")
    context = _seed_serialized_checkout_context(client)

    goods_receipt = _receive_serialized_stock(
        client,
        tenant_id=str(context["tenant_id"]),
        branch_id=str(context["branch_id"]),
        purchase_order_id=str(context["purchase_order_id"]),
        product_id=str(context["product_id"]),
        owner_headers=context["owner_headers"],
        serial_numbers=["IMEI-0001", "IMEI-0002"],
    )
    assert goods_receipt.status_code == 200
    assert goods_receipt.json()["lines"][0]["serial_numbers"] == ["IMEI-0001", "IMEI-0002"]

    sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
        json={
            "cashier_session_id": context["cashier_session_id"],
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [
                {
                    "product_id": context["product_id"],
                    "quantity": 1,
                    "serial_numbers": ["IMEI-0001"],
                }
            ],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["lines"][0]["serial_numbers"] == ["IMEI-0001"]

    duplicate_sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
        json={
            "cashier_session_id": context["cashier_session_id"],
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "payment_method": "UPI",
            "lines": [
                {
                    "product_id": context["product_id"],
                    "quantity": 1,
                    "serial_numbers": ["IMEI-0001"],
                }
            ],
        },
    )
    assert duplicate_sale.status_code == 400
    assert "not available" in duplicate_sale.json()["detail"]

    inventory_snapshot = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/inventory-snapshot",
        headers=context["owner_headers"],
    )
    assert inventory_snapshot.status_code == 200
    assert inventory_snapshot.json()["records"][0]["stock_on_hand"] == 1.0


def test_serialized_goods_receipt_rejects_missing_serial_numbers():
    client = _create_client("serialized-inventory-receipt-validation")
    context = _seed_serialized_checkout_context(client)

    goods_receipt = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/goods-receipts",
        headers=context["owner_headers"],
        json={
            "purchase_order_id": context["purchase_order_id"],
            "lines": [
                {
                    "product_id": context["product_id"],
                    "received_quantity": 1,
                }
            ],
        },
    )
    assert goods_receipt.status_code == 400
    assert goods_receipt.json()["detail"] == "Serial numbers are required for serialized products"


def test_serialized_checkout_preview_rejects_missing_serial_numbers():
    client = _create_client("serialized-inventory-preview-validation")
    context = _seed_serialized_checkout_context(client)
    goods_receipt = _receive_serialized_stock(
        client,
        tenant_id=str(context["tenant_id"]),
        branch_id=str(context["branch_id"]),
        purchase_order_id=str(context["purchase_order_id"]),
        product_id=str(context["product_id"]),
        owner_headers=context["owner_headers"],
        serial_numbers=["IMEI-0101", "IMEI-0102"],
    )
    assert goods_receipt.status_code == 200

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["cashier_headers"],
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "lines": [{"product_id": context["product_id"], "quantity": 1}],
        },
    )
    assert preview.status_code == 400
    assert preview.json()["detail"] == "Serial numbers are required for serialized products"


def test_rx_required_products_require_prescription_capture_for_preview_and_sale():
    client = _create_client("rx-required-compliance-flow")
    context = _seed_serialized_checkout_context(client)
    rx_product = _create_branch_product_with_stock(
        client,
        tenant_id=str(context["tenant_id"]),
        branch_id=str(context["branch_id"]),
        supplier_id=str(context["supplier_id"]),
        owner_headers=context["owner_headers"],
        name="Prescription Tablet",
        sku_code="rx-tablet-10",
        barcode="8901234567111",
        category_code="PHARMACY",
        selling_price=320.0,
        quantity=5,
        compliance_profile="RX_REQUIRED",
    )

    preview_missing = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["cashier_headers"],
        json={
            "customer_name": "Patient One",
            "customer_gstin": None,
            "lines": [{"product_id": rx_product["product_id"], "quantity": 1}],
        },
    )
    assert preview_missing.status_code == 400
    assert preview_missing.json()["detail"] == "Prescription details are required for prescription-only products"

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["cashier_headers"],
        json={
            "customer_name": "Patient One",
            "customer_gstin": None,
            "lines": [
                {
                    "product_id": rx_product["product_id"],
                    "quantity": 1,
                    "compliance_capture": {
                        "prescription_number": "RX-2026-0001",
                        "patient_name": "Patient One",
                        "prescriber_name": "Dr. Mehta",
                    },
                }
            ],
        },
    )
    assert preview.status_code == 200
    preview_line = preview.json()["lines"][0]
    assert preview_line["compliance_profile"] == "RX_REQUIRED"
    assert preview_line["compliance_capture"] == {
        "prescription_number": "RX-2026-0001",
        "patient_name": "Patient One",
        "prescriber_name": "Dr. Mehta",
    }

    sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
        json={
            "cashier_session_id": context["cashier_session_id"],
            "customer_name": "Patient One",
            "customer_gstin": None,
            "payment_method": "Cash",
            "lines": [
                {
                    "product_id": rx_product["product_id"],
                    "quantity": 1,
                    "compliance_capture": {
                        "prescription_number": "RX-2026-0001",
                        "patient_name": "Patient One",
                        "prescriber_name": "Dr. Mehta",
                    },
                }
            ],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["lines"][0]["compliance_profile"] == "RX_REQUIRED"
    assert sale.json()["lines"][0]["compliance_capture"]["patient_name"] == "Patient One"


def test_age_restricted_products_require_verification_for_preview_and_sale():
    client = _create_client("age-restricted-compliance-flow")
    context = _seed_serialized_checkout_context(client)
    age_product = _create_branch_product_with_stock(
        client,
        tenant_id=str(context["tenant_id"]),
        branch_id=str(context["branch_id"]),
        supplier_id=str(context["supplier_id"]),
        owner_headers=context["owner_headers"],
        name="Reserve Beverage",
        sku_code="bev-reserve-750",
        barcode="8901234567222",
        category_code="ALCOHOL",
        selling_price=850.0,
        quantity=4,
        compliance_profile="AGE_RESTRICTED",
        compliance_config={"minimum_age": 21},
    )

    preview_missing = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["cashier_headers"],
        json={
            "customer_name": "Walk-in Customer",
            "customer_gstin": None,
            "lines": [{"product_id": age_product["product_id"], "quantity": 1}],
        },
    )
    assert preview_missing.status_code == 400
    assert preview_missing.json()["detail"] == "Age verification is required for age-restricted products"

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["cashier_headers"],
        json={
            "customer_name": "Walk-in Customer",
            "customer_gstin": None,
            "lines": [
                {
                    "product_id": age_product["product_id"],
                    "quantity": 1,
                    "compliance_capture": {
                        "age_verified": True,
                        "id_reference": "DL-9988",
                    },
                }
            ],
        },
    )
    assert preview.status_code == 200
    preview_line = preview.json()["lines"][0]
    assert preview_line["compliance_profile"] == "AGE_RESTRICTED"
    assert preview_line["compliance_capture"] == {
        "age_verified": True,
        "id_reference": "DL-9988",
        "minimum_age": 21,
    }

    sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers=context["cashier_headers"],
        json={
            "cashier_session_id": context["cashier_session_id"],
            "customer_name": "Walk-in Customer",
            "customer_gstin": None,
            "payment_method": "UPI",
            "lines": [
                {
                    "product_id": age_product["product_id"],
                    "quantity": 1,
                    "compliance_capture": {
                        "age_verified": True,
                        "id_reference": "DL-9988",
                    },
                }
            ],
        },
    )
    assert sale.status_code == 200
    assert sale.json()["lines"][0]["compliance_profile"] == "AGE_RESTRICTED"
    assert sale.json()["lines"][0]["compliance_capture"]["minimum_age"] == 21
