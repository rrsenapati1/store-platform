from datetime import date

import pytest

from store_api.batch_tracking import build_batch_expiry_report, validate_goods_receipt_batch_lots


def test_batch_expiry_report_allocates_remaining_stock_fifo():
    as_of = date(2026, 4, 13)
    report = build_batch_expiry_report(
        batch_lots=[
            {
                "id": "lot-1",
                "product_id": "product-1",
                "batch_number": "BATCH-A",
                "expiry_date": "2026-04-20",
                "quantity": 6,
                "written_off_quantity": 0,
            },
            {
                "id": "lot-2",
                "product_id": "product-1",
                "batch_number": "BATCH-B",
                "expiry_date": "2026-07-01",
                "quantity": 4,
                "written_off_quantity": 0,
            },
        ],
        products_by_id={"product-1": {"name": "Notebook"}},
        stock_by_product={"product-1": 5},
        as_of=as_of,
    )

    assert report["expiring_soon_count"] == 1
    assert report["expired_count"] == 0
    assert report["untracked_stock_quantity"] == 0
    assert report["records"] == [
        {
            "batch_lot_id": "lot-1",
            "product_id": "product-1",
            "product_name": "Notebook",
            "batch_number": "BATCH-A",
            "expiry_date": "2026-04-20",
            "days_to_expiry": 7,
            "received_quantity": 6.0,
            "written_off_quantity": 0.0,
            "remaining_quantity": 1.0,
            "status": "EXPIRING_SOON",
        },
        {
            "batch_lot_id": "lot-2",
            "product_id": "product-1",
            "product_name": "Notebook",
            "batch_number": "BATCH-B",
            "expiry_date": "2026-07-01",
            "days_to_expiry": 79,
            "received_quantity": 4.0,
            "written_off_quantity": 0.0,
            "remaining_quantity": 4.0,
            "status": "FRESH",
        },
    ]


def test_batch_validation_requires_full_quantity_match_per_product():
    with pytest.raises(ValueError, match="Batch quantities must match goods receipt quantity"):
        validate_goods_receipt_batch_lots(
            goods_receipt_lines=[{"product_id": "product-1", "quantity": 10}],
            lots=[
                {"product_id": "product-1", "batch_number": "BATCH-A", "quantity": 6, "expiry_date": "2026-04-20"},
                {"product_id": "product-1", "batch_number": "BATCH-B", "quantity": 3, "expiry_date": "2026-05-01"},
            ],
        )
