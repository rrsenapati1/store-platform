from datetime import date, timedelta

import pytest

from store_control_plane.services.batches_policy import build_batch_expiry_report, validate_goods_receipt_batch_lots


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
