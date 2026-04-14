from store_control_plane.services.inventory_policy import (
    build_inventory_snapshot,
    build_receiving_board,
    build_stock_count_result,
    build_transfer_board,
    ensure_purchase_order_receivable,
    ensure_stock_adjustment_allowed,
    ensure_transfer_allowed,
    goods_receipt_number,
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
            }
        ],
    )

    assert report["received_count"] == 1
    assert report["blocked_count"] == 1
    assert report["records"][0]["receiving_status"] == "BLOCKED"
    assert report["records"][1]["goods_receipt_id"] == "grn-1"


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
