from store_api.vendor_billing import build_vendor_billing_board, ensure_purchase_invoice_not_already_created


def test_build_vendor_billing_board_splits_awaiting_and_invoiced_receipts():
    board = build_vendor_billing_board(
        branch_id="branch-1",
        goods_receipts=[
            {
                "id": "grn-1",
                "branch_id": "branch-1",
                "purchase_order_id": "po-1",
                "supplier_id": "supplier-1",
            },
            {
                "id": "grn-2",
                "branch_id": "branch-1",
                "purchase_order_id": "po-2",
                "supplier_id": "supplier-1",
            },
            {
                "id": "grn-3",
                "branch_id": "branch-2",
                "purchase_order_id": "po-3",
                "supplier_id": "supplier-1",
            },
        ],
        purchase_invoices=[
            {
                "id": "pinv-1",
                "goods_receipt_id": "grn-2",
                "invoice_number": "SPINV-2526-000001",
                "grand_total": 354.0,
            }
        ],
        suppliers_by_id={"supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"}},
    )

    assert board == {
        "branch_id": "branch-1",
        "awaiting_invoice_count": 1,
        "invoiced_count": 1,
        "records": [
            {
                "goods_receipt_id": "grn-1",
                "purchase_order_id": "po-1",
                "supplier_name": "Paper Supply Co",
                "billing_status": "AWAITING_INVOICE",
                "purchase_invoice_id": None,
                "purchase_invoice_number": None,
                "grand_total": None,
            },
            {
                "goods_receipt_id": "grn-2",
                "purchase_order_id": "po-2",
                "supplier_name": "Paper Supply Co",
                "billing_status": "INVOICED",
                "purchase_invoice_id": "pinv-1",
                "purchase_invoice_number": "SPINV-2526-000001",
                "grand_total": 354.0,
            },
        ],
    }


def test_ensure_purchase_invoice_not_already_created_raises_for_duplicate_goods_receipt():
    try:
        ensure_purchase_invoice_not_already_created(
            goods_receipt_id="grn-1",
            purchase_invoices=[
                {"id": "pinv-1", "goods_receipt_id": "grn-1"},
                {"id": "pinv-2", "goods_receipt_id": "grn-2"},
            ],
        )
    except ValueError as exc:
        assert str(exc) == "Purchase invoice already exists for goods receipt"
    else:
        raise AssertionError("Expected duplicate purchase invoice guard to raise")
