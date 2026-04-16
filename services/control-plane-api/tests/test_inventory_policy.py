from store_control_plane.services.inventory_policy import (
    build_goods_receipt_lines,
    build_inventory_snapshot,
    build_replenishment_board,
    build_restock_board,
    build_receiving_board,
    build_stock_count_board,
    build_stock_count_result,
    ensure_restock_task_cancelable,
    ensure_restock_task_completable,
    ensure_restock_task_creatable,
    ensure_restock_task_pickable,
    ensure_stock_count_review_approvable,
    ensure_stock_count_review_cancelable,
    ensure_stock_count_review_recordable,
    build_transfer_board,
    ensure_purchase_order_receivable,
    ensure_stock_adjustment_allowed,
    ensure_transfer_allowed,
    goods_receipt_number,
    restock_task_number,
    transfer_number,
)


def test_goods_receipt_number_normalizes_branch_code():
    assert goods_receipt_number(branch_code="blr-flagship", sequence_number=1) == "GRN-BLRFLAGSHIP-0001"


def test_receiving_policy_marks_approved_orders_ready_and_received_orders_closed():
    purchase_orders = [
        {
            "purchase_order_id": "po-1",
            "purchase_order_number": "PO-BLRFLAGSHIP-0001",
            "supplier_id": "supplier-1",
            "approval_status": "APPROVED",
        },
        {
            "purchase_order_id": "po-2",
            "purchase_order_number": "PO-BLRFLAGSHIP-0002",
            "supplier_id": "supplier-1",
            "approval_status": "PENDING_APPROVAL",
        },
    ]
    report = build_receiving_board(
        branch_id="branch-1",
        purchase_orders=purchase_orders,
        suppliers_by_id={"supplier-1": {"name": "Acme Tea Traders"}},
        goods_receipts=[
            {
                "goods_receipt_id": "grn-1",
                "purchase_order_id": "po-1",
                "has_discrepancy": False,
            }
        ],
    )

    assert report["received_count"] == 1
    assert report["received_with_variance_count"] == 0
    assert report["blocked_count"] == 1
    assert report["records"][0]["receiving_status"] == "BLOCKED"
    assert report["records"][1]["goods_receipt_id"] == "grn-1"


def test_receiving_policy_marks_discrepant_receipts_separately():
    report = build_receiving_board(
        branch_id="branch-1",
        purchase_orders=[
            {
                "purchase_order_id": "po-1",
                "purchase_order_number": "PO-BLRFLAGSHIP-0001",
                "supplier_id": "supplier-1",
                "approval_status": "APPROVED",
            }
        ],
        suppliers_by_id={"supplier-1": {"name": "Acme Tea Traders"}},
        goods_receipts=[
            {
                "goods_receipt_id": "grn-1",
                "purchase_order_id": "po-1",
                "has_discrepancy": True,
                "variance_quantity": 4.0,
            }
        ],
    )

    assert report["received_count"] == 1
    assert report["received_with_variance_count"] == 1
    assert report["records"][0]["receiving_status"] == "RECEIVED_WITH_VARIANCE"
    assert report["records"][0]["has_discrepancy"] is True
    assert report["records"][0]["variance_quantity"] == 4.0


def test_purchase_order_receivable_requires_approval_and_missing_receipt():
    approved_order = type("PurchaseOrder", (), {"approval_status": "APPROVED"})()
    pending_order = type("PurchaseOrder", (), {"approval_status": "PENDING_APPROVAL"})()

    ensure_purchase_order_receivable(purchase_order=approved_order, existing_goods_receipt=None)

    try:
        ensure_purchase_order_receivable(purchase_order=pending_order, existing_goods_receipt=None)
    except ValueError as error:
        assert str(error) == "Purchase order must be approved before receiving"
    else:
        raise AssertionError("Expected pending purchase order to be blocked from receiving")

    try:
        ensure_purchase_order_receivable(purchase_order=approved_order, existing_goods_receipt={"goods_receipt_id": "grn-1"})
    except ValueError as error:
        assert str(error) == "Goods receipt already exists for purchase order"
    else:
        raise AssertionError("Expected duplicate goods receipt to be blocked")


