import asyncio
from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.models import GoodsReceipt, PurchaseInvoice, PurchaseOrder, SupplierPayment, VendorDispute


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _bootstrap_owner_context(client: TestClient) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-supplier-reporting"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200

    return {
        "tenant_id": tenant_id,
        "branch_id": branch.json()["id"],
        "owner_access_token": owner_session["access_token"],
    }


def _create_purchase_flow(
    client: TestClient,
    *,
    owner_headers: dict[str, str],
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
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": product_name,
            "sku_code": sku_code,
            "barcode": barcode,
            "hsn_sac_code": hsn_sac_code,
            "gst_rate": 18.0,
            "selling_price": unit_cost * 2,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    branch_catalog_item = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        json={"product_id": product_id, "selling_price_override": None, "availability_status": "ACTIVE"},
    )
    assert branch_catalog_item.status_code == 200

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": supplier_name, "gstin": supplier_gstin, "payment_terms_days": payment_terms_days},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={"supplier_id": supplier_id, "lines": [{"product_id": product_id, "quantity": quantity, "unit_cost": unit_cost}]},
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Ready for supplier reporting"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for supplier reporting"},
    )
    assert approved.status_code == 200

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200
    goods_receipt_id = goods_receipt.json()["id"]

    purchase_invoice = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices",
        headers=owner_headers,
        json={"goods_receipt_id": goods_receipt_id},
    )
    assert purchase_invoice.status_code == 200

    return {
        "product_id": product_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "purchase_order_id": purchase_order_id,
        "goods_receipt_id": goods_receipt_id,
        "goods_receipt_number": goods_receipt.json()["goods_receipt_number"],
        "purchase_invoice_id": purchase_invoice.json()["id"],
        "invoice_number": purchase_invoice.json()["invoice_number"],
    }


async def _rewrite_dates(
    client: TestClient,
    *,
    invoice_dates: dict[str, tuple[date, date]],
    payment_dates: dict[str, date],
    purchase_order_approved_dates: dict[str, datetime],
    goods_receipt_dates: dict[str, date],
    dispute_dates: dict[str, tuple[date, date | None]],
) -> None:
    async with client.app.state.session_factory() as session:
        for purchase_invoice_id, (invoice_date, due_date) in invoice_dates.items():
            purchase_invoice = await session.get(PurchaseInvoice, purchase_invoice_id)
            assert purchase_invoice is not None
            purchase_invoice.invoice_date = invoice_date
            purchase_invoice.due_date = due_date

        for supplier_payment_id, paid_on in payment_dates.items():
            supplier_payment = await session.get(SupplierPayment, supplier_payment_id)
            assert supplier_payment is not None
            supplier_payment.paid_on = paid_on

        for purchase_order_id, approved_at in purchase_order_approved_dates.items():
            purchase_order = await session.get(PurchaseOrder, purchase_order_id)
            assert purchase_order is not None
            purchase_order.approved_at = approved_at

        for goods_receipt_id, received_on in goods_receipt_dates.items():
            goods_receipt = await session.get(GoodsReceipt, goods_receipt_id)
            assert goods_receipt is not None
            goods_receipt.received_on = received_on

        for dispute_id, (opened_on, resolved_on) in dispute_dates.items():
            dispute = await session.get(VendorDispute, dispute_id)
            assert dispute is not None
            dispute.opened_on = opened_on
            dispute.resolved_on = resolved_on

        await session.commit()


