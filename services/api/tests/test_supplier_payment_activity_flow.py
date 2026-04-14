from fastapi.testclient import TestClient

from store_api.main import create_app


def _create_tenant_branch(client: TestClient) -> dict[str, str]:
    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()
    tenant_id = tenant["id"]

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Bengaluru Flagship", "gstin": "29ABCDE1234F1Z5"},
    ).json()
    return {"tenant_id": tenant_id, "branch_id": branch["id"]}


def _create_purchase_invoice(
    client: TestClient,
    *,
    tenant_id: str,
    branch_id: str,
    product_name: str,
    sku_code: str,
    barcode: str,
    hsn_sac_code: str,
    supplier_name: str,
    supplier_gstin: str,
    quantity: float,
    unit_cost: float,
) -> dict[str, str]:
    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": product_name,
            "sku_code": sku_code,
            "barcode": barcode,
            "selling_price": unit_cost * 2,
            "tax_rate_percent": 18,
            "hsn_sac_code": hsn_sac_code,
        },
    ).json()
    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": supplier_name, "gstin": supplier_gstin},
    ).json()
    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": quantity, "unit_cost": unit_cost}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for supplier payment activity"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier payment activity"},
    )
    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    ).json()
    purchase_invoice = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers={"x-actor-role": "inventory_admin"},
        json={"goods_receipt_id": goods_receipt["id"]},
    ).json()
    return {
        "product_id": product["id"],
        "supplier_id": supplier["id"],
        "purchase_invoice_id": purchase_invoice["id"],
        "invoice_number": purchase_invoice["invoice_number"],
    }


def test_supplier_payment_activity_report_tracks_recent_vendor_settlement():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    paper_invoice = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Notebook",
        sku_code="SKU-001",
        barcode="8901234567890",
        hsn_sac_code="4820",
        supplier_name="Paper Supply Co",
        supplier_gstin="29AAAAA1111A1Z5",
        quantity=6,
        unit_cost=50,
    )
    ink_invoice = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Marker Pen",
        sku_code="SKU-002",
        barcode="8901234567891",
        hsn_sac_code="9608",
        supplier_name="Ink Wholesale",
        supplier_gstin="29BBBBB2222B1Z5",
        quantity=2,
        unit_cost=50,
    )

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_invoice['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": paper_invoice['product_id'], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    first_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-001"},
    )
    assert first_payment.status_code == 200

    second_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 195, "payment_method": "upi", "reference": "UPI-001"},
    )
    assert second_payment.status_code == 200

    third_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{ink_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 50, "payment_method": "cash", "reference": "CASH-001"},
    )
    assert third_payment.status_code == 200

    state = client.app.state.store_state
    state.supplier_payments[first_payment.json()["id"]]["payment_date"] = "2026-03-15"
    state.supplier_payments[second_payment.json()["id"]]["payment_date"] = "2026-04-12"
    state.supplier_payments[third_payment.json()["id"]]["payment_date"] = "2026-04-11"

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payment-activity",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "supplier_count": 2,
        "payment_count": 3,
        "paid_total": 345.0,
        "recent_30_days_paid_total": 245.0,
        "records": [
            {
                "supplier_id": paper_invoice["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "payment_count": 2,
                "paid_total": 295.0,
                "recent_30_days_paid_total": 195.0,
                "average_payment_value": 147.5,
                "outstanding_total": 0.0,
                "last_payment_date": "2026-04-12",
                "last_payment_number": "SPAY-2526-000002",
                "last_payment_method": "upi",
                "last_payment_reference": "UPI-001",
                "last_payment_amount": 195.0,
            },
            {
                "supplier_id": ink_invoice["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "payment_count": 1,
                "paid_total": 50.0,
                "recent_30_days_paid_total": 50.0,
                "average_payment_value": 50.0,
                "outstanding_total": 68.0,
                "last_payment_date": "2026-04-11",
                "last_payment_number": "SPAY-2526-000003",
                "last_payment_method": "cash",
                "last_payment_reference": "CASH-001",
                "last_payment_amount": 50.0,
            },
        ],
    }