def test_reviewed_goods_receipt_lines_support_partial_receipt_and_variance():
    purchase_order_lines = [
        type("PurchaseOrderLine", (), {"product_id": "product-1", "quantity": 24.0, "unit_cost": 61.5})(),
        type("PurchaseOrderLine", (), {"product_id": "product-2", "quantity": 10.0, "unit_cost": 12.0})(),
    ]
    products_by_id = {
        "product-1": type("Product", (), {"name": "Classic Tea", "sku_code": "tea-classic-250g"})(),
        "product-2": type("Product", (), {"name": "Ginger Tea", "sku_code": "tea-ginger-100g"})(),
    }

    lines = build_goods_receipt_lines(
        purchase_order_lines=purchase_order_lines,
        reviewed_lines=[
            {"product_id": "product-1", "received_quantity": 20.0, "discrepancy_note": "Four cartons short"},
            {"product_id": "product-2", "received_quantity": 0.0, "discrepancy_note": "Held back by supplier"},
        ],
        products_by_id=products_by_id,
    )

    assert lines[0].ordered_quantity == 24.0
    assert lines[0].quantity == 20.0
    assert lines[0].variance_quantity == 4.0
    assert lines[0].discrepancy_note == "Four cartons short"
    assert lines[1].ordered_quantity == 10.0
    assert lines[1].quantity == 0.0
    assert lines[1].variance_quantity == 10.0


def test_reviewed_goods_receipt_lines_reject_invalid_review_payloads():
    purchase_order_lines = [
        type("PurchaseOrderLine", (), {"product_id": "product-1", "quantity": 24.0, "unit_cost": 61.5})(),
    ]
    products_by_id = {
        "product-1": type("Product", (), {"name": "Classic Tea", "sku_code": "tea-classic-250g"})(),
    }

    for reviewed_lines, message in [
        ([{"product_id": "product-1", "received_quantity": -1.0}], "Received quantity must not be negative"),
        ([{"product_id": "product-1", "received_quantity": 25.0}], "Received quantity exceeds ordered quantity"),
        ([{"product_id": "product-2", "received_quantity": 1.0}], "Reviewed receipt lines must match purchase order lines"),
        ([{"product_id": "product-1", "received_quantity": 0.0}], "Goods receipt must include at least one received quantity"),
    ]:
        try:
            build_goods_receipt_lines(
                purchase_order_lines=purchase_order_lines,
                reviewed_lines=reviewed_lines,
                products_by_id=products_by_id,
            )
        except ValueError as error:
            assert str(error) == message
        else:
            raise AssertionError(f"Expected reviewed goods receipt validation failure: {message}")


def test_inventory_snapshot_rolls_up_ledger_entries_per_product():
    report = build_inventory_snapshot(
        branch_id="branch-1",
        inventory_ledger=[
            {
                "inventory_ledger_entry_id": "ledger-1",
                "branch_id": "branch-1",
                "product_id": "product-1",
                "entry_type": "PURCHASE_RECEIPT",
                "quantity": 24,
            },
            {
                "inventory_ledger_entry_id": "ledger-2",
                "branch_id": "branch-1",
                "product_id": "product-1",
                "entry_type": "ADJUSTMENT",
                "quantity": -4,
            },
        ],
        products_by_id={
            "product-1": {
                "product_id": "product-1",
                "product_name": "Classic Tea",
                "sku_code": "tea-classic-250g",
            }
        },
    )

    assert report["records"][0]["stock_on_hand"] == 20.0
    assert report["records"][0]["last_entry_type"] == "ADJUSTMENT"


def test_replenishment_board_builds_low_stock_suggestions_from_branch_policy():
    report = build_replenishment_board(
        branch_id="branch-1",
        branch_catalog_items=[
            {
                "product_id": "product-1",
                "product_name": "Classic Tea",
                "sku_code": "tea-classic-250g",
                "availability_status": "ACTIVE",
                "reorder_point": 10.0,
                "target_stock": 24.0,
            },
            {
                "product_id": "product-2",
                "product_name": "Ginger Tea",
                "sku_code": "tea-ginger-100g",
                "availability_status": "ACTIVE",
                "reorder_point": 6.0,
                "target_stock": 12.0,
            },
            {
                "product_id": "product-3",
                "product_name": "Mint Tea",
                "sku_code": "tea-mint-100g",
                "availability_status": "INACTIVE",
                "reorder_point": 4.0,
                "target_stock": 10.0,
            },
            {
                "product_id": "product-4",
                "product_name": "Masala Tea",
                "sku_code": "tea-masala-100g",
                "availability_status": "ACTIVE",
                "reorder_point": None,
                "target_stock": None,
            },
        ],
        stock_by_product_id={
            "product-1": 8.0,
            "product-2": 7.0,
            "product-3": 2.0,
        },
    )

    assert report["low_stock_count"] == 1
    assert report["adequate_count"] == 1
    assert len(report["records"]) == 2
    assert report["records"][0] == {
        "product_id": "product-1",
        "product_name": "Classic Tea",
        "sku_code": "tea-classic-250g",
        "availability_status": "ACTIVE",
        "stock_on_hand": 8.0,
        "reorder_point": 10.0,
        "target_stock": 24.0,
        "suggested_reorder_quantity": 16.0,
        "replenishment_status": "LOW_STOCK",
    }
    assert report["records"][1]["product_id"] == "product-2"
    assert report["records"][1]["suggested_reorder_quantity"] == 0.0
    assert report["records"][1]["replenishment_status"] == "ADEQUATE"


