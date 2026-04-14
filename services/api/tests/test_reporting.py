from store_api.reporting import (
    build_payment_mix,
    build_sales_summary,
    build_stock_risk_report,
    build_top_products,
)


def test_sales_summary_tracks_gross_returns_and_average_basket():
    summary = build_sales_summary(
        invoices=[
            {"grand_total": 236},
            {"grand_total": 236},
            {"grand_total": 11.8},
        ],
        credit_notes=[{"grand_total": 59}],
    )

    assert summary == {
        "sales_count": 3,
        "gross_sales_total": 483.8,
        "return_total": 59.0,
        "net_sales_total": 424.8,
        "average_basket_value": 161.27,
    }


def test_payment_mix_groups_sales_by_payment_method():
    payment_mix = build_payment_mix(
        sales=[
            {"invoice_id": "inv-cash", "payment_method": "cash"},
            {"invoice_id": "inv-upi", "payment_method": "upi"},
            {"invoice_id": "inv-upi-2", "payment_method": "upi"},
        ],
        invoices_by_id={
            "inv-cash": {"grand_total": 236},
            "inv-upi": {"grand_total": 118},
            "inv-upi-2": {"grand_total": 59},
        },
    )

    assert payment_mix == [
        {"payment_method": "upi", "sales_count": 2, "gross_sales_total": 177.0},
        {"payment_method": "cash", "sales_count": 1, "gross_sales_total": 236.0},
    ]


def test_top_products_ranks_product_sales_from_invoice_lines():
    top_products = build_top_products(
        invoices=[
            {
                "lines": [
                    {"product_id": "prod-notebook", "quantity": 2, "line_total": 200},
                    {"product_id": "prod-pen", "quantity": 1, "line_total": 50},
                ]
            },
            {
                "lines": [
                    {"product_id": "prod-notebook", "quantity": 1, "line_total": 100},
                    {"product_id": "prod-eraser", "quantity": 1, "line_total": 10},
                ]
            },
        ],
        products_by_id={
            "prod-notebook": {"name": "Notebook"},
            "prod-pen": {"name": "Pen Pack"},
            "prod-eraser": {"name": "Eraser"},
        },
    )

    assert top_products == [
        {"product_id": "prod-notebook", "product_name": "Notebook", "quantity_sold": 3.0, "sales_total": 300.0},
        {"product_id": "prod-pen", "product_name": "Pen Pack", "quantity_sold": 1.0, "sales_total": 50.0},
        {"product_id": "prod-eraser", "product_name": "Eraser", "quantity_sold": 1.0, "sales_total": 10.0},
    ]


def test_stock_risk_report_splits_low_out_and_negative_stock():
    stock_risk = build_stock_risk_report(
        stock_rows=[
            {"product_id": "prod-notebook", "product_name": "Notebook", "stock_on_hand": 3},
            {"product_id": "prod-pen", "product_name": "Pen Pack", "stock_on_hand": 0},
            {"product_id": "prod-eraser", "product_name": "Eraser", "stock_on_hand": -2},
            {"product_id": "prod-scale", "product_name": "Scale", "stock_on_hand": 8},
        ]
    )

    assert stock_risk == {
        "low_stock_products": [
            {"product_id": "prod-notebook", "product_name": "Notebook", "stock_on_hand": 3.0}
        ],
        "out_of_stock_products": [
            {"product_id": "prod-pen", "product_name": "Pen Pack", "stock_on_hand": 0.0}
        ],
        "negative_stock_products": [
            {"product_id": "prod-eraser", "product_name": "Eraser", "stock_on_hand": -2.0}
        ],
    }
