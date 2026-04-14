from store_api.receiving import build_receiving_board, ensure_goods_receipt_not_already_created


def test_receiving_board_counts_ready_blocked_and_received_orders():
    report = build_receiving_board(
        branch_id="branch-1",
        purchase_orders=[
            {"id": "po-ready", "branch_id": "branch-1", "supplier_id": "supplier-1", "approval_status": "APPROVED"},
            {"id": "po-blocked", "branch_id": "branch-1", "supplier_id": "supplier-1", "approval_status": "NOT_REQUESTED"},
            {"id": "po-received", "branch_id": "branch-1", "supplier_id": "supplier-1", "approval_status": "APPROVED"},
            {"id": "po-other", "branch_id": "branch-2", "supplier_id": "supplier-1", "approval_status": "APPROVED"},
        ],
        suppliers_by_id={"supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"}},
        goods_receipts=[
            {"id": "grn-1", "branch_id": "branch-1", "purchase_order_id": "po-received"},
            {"id": "grn-2", "branch_id": "branch-2", "purchase_order_id": "po-other"},
        ],
    )

    assert report == {
        "branch_id": "branch-1",
        "blocked_count": 1,
        "ready_count": 1,
        "received_count": 1,
        "records": [
            {
                "purchase_order_id": "po-ready",
                "supplier_name": "Paper Supply Co",
                "approval_status": "APPROVED",
                "receiving_status": "READY",
                "can_receive": True,
                "blocked_reason": None,
                "goods_receipt_id": None,
            },
            {
                "purchase_order_id": "po-blocked",
                "supplier_name": "Paper Supply Co",
                "approval_status": "NOT_REQUESTED",
                "receiving_status": "BLOCKED",
                "can_receive": False,
                "blocked_reason": "Approval not requested",
                "goods_receipt_id": None,
            },
            {
                "purchase_order_id": "po-received",
                "supplier_name": "Paper Supply Co",
                "approval_status": "APPROVED",
                "receiving_status": "RECEIVED",
                "can_receive": False,
                "blocked_reason": None,
                "goods_receipt_id": "grn-1",
            },
        ],
    }


def test_duplicate_goods_receipt_guard_blocks_repeat_receipt():
    try:
        ensure_goods_receipt_not_already_created(
            purchase_order_id="po-1",
            goods_receipts=[{"id": "grn-1", "purchase_order_id": "po-1"}],
        )
    except ValueError as exc:
        assert str(exc) == "Goods receipt already exists for purchase order"
    else:
        raise AssertionError("Expected duplicate goods receipt to be blocked")
