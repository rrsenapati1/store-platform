from datetime import date

from store_api.supplier_settlement import build_supplier_settlement_report


def test_build_supplier_settlement_report_tracks_overdue_and_recent_payment_activity():
    report = build_supplier_settlement_report(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
        purchase_invoices=[
            {
                "id": "pinv-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000011",
                "grand_total": 354.0,
                "invoice_date": "2026-03-01",
                "due_date": "2026-04-10",
            },
            {
                "id": "pinv-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "invoice_number": "SPINV-2526-000012",
                "grand_total": 118.0,
                "invoice_date": "2026-04-01",
                "due_date": "2026-04-15",
            },
        ],
        supplier_returns=[{"id": "sret-1", "purchase_invoice_id": "pinv-1", "grand_total": 59.0}],
        supplier_payments=[
            {
                "id": "spay-1",
                "branch_id": "branch-1",
                "purchase_invoice_id": "pinv-1",
                "supplier_id": "supplier-1",
                "payment_number": "SPAY-2526-000001",
                "payment_date": "2026-03-15",
                "payment_method": "bank_transfer",
                "reference": "UTR-001",
                "amount": 100.0,
            },
            {
                "id": "spay-2",
                "branch_id": "branch-1",
                "purchase_invoice_id": "pinv-1",
                "supplier_id": "supplier-1",
                "payment_number": "SPAY-2526-000002",
                "payment_date": "2026-04-12",
                "payment_method": "upi",
                "reference": "UPI-001",
                "amount": 195.0,
            },
            {
                "id": "spay-3",
                "branch_id": "branch-1",
                "purchase_invoice_id": "pinv-2",
                "supplier_id": "supplier-2",
                "payment_number": "SPAY-2526-000003",
                "payment_date": "2026-04-11",
                "payment_method": "cash",
                "reference": "CASH-001",
                "amount": 50.0,
            },
        ],
        suppliers_by_id={
            "supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"},
            "supplier-2": {"id": "supplier-2", "name": "Ink Wholesale"},
        },
    )

    assert report == {
        "branch_id": "branch-1",
        "as_of_date": "2026-04-13",
        "supplier_count": 1,
        "overdue_total": 0.0,
        "due_in_7_days_total": 68.0,
        "outstanding_total": 68.0,
        "records": [
            {
                "supplier_id": "supplier-2",
                "supplier_name": "Ink Wholesale",
                "outstanding_total": 68.0,
                "overdue_total": 0.0,
                "due_in_7_days_total": 68.0,
                "latest_payment_date": "2026-04-11",
                "latest_payment_number": "SPAY-2526-000003",
                "latest_payment_method": "cash",
                "latest_payment_reference": "CASH-001",
                "latest_payment_amount": 50.0,
                "days_since_last_payment": 2,
                "risk_status": "WATCH",
            }
        ],
    }