def test_restock_task_policy_guards_and_board_roll_up_status():
    assert restock_task_number(branch_code="blr-flagship", sequence_number=1) == "RST-BLRFLAGSHIP-0001"
    ensure_restock_task_creatable(
        requested_quantity=12,
        existing_active_task=None,
    )
    ensure_restock_task_pickable(status="OPEN", requested_quantity=12, picked_quantity=8)
    ensure_restock_task_completable(status="PICKED")
    ensure_restock_task_cancelable(status="OPEN")
    ensure_restock_task_cancelable(status="PICKED")

    for fn, kwargs, message in [
        (
            ensure_restock_task_creatable,
            {"requested_quantity": 0, "existing_active_task": None},
            "Restock task quantity must be greater than zero",
        ),
        (
            ensure_restock_task_creatable,
            {"requested_quantity": 6, "existing_active_task": {"restock_task_id": "task-1"}},
            "Active restock task already exists for product",
        ),
        (
            ensure_restock_task_pickable,
            {"status": "PICKED", "requested_quantity": 12, "picked_quantity": 8},
            "Restock task must be open before picking",
        ),
        (
            ensure_restock_task_pickable,
            {"status": "OPEN", "requested_quantity": 12, "picked_quantity": 13},
            "Picked quantity cannot exceed requested quantity",
        ),
        (
            ensure_restock_task_completable,
            {"status": "OPEN"},
            "Restock task must be picked before completion",
        ),
        (
            ensure_restock_task_cancelable,
            {"status": "COMPLETED"},
            "Completed restock tasks cannot be canceled",
        ),
    ]:
        try:
            fn(**kwargs)
        except ValueError as error:
            assert str(error) == message
        else:
            raise AssertionError(f"Expected restock-task validation failure: {message}")

    report = build_restock_board(
        branch_id="branch-1",
        task_sessions=[
            {
                "restock_task_id": "task-1",
                "task_number": "RST-BLRFLAGSHIP-0001",
                "product_id": "product-1",
                "status": "OPEN",
                "stock_on_hand_snapshot": 8.0,
                "reorder_point_snapshot": 10.0,
                "target_stock_snapshot": 24.0,
                "suggested_quantity_snapshot": 16.0,
                "requested_quantity": 12.0,
                "picked_quantity": None,
                "source_posture": "BACKROOM_AVAILABLE",
                "note": "Aisle refill before evening rush",
                "completion_note": None,
            },
            {
                "restock_task_id": "task-2",
                "task_number": "RST-BLRFLAGSHIP-0002",
                "product_id": "product-2",
                "status": "COMPLETED",
                "stock_on_hand_snapshot": 5.0,
                "reorder_point_snapshot": 6.0,
                "target_stock_snapshot": 12.0,
                "suggested_quantity_snapshot": 7.0,
                "requested_quantity": 7.0,
                "picked_quantity": 7.0,
                "source_posture": "BACKROOM_UNCERTAIN",
                "note": None,
                "completion_note": "Shelf topped up",
            },
        ],
        products_by_id={
            "product-1": {"product_name": "Classic Tea", "sku_code": "tea-classic-250g"},
            "product-2": {"product_name": "Ginger Tea", "sku_code": "tea-ginger-100g"},
        },
    )

    assert report["open_count"] == 1
    assert report["picked_count"] == 0
    assert report["completed_count"] == 1
    assert report["canceled_count"] == 0
    assert report["records"][0]["status"] == "OPEN"
    assert report["records"][0]["requested_quantity"] == 12.0
    assert report["records"][0]["has_active_task"] is True
    assert report["records"][1]["status"] == "COMPLETED"
    assert report["records"][1]["completion_note"] == "Shelf topped up"


def test_adjustment_policy_rejects_zero_delta():
    try:
        ensure_stock_adjustment_allowed(quantity_delta=0)
    except ValueError as error:
        assert str(error) == "Stock adjustment quantity must not be zero"
    else:
        raise AssertionError("Expected zero adjustment quantity to be rejected")


def test_stock_count_result_posts_variance_against_expected_stock():
    result = build_stock_count_result(expected_quantity=22.0, counted_quantity=20.0)

    assert result.expected_quantity == 22.0
    assert result.counted_quantity == 20.0
    assert result.variance_quantity == -2.0
    assert result.closing_stock == 20.0


