from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from .purchase_policy import money


def _expiry_status(days_to_expiry: int) -> str:
    if days_to_expiry < 0:
        return "EXPIRED"
    if days_to_expiry <= 30:
        return "EXPIRING_SOON"
    return "FRESH"


def validate_goods_receipt_batch_lots(
    *,
    goods_receipt_lines: list[dict[str, Any]],
    lots: list[dict[str, Any]],
) -> None:
    receipt_quantities: dict[str, float] = defaultdict(float)
    batch_quantities: dict[str, float] = defaultdict(float)

    for line in goods_receipt_lines:
        product_id = str(line["product_id"])
        receipt_quantities[product_id] = money(receipt_quantities[product_id] + float(line["quantity"]))

    for lot in lots:
        product_id = str(lot["product_id"])
        batch_quantities[product_id] = money(batch_quantities[product_id] + float(lot["quantity"]))

    if set(receipt_quantities) != set(batch_quantities):
        raise ValueError("Batch quantities must match goods receipt quantity for every product")

    for product_id, receipt_quantity in receipt_quantities.items():
        if batch_quantities[product_id] != receipt_quantity:
            raise ValueError("Batch quantities must match goods receipt quantity for every product")


def ensure_expiry_write_off_allowed(*, remaining_quantity: float, quantity: float) -> None:
    requested = money(quantity)
    available = money(remaining_quantity)
    if available <= 0:
        raise ValueError("No remaining batch quantity available for write-off")
    if requested <= 0:
        raise ValueError("Expiry write-off quantity must be greater than zero")
    if requested > available:
        raise ValueError("Expiry write-off exceeds remaining batch quantity")


def build_batch_expiry_report(
    *,
    batch_lots: list[dict[str, Any]],
    write_offs_by_batch_lot_id: dict[str, float],
    products_by_id: dict[str, dict[str, Any]],
    stock_by_product: dict[str, float],
    as_of: date,
) -> dict[str, Any]:
    grouped_lots: dict[str, list[dict[str, Any]]] = defaultdict(list)
    records: list[dict[str, Any]] = []
    untracked_stock_quantity = 0.0

    for lot in batch_lots:
        grouped_lots[str(lot["product_id"])].append(lot)

    for product_id, lots in grouped_lots.items():
        sorted_lots = sorted(
            lots,
            key=lambda lot: (str(lot["expiry_date"]), str(lot["batch_number"]), str(lot["id"])),
        )
        stock_on_hand = money(stock_by_product.get(product_id, 0.0))
        tracked_available_total = money(
            sum(max(money(float(lot["quantity"])) - money(write_offs_by_batch_lot_id.get(str(lot["id"]), 0.0)), 0.0) for lot in sorted_lots)
        )
        tracked_stock_remaining = min(stock_on_hand, tracked_available_total)
        depletion_remaining = money(tracked_available_total - tracked_stock_remaining)
        untracked_stock_quantity = money(untracked_stock_quantity + max(stock_on_hand - tracked_available_total, 0.0))

        for lot in sorted_lots:
            lot_id = str(lot["id"])
            written_off_quantity = money(write_offs_by_batch_lot_id.get(lot_id, 0.0))
            received_quantity = money(float(lot["quantity"]))
            net_available = max(money(received_quantity - written_off_quantity), 0.0)
            consumed_quantity = min(net_available, depletion_remaining)
            depletion_remaining = money(depletion_remaining - consumed_quantity)
            remaining_quantity = money(net_available - consumed_quantity)
            if remaining_quantity <= 0:
                continue

            expiry_day = lot["expiry_date"] if isinstance(lot["expiry_date"], date) else date.fromisoformat(str(lot["expiry_date"]))
            days_to_expiry = (expiry_day - as_of).days
            records.append(
                {
                    "batch_lot_id": lot_id,
                    "product_id": product_id,
                    "product_name": str(products_by_id.get(product_id, {}).get("name", "Unknown product")),
                    "batch_number": str(lot["batch_number"]),
                    "expiry_date": expiry_day.isoformat(),
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
        "untracked_stock_quantity": money(untracked_stock_quantity),
        "records": records,
    }