def test_supplier_reporting_routes_cover_payables_aging_statements_due_schedule_and_vendor_board() -> None:
    database_url = sqlite_test_database_url("supplier-reporting-core")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_owner_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    paper_flow = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
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
    ink_flow = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
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
    tape_flow = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
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

    supplier_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_flow['purchase_invoice_id']}/supplier-returns",
        headers=owner_headers,
        json={"lines": [{"product_id": paper_flow["product_id"], "quantity": 1}]},
    )
    assert supplier_return.status_code == 200

    first_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{paper_flow['purchase_invoice_id']}/supplier-payments",
        headers=owner_headers,
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-AGING-001"},
    )
    assert first_payment.status_code == 200

    second_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{ink_flow['purchase_invoice_id']}/supplier-payments",
        headers=owner_headers,
        json={"amount": 50, "payment_method": "cash", "reference": "CASH-001"},
    )
    assert second_payment.status_code == 200

    open_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers=owner_headers,
        json={
            "goods_receipt_id": paper_flow["goods_receipt_id"],
            "dispute_type": "SHORT_SUPPLY",
            "note": "Two cartons missing",
        },
    )
    assert open_dispute.status_code == 200

    resolved_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers=owner_headers,
        json={
            "purchase_invoice_id": paper_flow["purchase_invoice_id"],
            "dispute_type": "RATE_MISMATCH",
            "note": "Invoice rate higher than agreed",
        },
    )
    assert resolved_dispute.status_code == 200

    resolved = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes/{resolved_dispute.json()['id']}/resolve",
        headers=owner_headers,
        json={"resolution_note": "Supplier issued corrected invoice"},
    )
    assert resolved.status_code == 200

    asyncio.run(
        _rewrite_dates(
            client,
                invoice_dates={
                    paper_flow["purchase_invoice_id"]: (date(2026, 2, 20), date(2026, 4, 10)),
                    ink_flow["purchase_invoice_id"]: (date(2026, 4, 13), date(2026, 4, 13)),
                    tape_flow["purchase_invoice_id"]: (date(2026, 4, 14), date(2026, 4, 21)),
                },
            payment_dates={
                first_payment.json()["id"]: date(2026, 4, 10),
                second_payment.json()["id"]: date(2026, 4, 11),
            },
            purchase_order_approved_dates={},
            goods_receipt_dates={},
            dispute_dates={
                open_dispute.json()["id"]: (date(2026, 4, 1), None),
                resolved_dispute.json()["id"]: (date(2026, 4, 10), date(2026, 4, 12)),
            },
        )
    )

    payables = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payables-report",
        headers=owner_headers,
    )
    assert payables.status_code == 200
    assert payables.json()["outstanding_total"] == 322.0
    assert payables.json()["records"][0]["supplier_name"] == "Paper Supply Co"
    assert payables.json()["records"][0]["outstanding_total"] == 195.0

    aging = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-aging-report",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert aging.status_code == 200
    assert aging.json()["open_invoice_count"] == 3
    assert aging.json()["days_31_60_total"] == 195.0
    assert aging.json()["records"][0]["aging_bucket"] == "31_60_DAYS"

    statements = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-statements",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert statements.status_code == 200
    assert statements.json()["supplier_count"] == 3
    assert statements.json()["open_supplier_count"] == 3
    assert statements.json()["records"][0]["supplier_name"] == "Paper Supply Co"

    due_schedule = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-due-schedule",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert due_schedule.status_code == 200
    assert due_schedule.json()["overdue_invoice_count"] == 1
    assert due_schedule.json()["overdue_total"] == 195.0
    assert due_schedule.json()["due_today_total"] == 68.0

    dispute_board = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-dispute-board",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert dispute_board.status_code == 200
    assert dispute_board.json()["open_count"] == 1
    assert dispute_board.json()["resolved_count"] == 1
    assert dispute_board.json()["records"][0]["supplier_name"] == "Paper Supply Co"
    assert dispute_board.json()["records"][0]["overdue"] is True

    exception_report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-exception-report",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert exception_report.status_code == 200
    assert exception_report.json()["suppliers_with_open_disputes"] == 1
    assert exception_report.json()["suppliers_with_overdue_disputes"] == 1
    assert exception_report.json()["records"][0]["status"] == "ATTENTION"


