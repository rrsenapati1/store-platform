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
        json={"note": "Ready for supplier payment run"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier payment run"},
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


def test_supplier_payment_run_reports_vendor_release_priority():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    urgent_invoice = _create_purchase_invoice(
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

    urgent_state = client.app.state.store_state.purchase_invoices[urgent_invoice["purchase_invoice_id"]]
    urgent_state["invoice_date"] = "2026-03-11"
    urgent_state["due_date"] = "2026-04-10"

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{urgent_invoice['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": urgent_invoice['product_id'], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    supplier_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{urgent_invoice['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-RUN-001"},
    )
    assert supplier_payment.status_code == 200

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payment-run",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "supplier_count": 3,
        "release_now_total": 313.0,
        "release_this_week_total": 372.0,
        "release_this_month_total": 372.0,
        "outstanding_total": 372.0,
        "records": [
            {
                "supplier_id": urgent_invoice["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "open_invoice_count": 1,
                "overdue_total": 195.0,
                "due_today_total": 0.0,
                "due_in_7_days_total": 0.0,
                "due_in_8_30_days_total": 0.0,
                "due_later_total": 0.0,
                "release_now_total": 195.0,
                "release_this_week_total": 195.0,
                "release_this_month_total": 195.0,
                "outstanding_total": 195.0,
                "next_due_date": "2026-04-10",
                "next_due_invoice_number": urgent_invoice["invoice_number"],
                "most_urgent_status": "OVERDUE",
            },
            {
                "supplier_id": due_today_invoice["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "open_invoice_count": 1,
                "overdue_total": 0.0,
                "due_today_total": 118.0,
                "due_in_7_days_total": 0.0,
                "due_in_8_30_days_total": 0.0,
                "due_later_total": 0.0,
                "release_now_total": 118.0,
                "release_this_week_total": 118.0,
                "release_this_month_total": 118.0,
                "outstanding_total": 118.0,
                "next_due_date": "2026-04-13",
                "next_due_invoice_number": due_today_invoice["invoice_number"],
                "most_urgent_status": "DUE_TODAY",
            },
            {
                "supplier_id": due_soon_invoice["supplier_id"],
                "supplier_name": "Tape Traders",
                "open_invoice_count": 1,
                "overdue_total": 0.0,
                "due_today_total": 0.0,
                "due_in_7_days_total": 59.0,
                "due_in_8_30_days_total": 0.0,
                "due_later_total": 0.0,
                "release_now_total": 0.0,
                "release_this_week_total": 59.0,
                "release_this_month_total": 59.0,
                "outstanding_total": 59.0,
                "next_due_date": "2026-04-20",
                "next_due_invoice_number": due_soon_invoice["invoice_number"],
                "most_urgent_status": "DUE_IN_7_DAYS",
            },
        ],
    }
