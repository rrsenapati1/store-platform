from fastapi.testclient import TestClient

from store_api.main import create_app


def _create_tenant_branch(client: TestClient) -> dict[str, str]:
    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()
    branch = client.post(
        f"/v1/tenants/{tenant['id']}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Bengaluru Flagship", "gstin": "29ABCDE1234F1Z5"},
    ).json()
    return {"tenant_id": tenant["id"], "branch_id": branch["id"]}


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
        json={"note": "Ready for settlement blocker flow"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for settlement blocker flow"},
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
        "goods_receipt_id": goods_receipt["id"],
        "purchase_invoice_id": purchase_invoice["id"],
        "invoice_number": purchase_invoice["invoice_number"],
    }


def test_supplier_settlement_blockers_report_flags_disputed_suppliers_with_due_exposure():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    hard_hold = _create_purchase_invoice(
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
    soft_hold = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Marker Pen",
        sku_code="SKU-002",
        barcode="8901234567891",
        hsn_sac_code="9608",
        supplier_name="Ink Wholesale",
        supplier_gstin="29BBBBB2222B1Z5",
        payment_terms_days=7,
        quantity=2,
        unit_cost=50,
    )
    clear_supplier = _create_purchase_invoice(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Packing Tape",
        sku_code="SKU-003",
        barcode="8901234567892",
        hsn_sac_code="3919",
        supplier_name="Tape Traders",
        supplier_gstin="29CCCCC3333C1Z5",
        payment_terms_days=0,
        quantity=1,
        unit_cost=50,
    )

    hard_hold_state = client.app.state.store_state.purchase_invoices[hard_hold["purchase_invoice_id"]]
    hard_hold_state["invoice_date"] = "2026-03-11"
    hard_hold_state["due_date"] = "2026-04-10"

    payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{hard_hold['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-HOLD-001"},
    )
    assert payment.status_code == 200

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{hard_hold['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": hard_hold["product_id"], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    hard_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "purchase_invoice_id": hard_hold["purchase_invoice_id"],
            "dispute_type": "RATE_MISMATCH",
            "note": "Invoice does not match approved rate",
        },
    )
    assert hard_dispute.status_code == 200

    soft_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "purchase_invoice_id": soft_hold["purchase_invoice_id"],
            "dispute_type": "SHORT_SUPPLY",
            "note": "Short receipt waiting for vendor confirmation",
        },
    )
    assert soft_dispute.status_code == 200

    state = client.app.state.store_state
    state.vendor_disputes[hard_dispute.json()["id"]]["opened_on"] = "2026-04-01"
    state.vendor_disputes[soft_dispute.json()["id"]]["opened_on"] = "2026-04-11"

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-settlement-blockers",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "supplier_count": 2,
        "hard_hold_count": 1,
        "soft_hold_count": 1,
        "blocked_release_now_total": 195.0,
        "blocked_release_this_week_total": 313.0,
        "blocked_outstanding_total": 313.0,
        "records": [
            {
                "supplier_id": hard_hold["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "hold_status": "HARD_HOLD",
                "open_dispute_count": 1,
                "overdue_open_dispute_count": 1,
                "latest_dispute_type": "RATE_MISMATCH",
                "latest_reference_type": "purchase_invoice",
                "latest_reference_number": hard_hold["invoice_number"],
                "latest_opened_on": "2026-04-01",
                "outstanding_total": 195.0,
                "release_now_total": 195.0,
                "release_this_week_total": 195.0,
                "next_due_date": "2026-04-10",
                "next_due_invoice_number": hard_hold["invoice_number"],
                "most_urgent_status": "OVERDUE",
            },
            {
                "supplier_id": soft_hold["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "hold_status": "SOFT_HOLD",
                "open_dispute_count": 1,
                "overdue_open_dispute_count": 0,
                "latest_dispute_type": "SHORT_SUPPLY",
                "latest_reference_type": "purchase_invoice",
                "latest_reference_number": soft_hold["invoice_number"],
                "latest_opened_on": "2026-04-11",
                "outstanding_total": 118.0,
                "release_now_total": 0.0,
                "release_this_week_total": 118.0,
                "next_due_date": "2026-04-20",
                "next_due_invoice_number": soft_hold["invoice_number"],
                "most_urgent_status": "DUE_IN_7_DAYS",
            },
        ],
    }

    assert clear_supplier["supplier_id"] not in {
        record["supplier_id"] for record in report.json()["records"]
    }
