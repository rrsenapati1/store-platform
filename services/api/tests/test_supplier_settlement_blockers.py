from datetime import date

from store_api.supplier_settlement_blockers import build_supplier_settlement_blocker_report


def test_build_supplier_settlement_blocker_report_composes_payment_urgency_with_open_disputes():
    report = build_supplier_settlement_blocker_report(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
        purchase_invoices=[
            {
                "id": "pinv-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000001",
                "invoice_date": "2026-04-01",
                "payment_terms_days": 7,
                "grand_total": 236.0,
            },
            {
                "id": "pinv-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "invoice_number": "SPINV-2526-000002",
                "invoice_date": "2026-04-13",
                "payment_terms_days": 7,
                "grand_total": 118.0,
            },
            {
                "id": "pinv-3",
                "branch_id": "branch-1",
                "supplier_id": "supplier-3",
                "invoice_number": "SPINV-2526-000003",
                "invoice_date": "2026-04-13",
                "payment_terms_days": 0,
                "grand_total": 59.0,
            },
        ],
        supplier_returns=[],
        supplier_payments=[
            {
                "id": "spay-1",
                "branch_id": "branch-1",
                "purchase_invoice_id": "pinv-1",
                "supplier_id": "supplier-1",
                "amount": 100.0,
            }
        ],
        vendor_disputes=[
            {
                "id": "vdis-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "purchase_invoice_id": "pinv-1",
                "goods_receipt_id": None,
                "dispute_type": "RATE_MISMATCH",
                "status": "OPEN",
                "opened_on": "2026-04-01",
                "resolved_on": None,
            },
            {
                "id": "vdis-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "purchase_invoice_id": "pinv-2",
                "goods_receipt_id": None,
                "dispute_type": "SHORT_SUPPLY",
                "status": "OPEN",
                "opened_on": "2026-04-11",
                "resolved_on": None,
            },
        ],
        goods_receipts=[],
        suppliers_by_id={
            "supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"},
            "supplier-2": {"id": "supplier-2", "name": "Ink Wholesale"},
            "supplier-3": {"id": "supplier-3", "name": "Tape Traders"},
        },
    )

    assert report == {
        "branch_id": "branch-1",
        "as_of_date": "2026-04-13",
        "supplier_count": 2,
        "hard_hold_count": 1,
        "soft_hold_count": 1,
        "blocked_release_now_total": 136.0,
        "blocked_release_this_week_total": 254.0,
        "blocked_outstanding_total": 254.0,
        "records": [
            {
                "supplier_id": "supplier-1",
                "supplier_name": "Paper Supply Co",
                "hold_status": "HARD_HOLD",
                "open_dispute_count": 1,
                "overdue_open_dispute_count": 1,
                "latest_dispute_type": "RATE_MISMATCH",
                "latest_reference_type": "purchase_invoice",
                "latest_reference_number": "SPINV-2526-000001",
                "latest_opened_on": "2026-04-01",
                "outstanding_total": 136.0,
                "release_now_total": 136.0,
                "release_this_week_total": 136.0,
                "next_due_date": "2026-04-08",
                "next_due_invoice_number": "SPINV-2526-000001",
                "most_urgent_status": "OVERDUE",
            },
            {
                "supplier_id": "supplier-2",
                "supplier_name": "Ink Wholesale",
                "hold_status": "SOFT_HOLD",
                "open_dispute_count": 1,
                "overdue_open_dispute_count": 0,
                "latest_dispute_type": "SHORT_SUPPLY",
                "latest_reference_type": "purchase_invoice",
                "latest_reference_number": "SPINV-2526-000002",
                "latest_opened_on": "2026-04-11",
                "outstanding_total": 118.0,
                "release_now_total": 0.0,
                "release_this_week_total": 118.0,
                "next_due_date": "2026-04-20",
                "next_due_invoice_number": "SPINV-2526-000002",
                "most_urgent_status": "DUE_IN_7_DAYS",
            },
        ],
    }
