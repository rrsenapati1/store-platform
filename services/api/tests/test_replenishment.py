from store_api.replenishment import build_replenishment_records


def test_replenishment_records_rank_reorder_now_before_watch_and_ok():
    records = build_replenishment_records(
        reorder_rules=[
            {"product_id": "prod-notebook", "min_stock": 5, "target_stock": 12},
            {"product_id": "prod-pen", "min_stock": 2, "target_stock": 8},
            {"product_id": "prod-eraser", "min_stock": 1, "target_stock": 5},
        ],
        products_by_id={
            "prod-notebook": {"name": "Notebook"},
            "prod-pen": {"name": "Pen Pack"},
            "prod-eraser": {"name": "Eraser"},
        },
        stock_by_product={
            "prod-notebook": 3,
            "prod-pen": 2,
            "prod-eraser": 4,
        },
    )

    assert records == [
        {
            "product_id": "prod-notebook",
            "product_name": "Notebook",
            "stock_on_hand": 3.0,
            "min_stock": 5.0,
            "target_stock": 12.0,
            "reorder_quantity": 9.0,
            "status": "REORDER_NOW",
        },
        {
            "product_id": "prod-pen",
            "product_name": "Pen Pack",
            "stock_on_hand": 2.0,
            "min_stock": 2.0,
            "target_stock": 8.0,
            "reorder_quantity": 6.0,
            "status": "WATCH",
        },
        {
            "product_id": "prod-eraser",
            "product_name": "Eraser",
            "stock_on_hand": 4.0,
            "min_stock": 1.0,
            "target_stock": 5.0,
            "reorder_quantity": 1.0,
            "status": "OK",
        },
    ]
