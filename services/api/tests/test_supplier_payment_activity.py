from datetime import date

from store_api.supplier_payment_activity import build_supplier_payment_activity_report


def test_build_supplier_payment_activity_report_groups_payment_history_by_supplier():
    report = build_supplier_payment_activity_report(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
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
        purchase_invoices=[
            {
                "id": "pinv-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000011",
                "grand_total": 354.0,
            },
            {
                "id": "pinv-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "invoice_number": "SPINV-2526-000012",
                "grand_total": 118.0,
            },
            {
                "id": "pinv-3",
                "branch_id": "branch-1",
                "supplier_id": "supplier-3",
                "invoice_number": "SPINV-2526-000013",
                "grand_total": 236.0,
            },
        ],
        supplier_returns=[
            {"id": "sret-1", "purchase_invoice_id": "pinv-1", "grand_total": 59.0},
        ],
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
        "payment_count": 3,
        "paid_total": 345.0,
        "recent_30_days_paid_total": 245.0,
        "records": [
            {
                "supplier_id": "supplier-1",
                "supplier_name": "Paper Supply Co",
                "payment_count": 2,
                "paid_total": 295.0,
                "recent_30_days_paid_total": 195.0,
                "average_payment_value": 147.5,
                "outstanding_total": 0.0,
                "last_payment_date": "2026-04-12",
                "last_payment_number": "SPAY-2526-000002",
                "last_payment_method": "upi",
                "last_payment_reference": "UPI-001",
                "last_payment_amount": 195.0,
            },
            {
                "supplier_id": "supplier-2",
                "supplier_name": "Ink Wholesale",
                "payment_count": 1,
                "paid_total": 50.0,
                "recent_30_days_paid_total": 50.0,
                "average_payment_value": 50.0,
                "outstanding_total": 68.0,
                "last_payment_date": "2026-04-11",
                "last_payment_number": "SPAY-2526-000003",
                "last_payment_method": "cash",
                "last_payment_reference": "CASH-001",
                "last_payment_amount": 50.0,
            },
        ],
    }
