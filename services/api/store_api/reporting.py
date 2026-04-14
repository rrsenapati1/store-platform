from __future__ import annotations

from collections import defaultdict
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def build_sales_summary(*, invoices: list[dict[str, Any]], credit_notes: list[dict[str, Any]]) -> dict[str, float | int]:
    gross_sales_total = _money(sum(float(invoice["grand_total"]) for invoice in invoices))
    return_total = _money(sum(float(note["grand_total"]) for note in credit_notes))
    sales_count = len(invoices)
    average_basket_value = _money(gross_sales_total / sales_count) if sales_count else 0.0
    return {
        "sales_count": sales_count,
        "gross_sales_total": gross_sales_total,
        "return_total": return_total,
        "net_sales_total": _money(gross_sales_total - return_total),
        "average_basket_value": average_basket_value,
    }


def build_payment_mix(*, sales: list[dict[str, Any]], invoices_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    payment_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"sales_count": 0, "gross_sales_total": 0.0})
    for sale in sales:
        invoice = invoices_by_id.get(sale["invoice_id"])
        if not invoice:
            continue
        bucket = payment_totals[sale["payment_method"]]
        bucket["sales_count"] += 1
        bucket["gross_sales_total"] = _money(bucket["gross_sales_total"] + float(invoice["grand_total"]))
    return sorted(
        (
            {
                "payment_method": payment_method,
                "sales_count": totals["sales_count"],
                "gross_sales_total": totals["gross_sales_total"],
            }
            for payment_method, totals in payment_totals.items()
        ),
        key=lambda entry: (-entry["sales_count"], -entry["gross_sales_total"], entry["payment_method"]),
    )


def build_top_products(
    *,
    invoices: list[dict[str, Any]],
    products_by_id: dict[str, dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    product_totals: dict[str, dict[str, float]] = defaultdict(lambda: {"quantity_sold": 0.0, "sales_total": 0.0})
    for invoice in invoices:
        for line in invoice["lines"]:
            bucket = product_totals[line["product_id"]]
            bucket["quantity_sold"] += float(line["quantity"])
            bucket["sales_total"] = _money(bucket["sales_total"] + float(line["line_total"]))
    ranked = sorted(
        (
            {
                "product_id": product_id,
                "product_name": products_by_id[product_id]["name"],
                "quantity_sold": _money(totals["quantity_sold"]),
                "sales_total": totals["sales_total"],
            }
            for product_id, totals in product_totals.items()
            if product_id in products_by_id
        ),
        key=lambda entry: (-entry["sales_total"], -entry["quantity_sold"], entry["product_name"]),
    )
    return ranked[:limit]


def build_stock_risk_report(*, stock_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    normalized_rows = [
        {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "stock_on_hand": _money(float(row["stock_on_hand"])),
        }
        for row in stock_rows
    ]

    def _sorted(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(rows, key=lambda row: row["product_name"])

    return {
        "low_stock_products": _sorted([row for row in normalized_rows if 0 < row["stock_on_hand"] <= 5]),
        "out_of_stock_products": _sorted([row for row in normalized_rows if row["stock_on_hand"] == 0]),
        "negative_stock_products": _sorted([row for row in normalized_rows if row["stock_on_hand"] < 0]),
    }
