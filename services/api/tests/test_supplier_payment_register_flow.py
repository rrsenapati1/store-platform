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
        json={"note": "Ready for supplier payment register"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier payment register"},
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


def test_supplier_payment_register_reports_recent_payments_and_method_mix():
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
        json={"lines": [{"product_id": paper_invoice["product_id"], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    first_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-001"},
    )
    assert first_payment.status_code == 200

    second_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{ink_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 50, "payment_method": "cash", "reference": "CASH-001"},
    )
    assert second_payment.status_code == 200

    final_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 195, "payment_method": "upi", "reference": "UPI-001"},
    )
    assert final_payment.status_code == 200

    state = client.app.state.store_state
    state.supplier_payments[first_payment.json()["id"]]["payment_date"] = "2026-04-12"
    state.supplier_payments[second_payment.json()["id"]]["payment_date"] = "2026-04-11"
    state.supplier_payments[final_payment.json()["id"]]["payment_date"] = "2026-04-13"

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payment-register",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "payment_count": 3,
        "supplier_count": 2,
        "paid_total": 345.0,
        "bank_transfer_total": 100.0,
        "cash_total": 50.0,
        "upi_total": 195.0,
        "other_total": 0.0,
        "latest_payment_date": "2026-04-13",
        "records": [
            {
                "payment_id": final_payment.json()["id"],
                "payment_number": "SPAY-2526-000003",
                "payment_date": "2026-04-13",
                "supplier_id": paper_invoice["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "purchase_invoice_id": paper_invoice["purchase_invoice_id"],
                "purchase_invoice_number": paper_invoice["invoice_number"],
                "payment_method": "upi",
                "reference": "UPI-001",
                "amount": 195.0,
                "invoice_grand_total": 354.0,
                "invoice_credit_note_total": 59.0,
                "invoice_paid_total_after_payment": 295.0,
                "remaining_outstanding_total": 0.0,
                "settlement_status_after_payment": "SETTLED",
            },
            {
                "payment_id": first_payment.json()["id"],
                "payment_number": "SPAY-2526-000001",
                "payment_date": "2026-04-12",
                "supplier_id": paper_invoice["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "purchase_invoice_id": paper_invoice["purchase_invoice_id"],
                "purchase_invoice_number": paper_invoice["invoice_number"],
                "payment_method": "bank_transfer",
                "reference": "UTR-001",
                "amount": 100.0,
                "invoice_grand_total": 354.0,
                "invoice_credit_note_total": 59.0,
                "invoice_paid_total_after_payment": 100.0,
                "remaining_outstanding_total": 195.0,
                "settlement_status_after_payment": "PARTIALLY_SETTLED",
            },
            {
                "payment_id": second_payment.json()["id"],
                "payment_number": "SPAY-2526-000002",
                "payment_date": "2026-04-11",
                "supplier_id": ink_invoice["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "purchase_invoice_id": ink_invoice["purchase_invoice_id"],
                "purchase_invoice_number": ink_invoice["invoice_number"],
                "payment_method": "cash",
                "reference": "CASH-001",
                "amount": 50.0,
                "invoice_grand_total": 118.0,
                "invoice_credit_note_total": 0.0,
                "invoice_paid_total_after_payment": 50.0,
                "remaining_outstanding_total": 68.0,
                "settlement_status_after_payment": "PARTIALLY_SETTLED",
            },
        ],
    }
