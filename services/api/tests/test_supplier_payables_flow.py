from pathlib import Path

from fastapi.testclient import TestClient

from store_api.main import create_app


def _bootstrap_purchase_invoice(client: TestClient) -> dict[str, str]:
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
    branch_id = branch["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "selling_price": 100,
            "tax_rate_percent": 18,
            "hsn_sac_code": "4820",
        },
    ).json()

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co", "gstin": "29AAAAA1111A1Z5"},
    ).json()

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": supplier["id"],
            "lines": [{"product_id": product["id"], "quantity": 6, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for supplier settlement"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier settlement"},
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
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "product_id": product["id"],
        "purchase_invoice_id": purchase_invoice["id"],
    }


def test_supplier_payment_updates_payables_report_with_credit_notes_and_outstanding():
    client = TestClient(create_app())
    context = _bootstrap_purchase_invoice(client)

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{context['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": context["product_id"], "quantity": 1}]},
    )

    assert supplier_return.status_code == 200

    supplier_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{context['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 200, "payment_method": "bank_transfer", "reference": "UTR-001"},
    )

    assert supplier_payment.status_code == 200
    assert supplier_payment.json()["payment_number"] == "SPAY-2526-000001"
    assert supplier_payment.json()["amount"] == 200

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payables-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "invoiced_total": 354.0,
        "credit_note_total": 59.0,
        "paid_total": 200.0,
        "outstanding_total": 95.0,
        "records": [
            {
                "purchase_invoice_id": context["purchase_invoice_id"],
                "purchase_invoice_number": "SPINV-2526-000001",
                "supplier_name": "Paper Supply Co",
                "grand_total": 354.0,
                "credit_note_total": 59.0,
                "paid_total": 200.0,
                "outstanding_total": 95.0,
                "settlement_status": "PARTIALLY_SETTLED",
            }
        ],
    }


def test_supplier_payment_cannot_exceed_outstanding_amount():
    client = TestClient(create_app())
    context = _bootstrap_purchase_invoice(client)

    overpayment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{context['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 400, "payment_method": "bank_transfer"},
    )

    assert overpayment.status_code == 400
    assert overpayment.json()["detail"] == "Supplier payment exceeds outstanding amount"


def test_restart_preserves_supplier_payments_for_payables_reporting(tmp_path: Path):
    state_file = tmp_path / "store-api-state.json"
    first_client = TestClient(create_app(state_file=state_file))
    context = _bootstrap_purchase_invoice(first_client)

    payment = first_client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{context['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 200, "payment_method": "bank_transfer", "reference": "UTR-RESTART"},
    )

    assert payment.status_code == 200

    restarted_client = TestClient(create_app(state_file=state_file))
    report = restarted_client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payables-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json()["paid_total"] == 200.0
    assert report.json()["outstanding_total"] == 154.0


def test_supplier_aging_report_tracks_open_invoice_age_and_bucket():
    client = TestClient(create_app())
    context = _bootstrap_purchase_invoice(client)

    purchase_invoice = client.app.state.store_state.purchase_invoices[context["purchase_invoice_id"]]
    purchase_invoice["invoice_date"] = "2026-02-20"

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{context['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": context["product_id"], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    supplier_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{context['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-AGING-001"},
    )
    assert supplier_payment.status_code == 200

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-aging-report",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "open_invoice_count": 1,
        "current_total": 0.0,
        "days_1_30_total": 0.0,
        "days_31_60_total": 195.0,
        "days_61_plus_total": 0.0,
        "outstanding_total": 195.0,
        "records": [
            {
                "purchase_invoice_id": context["purchase_invoice_id"],
                "purchase_invoice_number": "SPINV-2526-000001",
                "supplier_name": "Paper Supply Co",
                "invoice_date": "2026-02-20",
                "invoice_age_days": 52,
                "grand_total": 354.0,
                "credit_note_total": 59.0,
                "paid_total": 100.0,
                "outstanding_total": 195.0,
                "aging_bucket": "31_60_DAYS",
            }
        ],
    }