def test_supplier_reporting_routes_cover_settlement_blockers_escalations_performance_and_payment_activity() -> None:
    database_url = sqlite_test_database_url("supplier-reporting-ops")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_owner_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    hard_hold = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
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
    soft_hold = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
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
    branch_follow_up = _create_purchase_flow(
        client,
        owner_headers=owner_headers,
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
    )

    hard_return = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{hard_hold['purchase_invoice_id']}/supplier-returns",
        headers=owner_headers,
        json={"lines": [{"product_id": hard_hold["product_id"], "quantity": 1}]},
    )
    assert hard_return.status_code == 200

    first_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{hard_hold['purchase_invoice_id']}/supplier-payments",
        headers=owner_headers,
        json={"amount": 100, "payment_method": "bank_transfer", "reference": "UTR-HOLD-001"},
    )
    assert first_payment.status_code == 200

    second_payment = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/purchase-invoices/{soft_hold['purchase_invoice_id']}/supplier-payments",
        headers=owner_headers,
        json={"amount": 50, "payment_method": "cash", "reference": "CASH-001"},
    )
    assert second_payment.status_code == 200

    hard_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers=owner_headers,
        json={
            "purchase_invoice_id": hard_hold["purchase_invoice_id"],
            "dispute_type": "RATE_MISMATCH",
            "note": "Invoice does not match approved rate",
        },
    )
    assert hard_dispute.status_code == 200

    soft_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers=owner_headers,
        json={
            "purchase_invoice_id": soft_hold["purchase_invoice_id"],
            "dispute_type": "SHORT_SUPPLY",
            "note": "Short receipt waiting for vendor confirmation",
        },
    )
    assert soft_dispute.status_code == 200

    branch_dispute = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/vendor-disputes",
        headers=owner_headers,
        json={
            "goods_receipt_id": branch_follow_up["goods_receipt_id"],
            "dispute_type": "DAMAGED_STOCK",
            "note": "Boxes arrived dented",
        },
    )
    assert branch_dispute.status_code == 200

    asyncio.run(
        _rewrite_dates(
            client,
            invoice_dates={
                hard_hold["purchase_invoice_id"]: (date(2026, 3, 11), date(2026, 4, 10)),
                soft_hold["purchase_invoice_id"]: (date(2026, 4, 13), date(2026, 4, 20)),
                branch_follow_up["purchase_invoice_id"]: (date(2026, 4, 13), date(2026, 4, 20)),
            },
            payment_dates={
                first_payment.json()["id"]: date(2026, 4, 11),
                second_payment.json()["id"]: date(2026, 4, 12),
            },
            purchase_order_approved_dates={
                hard_hold["purchase_order_id"]: datetime(2026, 4, 1, 9, 0, 0),
                soft_hold["purchase_order_id"]: datetime(2026, 4, 1, 9, 0, 0),
                branch_follow_up["purchase_order_id"]: datetime(2026, 4, 1, 9, 0, 0),
            },
            goods_receipt_dates={
                hard_hold["goods_receipt_id"]: date(2026, 4, 2),
                soft_hold["goods_receipt_id"]: date(2026, 4, 6),
                branch_follow_up["goods_receipt_id"]: date(2026, 4, 2),
            },
            dispute_dates={
                hard_dispute.json()["id"]: (date(2026, 4, 1), None),
                soft_dispute.json()["id"]: (date(2026, 4, 11), None),
                branch_dispute.json()["id"]: (date(2026, 4, 12), None),
            },
        )
    )

    settlement_report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-settlement-report",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert settlement_report.status_code == 200
    assert settlement_report.json()["supplier_count"] == 3
    assert settlement_report.json()["records"][0]["supplier_name"] == "Paper Supply Co"

    settlement_blockers = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-settlement-blockers",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert settlement_blockers.status_code == 200
    assert settlement_blockers.json()["hard_hold_count"] == 1
    assert settlement_blockers.json()["soft_hold_count"] == 2
    assert settlement_blockers.json()["blocked_release_now_total"] == 195.0

    escalation_report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-escalation-report",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert escalation_report.status_code == 200
    assert escalation_report.json()["finance_escalation_count"] == 1
    assert escalation_report.json()["owner_escalation_count"] == 2
    assert escalation_report.json()["branch_follow_up_count"] == 0

    performance_report = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-performance-report",
        headers=owner_headers,
    )
    assert performance_report.status_code == 200
    assert performance_report.json()["supplier_count"] == 3
    assert performance_report.json()["records"][0]["performance_status"] == "AT_RISK"

    payment_activity = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/supplier-payment-activity",
        headers=owner_headers,
        params={"as_of_date": "2026-04-13"},
    )
    assert payment_activity.status_code == 200
    assert payment_activity.json()["payment_count"] == 2
    assert payment_activity.json()["recent_30_days_paid_total"] == 150.0
