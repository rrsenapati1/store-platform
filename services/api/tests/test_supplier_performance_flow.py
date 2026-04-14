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


def _create_purchase_flow(
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
) -> dict[str, str]:
    product = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": product_name,
            "sku_code": sku_code,
            "barcode": barcode,
            "selling_price": 100,
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
            "lines": [{"product_id": product["id"], "quantity": 5, "unit_cost": 50}],
        },
    ).json()
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready for supplier performance"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for supplier performance"},
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
        "purchase_order_id": purchase_order["id"],
        "goods_receipt_id": goods_receipt["id"],
        "purchase_invoice_id": purchase_invoice["id"],
    }


def test_supplier_performance_report_summarizes_delivery_mismatch_and_returns():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    strong_flow = _create_purchase_flow(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Notebook",
        sku_code="SKU-001",
        barcode="8901234567890",
        hsn_sac_code="4820",
        supplier_name="Paper Supply Co",
        supplier_gstin="29AAAAA1111A1Z5",
    )
    risk_flow = _create_purchase_flow(
        client,
        tenant_id=context["tenant_id"],
        branch_id=context["branch_id"],
        product_name="Marker Pen",
        sku_code="SKU-002",
        barcode="8901234567891",
        hsn_sac_code="9608",
        supplier_name="Ink Wholesale",
        supplier_gstin="29BBBBB2222B1Z5",
    )

    dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "purchase_invoice_id": risk_flow["purchase_invoice_id"],
            "dispute_type": "RATE_MISMATCH",
            "note": "Invoice rate higher than agreed",
        },
    )
    assert dispute.status_code == 200

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{risk_flow['purchase_invoice_id']}/supplier-returns",
        headers={"x-actor-role": "inventory_admin"},
        json={"lines": [{"product_id": risk_flow["product_id"], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    state = client.app.state.store_state
    state.purchase_orders[strong_flow["purchase_order_id"]]["approved_on"] = "2026-04-01"
    state.goods_receipts[strong_flow["goods_receipt_id"]]["received_on"] = "2026-04-02"
    state.purchase_orders[risk_flow["purchase_order_id"]]["approved_on"] = "2026-04-01"
    state.goods_receipts[risk_flow["goods_receipt_id"]]["received_on"] = "2026-04-06"

    report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-performance-report",
        headers={"x-actor-role": "tenant_owner"},
    )

    assert report.status_code == 200
    assert report.json() == {
        "branch_id": context["branch_id"],
        "supplier_count": 2,
        "strong_count": 1,
        "watch_count": 0,
        "at_risk_count": 1,
        "records": [
            {
                "supplier_id": risk_flow["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "approved_purchase_order_count": 1,
                "received_purchase_order_count": 1,
                "on_time_receipt_count": 0,
                "on_time_receipt_rate": 0.0,
                "average_receipt_delay_days": 5.0,
                "purchase_invoice_count": 1,
                "invoice_mismatch_count": 1,
                "invoice_mismatch_rate": 1.0,
                "supplier_return_count": 1,
                "supplier_return_rate": 1.0,
                "performance_status": "AT_RISK",
            },
            {
                "supplier_id": strong_flow["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "approved_purchase_order_count": 1,
                "received_purchase_order_count": 1,
                "on_time_receipt_count": 1,
                "on_time_receipt_rate": 1.0,
                "average_receipt_delay_days": 1.0,
                "purchase_invoice_count": 1,
                "invoice_mismatch_count": 0,
                "invoice_mismatch_rate": 0.0,
                "supplier_return_count": 0,
                "supplier_return_rate": 0.0,
                "performance_status": "STRONG",
            },
        ],
    }
