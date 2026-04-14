from fastapi.testclient import TestClient

from store_api.main import create_app


def _bootstrap_branch(client: TestClient, *, include_pen: bool = False) -> dict[str, object]:
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

    notebook = client.post(
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

    pen = None
    if include_pen:
        pen = client.post(
            f"/v1/tenants/{tenant_id}/products",
            headers={"x-actor-role": "catalog_admin"},
            json={
                "name": "Pen Pack",
                "sku_code": "SKU-002",
                "barcode": "8901234567891",
                "selling_price": 50,
                "tax_rate_percent": 18,
                "hsn_sac_code": "9608",
            },
        ).json()

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Paper Supply Co"},
    ).json()

    lines = [{"product_id": notebook["id"], "quantity": 6, "unit_cost": 50}]
    if pen:
        lines.append({"product_id": pen["id"], "quantity": 10, "unit_cost": 20})

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={"supplier_id": supplier["id"], "lines": lines},
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for branch bootstrap"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for branch bootstrap"},
    )

    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order["id"]},
    )

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "notebook": notebook,
        "pen": pen,
    }


def test_cash_session_tracks_sales_and_closing_variance():
    client = TestClient(create_app())
    context = _bootstrap_branch(client)

    cash_session = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/cash-sessions/open",
        headers={"x-actor-role": "store_manager"},
        json={"opening_float": 500},
    )

    assert cash_session.status_code == 200

    sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["notebook"]["id"], "quantity": 2}],
            "payment_amount": 236,
            "payment_method": "cash",
            "cash_session_id": cash_session.json()["id"],
        },
    )

    assert sale.status_code == 200

    closed = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/cash-sessions/{cash_session.json()['id']}/close",
        headers={"x-actor-role": "store_manager"},
        json={"closing_amount": 736},
    )

    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["cash_sales_total"] == 236
    assert closed.json()["expected_close_amount"] == 736
    assert closed.json()["variance_amount"] == 0


def test_sale_return_can_issue_credit_note_and_wait_for_refund_approval():
    client = TestClient(create_app())
    context = _bootstrap_branch(client)

    sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["notebook"]["id"], "quantity": 2}],
            "payment_amount": 236,
        },
    ).json()

    sale_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales/{sale['sale_id']}/returns",
        headers={"x-actor-role": "cashier"},
        json={"lines": [{"product_id": context["notebook"]["id"], "quantity": 1}], "refund_amount": 118},
    )

    assert sale_return.status_code == 200
    assert sale_return.json()["status"] == "REFUND_PENDING_APPROVAL"
    assert sale_return.json()["credit_note"]["credit_note_number"] == "SCN-2526-000001"
    assert sale_return.json()["credit_note"]["grand_total"] == 118

    approved = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sale-returns/{sale_return.json()['id']}/approve-refund",
        headers={"x-actor-role": "store_manager"},
        json={},
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "REFUND_APPROVED"


def test_exchange_order_balances_return_and_replacement_lines():
    client = TestClient(create_app())
    context = _bootstrap_branch(client, include_pen=True)

    sale = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales",
        headers={"x-actor-role": "cashier"},
        json={
            "customer_name": "Walk In",
            "lines": [{"product_id": context["notebook"]["id"], "quantity": 2}],
            "payment_amount": 236,
        },
    ).json()

    exchange = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/sales/{sale['sale_id']}/exchanges",
        headers={"x-actor-role": "cashier"},
        json={
            "return_lines": [{"product_id": context["notebook"]["id"], "quantity": 1}],
            "replacement_lines": [{"product_id": context["pen"]["id"], "quantity": 2}],
        },
    )

    assert exchange.status_code == 200
    assert exchange.json()["balance_direction"] == "EVEN"
    assert exchange.json()["balance_amount"] == 0
    assert exchange.json()["stock_effects"] == {
        "returned_products": [
            {
                "product_id": context["notebook"]["id"],
                "stock_after": 5,
            }
        ],
        "replacement_products": [
            {
                "product_id": context["pen"]["id"],
                "stock_after": 8,
            }
        ],
    }


def test_goods_receipt_can_be_converted_to_purchase_invoice_and_reported():
    client = TestClient(create_app())

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
        json={"note": "Ready for purchase invoice flow"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for purchase invoice flow"},
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
    )

    assert purchase_invoice.status_code == 200
    assert purchase_invoice.json()["invoice_number"] == "SPINV-2526-000001"
    assert purchase_invoice.json()["subtotal"] == 300
    assert purchase_invoice.json()["tax"] == {"cgst": 27, "sgst": 27, "igst": 0, "tax_total": 54}
    assert purchase_invoice.json()["grand_total"] == 354

    finance_history = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/finance-history",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert finance_history.status_code == 200
    assert finance_history.json() == {
        "branch_id": branch_id,
        "sales_invoice_total": 0,
        "purchase_invoice_total": 354,
        "customer_credit_note_total": 0,
        "supplier_credit_note_total": 0,
        "cash_variance_total": 0,
        "recent_documents": [
            {
                "document_type": "purchase_invoice",
                "document_number": "SPINV-2526-000001",
                "grand_total": 354,
            }
        ],
    }


def test_supplier_return_reduces_stock_and_updates_finance_history():
    client = TestClient(create_app())

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
        json={"note": "Ready for supplier return flow"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier return flow"},
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

    supplier_return = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice['id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": product["id"], "quantity": 2}]},
    )

    assert supplier_return.status_code == 200
    assert supplier_return.json()["supplier_credit_note_number"] == "SRCN-2526-000001"
    assert supplier_return.json()["grand_total"] == 118
    assert supplier_return.json()["lines"] == [
        {
            "product_id": product["id"],
            "quantity": 2,
            "stock_after_return": 4,
        }
    ]

    finance_history = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/finance-history",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert finance_history.status_code == 200
    assert finance_history.json()["purchase_invoice_total"] == 354
    assert finance_history.json()["supplier_credit_note_total"] == 118
