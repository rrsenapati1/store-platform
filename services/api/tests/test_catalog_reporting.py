from store_api.catalog_reporting import build_branch_catalog_records, build_inventory_snapshot_report


def test_branch_catalog_records_apply_override_pricing_and_stock_status():
    records = build_branch_catalog_records(
        products=[
            {
                "id": "product-1",
                "name": "Notebook",
                "sku_code": "SKU-001",
                "barcode": "8901234567890",
                "selling_price": 100,
                "hsn_sac_code": "4820",
            },
            {
                "id": "product-2",
                "name": "Pen",
                "sku_code": "SKU-002",
                "barcode": "8901234567001",
                "selling_price": 20,
                "hsn_sac_code": "9608",
            },
        ],
        catalog_overrides={
            ("branch-1", "product-1"): {"selling_price": 112, "is_active": True},
            ("branch-1", "product-2"): {"selling_price": None, "is_active": False},
        },
        branch_id="branch-1",
        stock_by_product={"product-1": 4, "product-2": 0},
    )

    assert records == [
        {
            "product_id": "product-1",
            "product_name": "Notebook",
            "sku_code": "SKU-001",
            "barcode": "8901234567890",
            "hsn_sac_code": "4820",
            "selling_price": 112.0,
            "stock_on_hand": 4.0,
            "is_active": True,
            "price_source": "OVERRIDE",
            "availability_status": "LOW_STOCK",
        },
        {
            "product_id": "product-2",
            "product_name": "Pen",
            "sku_code": "SKU-002",
            "barcode": "8901234567001",
            "hsn_sac_code": "9608",
            "selling_price": 20.0,
            "stock_on_hand": 0.0,
            "is_active": False,
            "price_source": "MASTER",
            "availability_status": "INACTIVE",
        },
    ]


def test_inventory_snapshot_report_counts_low_and_out_of_stock_records():
    report = build_inventory_snapshot_report(
        catalog_records=[
            {"product_id": "product-1", "product_name": "Notebook", "stock_on_hand": 4, "availability_status": "LOW_STOCK"},
            {"product_id": "product-2", "product_name": "Pen", "stock_on_hand": 0, "availability_status": "OUT_OF_STOCK"},
            {"product_id": "product-3", "product_name": "Marker", "stock_on_hand": 8, "availability_status": "AVAILABLE"},
        ]
    )

    assert report == {
        "sku_count": 3,
        "low_stock_count": 1,
        "out_of_stock_count": 1,
        "inactive_count": 0,
        "records": [
            {"product_id": "product-1", "product_name": "Notebook", "stock_on_hand": 4.0, "availability_status": "LOW_STOCK"},
            {"product_id": "product-2", "product_name": "Pen", "stock_on_hand": 0.0, "availability_status": "OUT_OF_STOCK"},
            {"product_id": "product-3", "product_name": "Marker", "stock_on_hand": 8.0, "availability_status": "AVAILABLE"},
        ],
    }
