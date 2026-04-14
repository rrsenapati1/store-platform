from __future__ import annotations

from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def build_replenishment_records(
    *,
    reorder_rules: list[dict[str, Any]],
    products_by_id: dict[str, dict[str, Any]],
    stock_by_product: dict[str, float],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rule in reorder_rules:
        product_id = rule["product_id"]
        product = products_by_id.get(product_id)
        if product is None:
            continue
        stock_on_hand = _money(stock_by_product.get(product_id, 0.0))
        min_stock = _money(rule["min_stock"])
        target_stock = _money(rule["target_stock"])
        if stock_on_hand < min_stock:
            status = "REORDER_NOW"
        elif stock_on_hand == min_stock:
            status = "WATCH"
        else:
            status = "OK"
        records.append(
            {
                "product_id": product_id,
                "product_name": product["name"],
                "stock_on_hand": stock_on_hand,
                "min_stock": min_stock,
                "target_stock": target_stock,
                "reorder_quantity": _money(max(0.0, target_stock - stock_on_hand)),
                "status": status,
            }
        )
    status_order = {"REORDER_NOW": 0, "WATCH": 1, "OK": 2}
    return sorted(records, key=lambda record: (status_order[record["status"]], -record["reorder_quantity"], record["product_name"]))
