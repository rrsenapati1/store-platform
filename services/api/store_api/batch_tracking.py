from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any


def _quantity(value: float) -> float:
    return round(float(value), 2)


def _expiry_status(days_to_expiry: int) -> str:
    if days_to_expiry < 0:
        return "EXPIRED"
    if days_to_expiry <= 30:
        return "EXPIRING_SOON"
    return "FRESH"


def validate_goods_receipt_batch_lots(
    goods_receipt_lines: list[dict[str, Any]],
    lots: list[dict[str, Any]],
) -> None:
    receipt_quantities: dict[str, float] = defaultdict(float)
    batch_quantities: dict[str, float] = defaultdict(float)

    for line in goods_receipt_lines:
        receipt_quantities[line["product_id"]] = _quantity(receipt_quantities[line["product_id"]] + float(line["quantity"]))

    for lot in lots:
        batch_quantities[lot["product_id"]] = _quantity(batch_quantities[lot["product_id"]] + float(lot["quantity"]))

    if set(receipt_quantities) != set(batch_quantities):
        raise ValueError("Batch quantities must match goods receipt quantity for every product")

    for product_id, receipt_quantity in receipt_quantities.items():
        if batch_quantities[product_id] != receipt_quantity:
            raise ValueError("Batch quantities must match goods receipt quantity for every product")


def build_batch_expiry_report(
    *,
    batch_lots: list[dict[str, Any]],
    products_by_id: dict[str, dict[str, Any]],
    stock_by_product: dict[str, float],
    as_of: date,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    untracked_stock_quantity = 0.0
    grouped_lots: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for lot in batch_lots:
        grouped_lots[lot["product_id"]].append(lot)

    for product_id, lots in grouped_lots.items():
        sorted_lots = sorted(
            lots,
            key=lambda lot: (lot["expiry_date"], lot["batch_number"], lot["id"]),
        )
        stock_on_hand = _quantity(stock_by_product.get(product_id, 0.0))
        tracked_available_total = _quantity(
            sum(max(_quantity(lot["quantity"]) - _quantity(lot.get("written_off_quantity", 0.0)), 0.0) for lot in sorted_lots)
        )
        tracked_stock_remaining = min(stock_on_hand, tracked_available_total)
        depletion_remaining = _quantity(tracked_available_total - tracked_stock_remaining)
        untracked_stock_quantity = _quantity(untracked_stock_quantity + max(stock_on_hand - tracked_available_total, 0.0))

        for lot in sorted_lots:
            received_quantity = _quantity(lot["quantity"])
            written_off_quantity = _quantity(lot.get("written_off_quantity", 0.0))
            net_available = max(_quantity(received_quantity - written_off_quantity), 0.0)
            consumed_quantity = min(net_available, depletion_remaining)
            depletion_remaining = _quantity(depletion_remaining - consumed_quantity)
            remaining_quantity = _quantity(net_available - consumed_quantity)
            if remaining_quantity <= 0:
                continue

            expiry_day = date.fromisoformat(lot["expiry_date"])
            days_to_expiry = (expiry_day - as_of).days
            records.append(
                {
                    "batch_lot_id": lot["id"],
                    "product_id": product_id,
                    "product_name": products_by_id.get(product_id, {}).get("name", "Unknown product"),
                    "batch_number": lot["batch_number"],
                    "expiry_date": lot["expiry_date"],
                    "days_to_expiry": days_to_expiry,
                    "received_quantity": received_quantity,
                    "written_off_quantity": written_off_quantity,
                    "remaining_quantity": remaining_quantity,
                    "status": _expiry_status(days_to_expiry),
                }
            )

    records.sort(key=lambda record: (record["expiry_date"], record["batch_number"], record["batch_lot_id"]))
    return {
        "tracked_lot_count": len(records),
        "expiring_soon_count": sum(1 for record in records if record["status"] == "EXPIRING_SOON"),
        "expired_count": sum(1 for record in records if record["status"] == "EXPIRED"),
        "untracked_stock_quantity": _quantity(untracked_stock_quantity),
        "records": records,
    }
