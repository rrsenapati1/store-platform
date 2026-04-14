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


def _create_supplier_receipt(
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
    create_purchase_invoice: bool,
) -> dict[str, str | None]:
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
        json={"note": "Ready for supplier escalation flow"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier escalation flow"},
    )
    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    ).json()

    purchase_invoice_id = None
    invoice_number = None
    if create_purchase_invoice:
        purchase_invoice = client.post(
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
            headers={"x-actor-role": "inventory_admin"},
            json={"goods_receipt_id": goods_receipt["id"]},
        ).json()
        purchase_invoice_id = purchase_invoice["id"]
        invoice_number = purchase_invoice["invoice_number"]

    return {
        "product_id": product["id"],
        "supplier_id": supplier["id"],
        "goods_receipt_id": goods_receipt["id"],
        "purchase_invoice_id": purchase_invoice_id,
        "invoice_number": invoice_number,
    }


def test_supplier_escalation_report_prioritizes_finance_owner_stale_and_branch_follow_up():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    hard_hold = _create_supplier_receipt(
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
        create_purchase_invoice=True,
    )
    soft_hold = _create_supplier_receipt(
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
        create_purchase_invoice=True,
    )
    branch_follow_up = _create_supplier_receipt(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Shipping Box",
        sku_code="SKU-003",
        barcode="8901234567892",
        hsn_sac_code="4819",
        supplier_name="Box Makers",
        supplier_gstin="29CCCCC3333C1Z5",
        payment_terms_days=7,
        quantity=2,
        unit_cost=30,
        create_purchase_invoice=False,
    )
    stale_case = _create_supplier_receipt(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Archive File",
        sku_code="SKU-004",
        barcode="8901234567893",
        hsn_sac_code="4820",
        supplier_name="Archive Traders",
        supplier_gstin="29DDDDD4444D1Z5",
        payment_terms_days=7,
        quantity=1,
        unit_cost=40,
        create_purchase_invoice=False,
    )

    hard_hold_state = client.app.state.store_state.purchase_invoices[hard_hold["purchase_invoice_id"]]
    hard_hold_state["invoice_date"] = "2026-03-11"
    hard_hold_state["due_date"] = "2026-04-10"

    supplier_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{hard_hold['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-ESC-001"},
    )
    assert supplier_payment.status_code == 200

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

    branch_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "goods_receipt_id": branch_follow_up["goods_receipt_id"],
            "dispute_type": "DAMAGED_STOCK",
            "note": "Boxes arrived dented",
        },
    )
    assert branch_dispute.status_code == 200

    stale_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "goods_receipt_id": stale_case["goods_receipt_id"],
            "dispute_type": "MISSING_DOCS",
            "note": "Missing compliance documents",
        },
    )
    assert stale_dispute.status_code == 200

    state = client.app.state.store_state
    state.vendor_disputes[hard_dispute.json()["id"]]["opened_on"] = "2026-04-01"
    state.vendor_disputes[soft_dispute.json()["id"]]["opened_on"] = "2026-04-11"
    state.vendor_disputes[branch_dispute.json()["id"]]["opened_on"] = "2026-04-12"
    state.vendor_disputes[stale_dispute.json()["id"]]["opened_on"] = "2026-03-20"

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-escalation-report",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "open_case_count": 4,
        "finance_escalation_count": 1,
        "owner_escalation_count": 1,
        "stale_case_count": 1,
        "branch_follow_up_count": 1,
        "blocked_release_now_total": 195.0,
        "blocked_release_this_week_total": 313.0,
        "blocked_outstanding_total": 313.0,
        "records": [
            {
                "dispute_id": hard_dispute.json()["id"],
                "supplier_id": hard_hold["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "reference_type": "purchase_invoice",
                "reference_number": hard_hold["invoice_number"],
                "dispute_type": "RATE_MISMATCH",
                "opened_on": "2026-04-01",
                "age_days": 12,
                "overdue": True,
                "hold_status": "HARD_HOLD",
                "blocked_release_now_total": 195.0,
                "blocked_release_this_week_total": 195.0,
                "blocked_outstanding_total": 195.0,
                "next_due_invoice_number": hard_hold["invoice_number"],
                "most_urgent_status": "OVERDUE",
                "escalation_status": "FINANCE_ESCALATION",
                "escalation_target": "finance_admin",
                "next_action": "Freeze release and resolve invoice dispute before payment",
            },
            {
                "dispute_id": soft_dispute.json()["id"],
                "supplier_id": soft_hold["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "reference_type": "purchase_invoice",
                "reference_number": soft_hold["invoice_number"],
                "dispute_type": "SHORT_SUPPLY",
                "opened_on": "2026-04-11",
                "age_days": 2,
                "overdue": False,
                "hold_status": "SOFT_HOLD",
                "blocked_release_now_total": 0.0,
                "blocked_release_this_week_total": 118.0,
                "blocked_outstanding_total": 118.0,
                "next_due_invoice_number": soft_hold["invoice_number"],
                "most_urgent_status": "DUE_IN_7_DAYS",
                "escalation_status": "OWNER_ESCALATION",
                "escalation_target": "tenant_owner",
                "next_action": "Owner follow-up before the next payment window",
            },
            {
                "dispute_id": stale_dispute.json()["id"],
                "supplier_id": stale_case["supplier_id"],
                "supplier_name": "Archive Traders",
                "reference_type": "goods_receipt",
                "reference_number": stale_case["goods_receipt_id"],
                "dispute_type": "MISSING_DOCS",
                "opened_on": "2026-03-20",
                "age_days": 24,
                "overdue": True,
                "hold_status": None,
                "blocked_release_now_total": 0.0,
                "blocked_release_this_week_total": 0.0,
                "blocked_outstanding_total": 0.0,
                "next_due_invoice_number": None,
                "most_urgent_status": None,
                "escalation_status": "STALE_CASE",
                "escalation_target": "tenant_owner",
                "next_action": "Escalate stale dispute and request supplier resolution date",
            },
            {
                "dispute_id": branch_dispute.json()["id"],
                "supplier_id": branch_follow_up["supplier_id"],
                "supplier_name": "Box Makers",
                "reference_type": "goods_receipt",
                "reference_number": branch_follow_up["goods_receipt_id"],
                "dispute_type": "DAMAGED_STOCK",
                "opened_on": "2026-04-12",
                "age_days": 1,
                "overdue": False,
                "hold_status": None,
                "blocked_release_now_total": 0.0,
                "blocked_release_this_week_total": 0.0,
                "blocked_outstanding_total": 0.0,
                "next_due_invoice_number": None,
                "most_urgent_status": None,
                "escalation_status": "BRANCH_FOLLOW_UP",
                "escalation_target": "store_manager",
                "next_action": "Branch follow-up and update dispute status",
            },
        ],
    }
