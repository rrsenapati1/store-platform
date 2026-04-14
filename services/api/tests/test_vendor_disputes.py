from datetime import date

from store_api.vendor_disputes import build_vendor_dispute_board


def test_build_vendor_dispute_board_groups_open_and_resolved_cases():
    board = build_vendor_dispute_board(
        branch_id="branch-1",
        as_of_date=date(2026, 4, 13),
        vendor_disputes=[
            {
                "id": "vdis-1",
                "tenant_id": "tenant-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "goods_receipt_id": "grn-1",
                "purchase_invoice_id": None,
                "dispute_type": "SHORT_SUPPLY",
                "note": "Two cartons missing",
                "status": "OPEN",
                "opened_on": "2026-04-01",
                "resolved_on": None,
                "resolution_note": None,
            },
            {
                "id": "vdis-2",
                "tenant_id": "tenant-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "goods_receipt_id": None,
                "purchase_invoice_id": "pinv-2",
                "dispute_type": "RATE_MISMATCH",
                "note": "Invoice rate higher than PO",
                "status": "RESOLVED",
                "opened_on": "2026-04-10",
                "resolved_on": "2026-04-12",
                "resolution_note": "Supplier issued corrected invoice",
            },
        ],
        goods_receipts=[
            {"id": "grn-1", "branch_id": "branch-1", "supplier_id": "supplier-1"},
        ],
        purchase_invoices=[
            {
                "id": "pinv-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "invoice_number": "SPINV-2526-000022",
            }
        ],
        suppliers_by_id={
            "supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"},
            "supplier-2": {"id": "supplier-2", "name": "Ink Wholesale"},
        },
    )

    assert board == {
        "branch_id": "branch-1",
        "as_of_date": "2026-04-13",
        "open_count": 1,
        "resolved_count": 1,
        "overdue_open_count": 1,
        "records": [
            {
                "dispute_id": "vdis-1",
                "supplier_id": "supplier-1",
                "supplier_name": "Paper Supply Co",
                "reference_type": "goods_receipt",
                "reference_number": "grn-1",
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
                "dispute_id": "vdis-2",
                "supplier_id": "supplier-2",
                "supplier_name": "Ink Wholesale",
                "reference_type": "purchase_invoice",
                "reference_number": "SPINV-2526-000022",
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
