from datetime import date

from store_api.supplier_statements import build_supplier_statement_report


def test_build_supplier_statement_report_rolls_up_exposure_per_supplier():
    report = build_supplier_statement_report(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
        purchase_invoices=[
            {
                "id": "pinv-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000001",
                "invoice_date": "2026-04-01",
                "grand_total": 236.0,
            },
            {
                "id": "pinv-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000002",
                "invoice_date": "2026-02-20",
                "grand_total": 354.0,
            },
            {
                "id": "pinv-3",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "invoice_number": "SPINV-2526-000003",
                "invoice_date": "2026-01-10",
                "grand_total": 118.0,
            },
        ],
        supplier_returns=[
            {"id": "sret-1", "purchase_invoice_id": "pinv-2", "grand_total": 59.0},
        ],
        supplier_payments=[
            {"id": "spay-1", "purchase_invoice_id": "pinv-1", "amount": 100.0},
            {"id": "spay-2", "purchase_invoice_id": "pinv-2", "amount": 100.0},
            {"id": "spay-3", "purchase_invoice_id": "pinv-3", "amount": 118.0},
        ],
        suppliers_by_id={
            "supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"},
            "supplier-2": {"id": "supplier-2", "name": "Ink Wholesale"},
        },
    )

    assert report == {
        "branch_id": "branch-1",
        "as_of_date": "2026-04-13",
        "supplier_count": 2,
        "open_supplier_count": 1,
        "outstanding_total": 331.0,
        "records": [
            {
                "supplier_id": "supplier-1",
                "supplier_name": "Paper Supply Co",
                "invoice_count": 2,
                "open_invoice_count": 2,
                "invoiced_total": 590.0,
                "credit_note_total": 59.0,
                "paid_total": 200.0,
                "outstanding_total": 331.0,
                "current_total": 0.0,
                "days_1_30_total": 136.0,
                "days_31_60_total": 195.0,
                "days_61_plus_total": 0.0,
                "oldest_open_invoice_date": "2026-02-20",
                "oldest_open_invoice_number": "SPINV-2526-000002",
            },
            {
                "supplier_id": "supplier-2",
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
