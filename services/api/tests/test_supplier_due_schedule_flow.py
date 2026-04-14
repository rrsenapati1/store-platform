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
    payment_terms_days: int,
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
        json={"name": supplier_name, "gstin": supplier_gstin, "payment_terms_days": payment_terms_days},
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
        json={"note": "Ready for supplier due schedule"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier due schedule"},
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
        "due_date": purchase_invoice["due_date"],
    }


def test_supplier_due_schedule_reports_overdue_and_upcoming_vendor_dues():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    overdue_invoice = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Notebook",
        sku_code="SKU-001",
        barcode="8901234567890",
        hsn_sac_code="4820",
        supplier_name="Paper Supply Co",
        supplier_gstin="29AAAAA1111A1Z5",
        payment_terms_days=30,
        quantity=6,
        unit_cost=50,
    )
    due_today_invoice = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Marker Pen",
        sku_code="SKU-002",
        barcode="8901234567891",
        hsn_sac_code="9608",
        supplier_name="Ink Wholesale",
        supplier_gstin="29BBBBB2222B1Z5",
        payment_terms_days=0,
        quantity=2,
        unit_cost=50,
    )
    due_soon_invoice = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Packing Tape",
        sku_code="SKU-003",
        barcode="8901234567892",
        hsn_sac_code="3919",
        supplier_name="Tape Traders",
        supplier_gstin="29CCCCC3333C1Z5",
        payment_terms_days=7,
        quantity=1,
        unit_cost=50,
    )

    assert overdue_invoice["due_date"] == "2026-05-13"
    assert due_today_invoice["due_date"] == "2026-04-13"
    assert due_soon_invoice["due_date"] == "2026-04-20"

    overdue_state = client.app.state.store_state.purchase_invoices[overdue_invoice["purchase_invoice_id"]]
    overdue_state["invoice_date"] = "2026-03-11"
    overdue_state["due_date"] = "2026-04-10"

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{overdue_invoice['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": overdue_invoice['product_id'], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    supplier_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{overdue_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-DUE-001"},
    )
    assert supplier_payment.status_code == 200

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-due-schedule",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "open_invoice_count": 3,
        "overdue_invoice_count": 1,
        "overdue_total": 195.0,
        "due_today_total": 118.0,
        "due_in_7_days_total": 59.0,
        "due_in_8_30_days_total": 0.0,
        "due_later_total": 0.0,
        "outstanding_total": 372.0,
        "records": [
            {
                "purchase_invoice_id": overdue_invoice["purchase_invoice_id"],
                "purchase_invoice_number": overdue_invoice["invoice_number"],
                "supplier_id": overdue_invoice["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "invoice_date": "2026-03-11",
                "due_date": "2026-04-10",
                "payment_terms_days": 30,
                "grand_total": 354.0,
                "credit_note_total": 59.0,
                "paid_total": 100.0,
                "outstanding_total": 195.0,
                "days_until_due": -3,
                "due_status": "OVERDUE",
            },
            {
                "purchase_invoice_id": due_today_invoice["purchase_invoice_id"],
                "purchase_invoice_number": due_today_invoice["invoice_number"],
                "supplier_id": due_today_invoice["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "invoice_date": "2026-04-13",
                "due_date": "2026-04-13",
                "payment_terms_days": 0,
                "grand_total": 118.0,
                "credit_note_total": 0.0,
                "paid_total": 0.0,
                "outstanding_total": 118.0,
                "days_until_due": 0,
                "due_status": "DUE_TODAY",
            },
            {
                "purchase_invoice_id": due_soon_invoice["purchase_invoice_id"],
                "purchase_invoice_number": due_soon_invoice["invoice_number"],
                "supplier_id": due_soon_invoice["supplier_id"],
                "supplier_name": "Tape Traders",
                "invoice_date": "2026-04-13",
                "due_date": "2026-04-20",
                "payment_terms_days": 7,
                "grand_total": 59.0,
                "credit_note_total": 0.0,
                "paid_total": 0.0,
                "outstanding_total": 59.0,
                "days_until_due": 7,
                "due_status": "DUE_IN_7_DAYS",
            },
        ],
    }
