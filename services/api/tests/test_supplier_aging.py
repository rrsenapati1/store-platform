from datetime import date

from store_api.supplier_aging import build_supplier_aging_report


def test_build_supplier_aging_report_groups_open_payables_into_age_buckets():
    report = build_supplier_aging_report(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
        purchase_invoices=[
            {
                "id": "pinv-current",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000001",
                "invoice_date": "2026-04-13",
                "grand_total": 118.0,
            },
            {
                "id": "pinv-aged",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000002",
                "invoice_date": "2026-02-20",
                "grand_total": 354.0,
            },
            {
                "id": "pinv-settled",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000003",
                "invoice_date": "2026-01-10",
                "grand_total": 150.0,
            },
        ],
        supplier_returns=[
            {
                "id": "sret-1",
                "purchase_invoice_id": "pinv-aged",
                "grand_total": 59.0,
            }
        ],
        supplier_payments=[
            {
                "id": "spay-1",
                "purchase_invoice_id": "pinv-aged",
                "amount": 100.0,
            },
            {
                "id": "spay-2",
                "purchase_invoice_id": "pinv-settled",
                "amount": 150.0,
            },
        ],
        suppliers_by_id={"supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"}},
    )

    assert report == {
        "branch_id": "branch-1",
        "as_of_date": "2026-04-13",
        "open_invoice_count": 2,
        "current_total": 118.0,
        "days_1_30_total": 0.0,
        "days_31_60_total": 195.0,
        "days_61_plus_total": 0.0,
        "outstanding_total": 313.0,
        "records": [
            {
                "purchase_invoice_id": "pinv-aged",
                "purchase_invoice_number": "SPINV-2526-000002",
                "supplier_name": "Paper Supply Co",
                "invoice_date": "2026-02-20",
                "invoice_age_days": 52,
                "grand_total": 354.0,
                "credit_note_total": 59.0,
                "paid_total": 100.0,
                "outstanding_total": 195.0,
                "aging_bucket": "31_60_DAYS",
            },
            {
                "purchase_invoice_id": "pinv-current",
                "purchase_invoice_number": "SPINV-2526-000001",
                "supplier_name": "Paper Supply Co",
                "invoice_date": "2026-04-13",
                "invoice_age_days": 0,
                "grand_total": 118.0,
                "credit_note_total": 0.0,
                "paid_total": 0.0,
                "outstanding_total": 118.0,
                "aging_bucket": "CURRENT",
            },
        ],
    }
