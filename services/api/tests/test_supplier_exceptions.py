from datetime import date

from store_api.supplier_exceptions import build_supplier_exception_report


def test_build_supplier_exception_report_groups_disputes_by_supplier():
    report = build_supplier_exception_report(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
        vendor_disputes=[
            {
                "id": "vdis-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "goods_receipt_id": "grn-1",
                "purchase_invoice_id": None,
                "dispute_type": "SHORT_SUPPLY",
                "status": "OPEN",
                "opened_on": "2026-04-01",
                "resolved_on": None,
            },
            {
                "id": "vdis-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "goods_receipt_id": None,
                "purchase_invoice_id": "pinv-1",
                "dispute_type": "RATE_MISMATCH",
                "status": "RESOLVED",
                "opened_on": "2026-04-10",
                "resolved_on": "2026-04-12",
            },
            {
                "id": "vdis-3",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "goods_receipt_id": None,
                "purchase_invoice_id": "pinv-2",
                "dispute_type": "RATE_MISMATCH",
                "status": "OPEN",
                "opened_on": "2026-04-11",
                "resolved_on": None,
            },
        ],
        goods_receipts=[
            {"id": "grn-1", "branch_id": "branch-1"},
        ],
        purchase_invoices=[
            {"id": "pinv-1", "branch_id": "branch-1", "invoice_number": "SPINV-2526-000021"},
            {"id": "pinv-2", "branch_id": "branch-1", "invoice_number": "SPINV-2526-000022"},
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
        "suppliers_with_open_disputes": 2,
        "suppliers_with_overdue_disputes": 1,
        "records": [
            {
                "supplier_id": "supplier-1",
                "supplier_name": "Paper Supply Co",
                "dispute_count": 2,
                "open_count": 1,
                "resolved_count": 1,
                "overdue_open_count": 1,
                "latest_dispute_type": "RATE_MISMATCH",
                "latest_reference_type": "purchase_invoice",
                "latest_reference_number": "SPINV-2526-000021",
                "latest_opened_on": "2026-04-10",
                "status": "ATTENTION",
            },
            {
                "supplier_id": "supplier-2",
                "supplier_name": "Ink Wholesale",
                "dispute_count": 1,
                "open_count": 1,
                "resolved_count": 0,
                "overdue_open_count": 0,
                "latest_dispute_type": "RATE_MISMATCH",
                "latest_reference_type": "purchase_invoice",
                "latest_reference_number": "SPINV-2526-000022",
                "latest_opened_on": "2026-04-11",
                "status": "OPEN",
            },
        ],
    }
