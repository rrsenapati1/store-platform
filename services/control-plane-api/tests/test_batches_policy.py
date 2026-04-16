from datetime import date, timedelta

import pytest

from store_control_plane.services.batches_policy import (
    build_batch_expiry_board,
    build_batch_expiry_report,
    ensure_batch_expiry_review_approvable,
    ensure_batch_expiry_review_cancelable,
    ensure_batch_expiry_review_recordable,
    validate_goods_receipt_batch_lots,
)


def test_validate_goods_receipt_batch_lots_requires_exact_product_quantity_match() -> None:
    with pytest.raises(ValueError, match="Batch quantities must match goods receipt quantity for every product"):
        validate_goods_receipt_batch_lots(
            goods_receipt_lines=[{"product_id": "product-1", "quantity": 10}],
            lots=[
                {"product_id": "product-1", "quantity": 6},
                {"product_id": "product-1", "quantity": 3},
            ],
        )


def test_build_batch_expiry_report_depletes_oldest_stock_first_and_hides_empty_lots() -> None:
    as_of = date.today()
    report = build_batch_expiry_report(
        batch_lots=[
            {
                "id": "lot-a",
                "product_id": "product-1",
                "batch_number": "BATCH-A",
                "quantity": 6,
                "expiry_date": (as_of + timedelta(days=7)).isoformat(),
            },
            {
                "id": "lot-b",
                "product_id": "product-1",
                "batch_number": "BATCH-B",
                "quantity": 4,
                "expiry_date": (as_of + timedelta(days=90)).isoformat(),
            },
        ],
        write_offs_by_batch_lot_id={"lot-a": 1.0},
        products_by_id={"product-1": {"name": "Classic Tea"}},
        stock_by_product={"product-1": 5},
        as_of=as_of,
    )

    assert report["tracked_lot_count"] == 2
    assert report["expiring_soon_count"] == 1
    assert report["records"] == [
        {
            "batch_lot_id": "lot-a",
            "product_id": "product-1",
            "product_name": "Classic Tea",
            "batch_number": "BATCH-A",
            "expiry_date": (as_of + timedelta(days=7)).isoformat(),
            "days_to_expiry": 7,
            "received_quantity": 6.0,
            "written_off_quantity": 1.0,
            "remaining_quantity": 1.0,
            "status": "EXPIRING_SOON",
        },
        {
            "batch_lot_id": "lot-b",
            "product_id": "product-1",
            "product_name": "Classic Tea",
            "batch_number": "BATCH-B",
            "expiry_date": (as_of + timedelta(days=90)).isoformat(),
            "days_to_expiry": 90,
            "received_quantity": 4.0,
            "written_off_quantity": 0.0,
            "remaining_quantity": 4.0,
            "status": "FRESH",
        },
    ]


def test_batch_expiry_review_status_guards_require_valid_session_state() -> None:
    ensure_batch_expiry_review_recordable(status="OPEN")
    ensure_batch_expiry_review_approvable(status="REVIEWED")
    ensure_batch_expiry_review_cancelable(status="OPEN")

    with pytest.raises(ValueError, match="Expiry review already recorded for session"):
        ensure_batch_expiry_review_recordable(status="REVIEWED")

    with pytest.raises(ValueError, match="Expiry review session must be reviewed before approval"):
        ensure_batch_expiry_review_approvable(status="OPEN")

    with pytest.raises(ValueError, match="Approved expiry review sessions cannot be canceled"):
        ensure_batch_expiry_review_cancelable(status="APPROVED")

    with pytest.raises(ValueError, match="Expiry review session already canceled"):
        ensure_batch_expiry_review_cancelable(status="CANCELED")


def test_build_batch_expiry_board_rolls_up_reviewed_session_states() -> None:
    board = build_batch_expiry_board(
        branch_id="branch-1",
        review_sessions=[
            {
                "batch_expiry_session_id": "expiry-session-1",
                "session_number": "EWS-BLRFLAGSHIP-0001",
                "batch_lot_id": "lot-1",
                "product_id": "product-1",
                "batch_number": "BATCH-A",
                "status": "REVIEWED",
                "remaining_quantity_snapshot": 6,
                "proposed_quantity": 2,
                "reason": "Expired on shelf",
                "note": "Shelf check",
                "review_note": None,
            },
            {
                "batch_expiry_session_id": "expiry-session-2",
                "session_number": "EWS-BLRFLAGSHIP-0002",
                "batch_lot_id": "lot-2",
                "product_id": "product-2",
                "batch_number": "BATCH-B",
                "status": "OPEN",
                "remaining_quantity_snapshot": 4,
                "proposed_quantity": None,
                "reason": None,
                "note": None,
                "review_note": None,
            },
        ],
        products_by_id={
            "product-1": {"product_name": "Classic Tea", "sku_code": "tea-classic-250g"},
            "product-2": {"product_name": "Masala Tea", "sku_code": "tea-masala-250g"},
        },
    )

    assert board == {
        "branch_id": "branch-1",
        "open_count": 1,
        "reviewed_count": 1,
        "approved_count": 0,
        "canceled_count": 0,
        "records": [
            {
                "batch_expiry_session_id": "expiry-session-2",
                "session_number": "EWS-BLRFLAGSHIP-0002",
                "batch_lot_id": "lot-2",
                "product_id": "product-2",
                "product_name": "Masala Tea",
                "sku_code": "tea-masala-250g",
                "batch_number": "BATCH-B",
                "status": "OPEN",
                "remaining_quantity_snapshot": 4.0,
                "proposed_quantity": None,
                "reason": None,
                "note": None,
                "review_note": None,
            },
            {
                "batch_expiry_session_id": "expiry-session-1",
                "session_number": "EWS-BLRFLAGSHIP-0001",
                "batch_lot_id": "lot-1",
                "product_id": "product-1",
                "product_name": "Classic Tea",
                "sku_code": "tea-classic-250g",
                "batch_number": "BATCH-A",
                "status": "REVIEWED",
                "remaining_quantity_snapshot": 6.0,
                "proposed_quantity": 2.0,
                "reason": "Expired on shelf",
                "note": "Shelf check",
                "review_note": None,
            },
        ],
    }
