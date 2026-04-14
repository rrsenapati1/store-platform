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
        json={"note": "Ready for supplier statement"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier statement"},
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


def test_supplier_statement_report_rolls_up_supplier_exposure():
    client = TestClient(create_app())
    first_context = _bootstrap_purchase_invoice(client)
    first_invoice = client.app.state.store_state.purchase_invoices[first_context["purchase_invoice_id"]]
    first_invoice["invoice_date"] = "2026-02-20"

    supplier_return = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-invoices/{first_context['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": first_context["product_id"], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    supplier_payment = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-invoices/{first_context['purchase_invoice_id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-STMT-001"},
    )
    assert supplier_payment.status_code == 200

    second_supplier = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Ink Wholesale", "gstin": "29BBBBB2222B1Z5"},
    ).json()
    second_product = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Marker Pen",
            "sku_code": "SKU-002",
            "barcode": "8901234567891",
            "selling_price": 50,
            "tax_rate_percent": 18,
            "hsn_sac_code": "9608",
        },
    ).json()
    second_po = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "supplier_id": second_supplier["id"],
            "lines": [{"product_id": second_product["id"], "quantity": 2, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-orders/{second_po['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for supplier statement test"},
    )
    client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-orders/{second_po['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier statement test"},
    )
    second_grn = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": second_po["id"]},
    ).json()
    second_invoice = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-invoices",
        headers={"x-actor-role": "inventory_admin"},
        json={"goods_receipt_id": second_grn["id"]},
    ).json()
    client.app.state.store_state.purchase_invoices[second_invoice["id"]]["invoice_date"] = "2026-04-01"
    second_payment = client.post(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/purchase-invoices/{second_invoice['id']}/supplier-payments",
        headers={"x-actor-role": "inventory_admin"},
        json={"amount": 118, "payment_method": "bank_transfer", "reference": "UTR-STMT-002"},
    )
    assert second_payment.status_code == 200

    report = client.get(
        f"/v1/tenants/{first_context['tenant_id']}/branches/{first_context['branch_id']}/supplier-statements",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": first_context["branch_id"],
        "as_of_date": "2026-04-13",
        "supplier_count": 2,
        "open_supplier_count": 1,
        "outstanding_total": 195.0,
        "records": [
            {
                "supplier_id": client.app.state.store_state.purchase_invoices[first_context["purchase_invoice_id"]]["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "invoice_count": 1,
                "open_invoice_count": 1,
                "invoiced_total": 354.0,
                "credit_note_total": 59.0,
                "paid_total": 100.0,
                "outstanding_total": 195.0,
                "current_total": 0.0,
                "days_1_30_total": 0.0,
                "days_31_60_total": 195.0,
                "days_61_plus_total": 0.0,
                "oldest_open_invoice_date": "2026-02-20",
                "oldest_open_invoice_number": "SPINV-2526-000001",
            },
            {
                "supplier_id": second_supplier["id"],
                "supplier_name": "Ink Wholesale",
                "invoice_count": 1,
                "open_invoice_count": 0,
                "invoiced_total": 118.0,
                "credit_note_total": 0.0,
                "paid_total": 118.0,
                "outstanding_total": 0.0,
                "current_total": 0.0,
                "days_1_30_total": 0.0,
                "days_31_60_total": 0.0,
                "days_61_plus_total": 0.0,
                "oldest_open_invoice_date": None,
                "oldest_open_invoice_number": None,
            },
        ],
    }