def test_stock_count_review_status_guards_require_valid_session_state():
    ensure_stock_count_review_recordable(status="OPEN")
    ensure_stock_count_review_approvable(status="COUNTED")
    ensure_stock_count_review_cancelable(status="OPEN")
    ensure_stock_count_review_cancelable(status="COUNTED")

    for fn, status, message in [
        (ensure_stock_count_review_recordable, "COUNTED", "Blind count already recorded for session"),
        (ensure_stock_count_review_approvable, "OPEN", "Stock count session must be counted before approval"),
        (ensure_stock_count_review_cancelable, "APPROVED", "Approved stock count sessions cannot be canceled"),
    ]:
        try:
            fn(status=status)
        except ValueError as error:
            assert str(error) == message
        else:
            raise AssertionError(f"Expected stock count review status failure for {status}")


def test_stock_count_board_rolls_up_reviewed_session_states():
    report = build_stock_count_board(
        branch_id="branch-1",
        review_sessions=[
            {
                "stock_count_session_id": "session-1",
                "product_id": "product-1",
                "status": "OPEN",
                "expected_quantity": 22.0,
                "counted_quantity": None,
                "variance_quantity": None,
                "note": "Aisle 1 blind count",
            },
            {
                "stock_count_session_id": "session-2",
                "product_id": "product-2",
                "status": "COUNTED",
                "expected_quantity": 10.0,
                "counted_quantity": 8.0,
                "variance_quantity": -2.0,
                "note": "Backroom recount",
            },
            {
                "stock_count_session_id": "session-3",
                "product_id": "product-3",
                "status": "APPROVED",
                "expected_quantity": 5.0,
                "counted_quantity": 5.0,
                "variance_quantity": 0.0,
                "note": None,
            },
        ],
        products_by_id={
            "product-1": {"product_name": "Classic Tea", "sku_code": "tea-classic-250g"},
            "product-2": {"product_name": "Ginger Tea", "sku_code": "tea-ginger-100g"},
            "product-3": {"product_name": "Mint Tea", "sku_code": "tea-mint-100g"},
        },
    )

    assert report["open_count"] == 1
    assert report["counted_count"] == 1
    assert report["approved_count"] == 1
    assert report["records"][0]["status"] == "OPEN"
    assert report["records"][1]["status"] == "COUNTED"
    assert report["records"][1]["variance_quantity"] == -2.0


def test_transfer_policy_requires_positive_quantity_distinct_destination_and_stock():
    ensure_transfer_allowed(
        source_branch_id="branch-1",
        destination_branch_id="branch-2",
        quantity=5,
        available_quantity=20,
    )

    for kwargs, message in [
        (
            {
                "source_branch_id": "branch-1",
                "destination_branch_id": "branch-1",
                "quantity": 5,
                "available_quantity": 20,
            },
            "Transfer destination must be a different branch",
        ),
        (
            {
                "source_branch_id": "branch-1",
                "destination_branch_id": "branch-2",
                "quantity": 0,
                "available_quantity": 20,
            },
            "Transfer quantity must be greater than zero",
        ),
        (
            {
                "source_branch_id": "branch-1",
                "destination_branch_id": "branch-2",
                "quantity": 25,
                "available_quantity": 20,
            },
            "Insufficient stock for transfer",
        ),
    ]:
        try:
            ensure_transfer_allowed(**kwargs)
        except ValueError as error:
            assert str(error) == message
        else:
            raise AssertionError(f"Expected transfer validation failure: {message}")


def test_transfer_number_and_board_roll_up_branch_direction():
    assert transfer_number(branch_code="blr-flagship", sequence_number=1) == "TRF-BLRFLAGSHIP-0001"

    report = build_transfer_board(
        branch_id="branch-1",
        transfers=[
            {
                "transfer_order_id": "transfer-1",
                "transfer_number": "TRF-BLRFLAGSHIP-0001",
                "source_branch_id": "branch-1",
                "destination_branch_id": "branch-2",
                "product_id": "product-1",
                "quantity": 5,
                "status": "COMPLETED",
            },
            {
                "transfer_order_id": "transfer-2",
                "transfer_number": "TRF-MYSURUHUB-0001",
                "source_branch_id": "branch-3",
                "destination_branch_id": "branch-1",
                "product_id": "product-1",
                "quantity": 2,
                "status": "COMPLETED",
            },
        ],
        branches_by_id={
            "branch-1": {"name": "Bengaluru Flagship"},
            "branch-2": {"name": "Mysuru Hub"},
            "branch-3": {"name": "Chennai South"},
        },
        products_by_id={
            "product-1": {"product_name": "Classic Tea", "sku_code": "tea-classic-250g"},
        },
    )

    assert report["outbound_count"] == 1
    assert report["inbound_count"] == 1
    assert report["records"][0]["direction"] == "OUTBOUND"
    assert report["records"][1]["direction"] == "INBOUND"
