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
        json={"note": "Ready for dispute tracking"},
    )
    client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order['id']}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved for dispute tracking"},
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


def test_vendor_dispute_board_tracks_open_and_resolved_cases():
    client = TestClient(create_app())
    context = _create_tenant_branch(client)

    paper_flow = _create_purchase_invoice(
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
    ink_flow = _create_purchase_invoice(
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

    open_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "goods_receipt_id": paper_flow["goods_receipt_id"],
            "dispute_type": "SHORT_SUPPLY",
            "note": "Two cartons missing",
        },
    )
    assert open_dispute.status_code == 200

    resolved_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "purchase_invoice_id": ink_flow["purchase_invoice_id"],
            "dispute_type": "RATE_MISMATCH",
            "note": "Invoice rate higher than PO",
        },
    )
    assert resolved_dispute.status_code == 200

    resolved = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes/{resolved_dispute.json()['id']}/resolve",
        headers={"x-actor-role": "inventory_admin"},
        json={"resolution_note": "Supplier issued corrected invoice"},
    )
    assert resolved.status_code == 200

    state = client.app.state.store_state
    state.vendor_disputes[open_dispute.json()["id"]]["opened_on"] = "2026-04-01"
    state.vendor_disputes[resolved_dispute.json()["id"]]["opened_on"] = "2026-04-10"
    state.vendor_disputes[resolved_dispute.json()["id"]]["resolved_on"] = "2026-04-12"

    board = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-dispute-board",
        headers={"x-actor-role": "tenant_owner"},
        params={"as_of_date": "2026-04-13"},
    )

    assert board.status_code == 200
    assert board.json() == {
        "branch_id": context["branch_id"],
        "as_of_date": "2026-04-13",
        "open_count": 1,
        "resolved_count": 1,
        "overdue_open_count": 1,
        "records": [
            {
                "dispute_id": open_dispute.json()["id"],
                "supplier_id": paper_flow["supplier_id"],
                "supplier_name": "Paper Supply Co",
                "reference_type": "goods_receipt",
                "reference_number": paper_flow["goods_receipt_id"],
                "dispute_type": "SHORT_SUPPLY",
                "status": "OPEN",
                "opened_on": "2026-04-01",
                "resolved_on": None,
                "age_days": 12,
                "overdue": True,
                "note": "Two cartons missing",
                "resolution_note": None,
            },
            {
                "dispute_id": resolved_dispute.json()["id"],
                "supplier_id": ink_flow["supplier_id"],
                "supplier_name": "Ink Wholesale",
                "reference_type": "purchase_invoice",
                "reference_number": ink_flow["invoice_number"],
                "dispute_type": "RATE_MISMATCH",
                "status": "RESOLVED",
                "opened_on": "2026-04-10",
                "resolved_on": "2026-04-12",
                "age_days": 3,
                "overdue": False,
                "note": "Invoice rate higher than PO",
                "resolution_note": "Supplier issued corrected invoice",
            },
        ],
    }
