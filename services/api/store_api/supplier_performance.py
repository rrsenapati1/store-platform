from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from typing import Any


def _parse_iso_date(raw_value: Any) -> date | None:
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return None
    return None


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 2)


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _performance_status(*, on_time_receipt_rate: float, invoice_mismatch_count: int, supplier_return_rate: float) -> str:
    if invoice_mismatch_count > 0 or supplier_return_rate >= 0.5 or on_time_receipt_rate < 0.5:
        return "AT_RISK"
    if supplier_return_rate > 0.0 or on_time_receipt_rate < 1.0:
        return "WATCH"
    return "STRONG"


def build_supplier_performance_report(
    *,
    branch_id: str,
    purchase_orders: Iterable[dict[str, Any]],
    goods_receipts: Iterable[dict[str, Any]],
    purchase_invoices: Iterable[dict[str, Any]],
    supplier_returns: Iterable[dict[str, Any]],
    vendor_disputes: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    approved_purchase_orders = [
        purchase_order
        for purchase_order in purchase_orders
        if purchase_order.get("branch_id") == branch_id and purchase_order.get("approval_status") == "APPROVED"
    ]
    goods_receipts_by_purchase_order_id = {
        goods_receipt["purchase_order_id"]: goods_receipt
        for goods_receipt in goods_receipts
        if goods_receipt.get("branch_id") == branch_id
    }
    branch_purchase_invoices = [
        purchase_invoice for purchase_invoice in purchase_invoices if purchase_invoice.get("branch_id") == branch_id
    ]
    purchase_invoices_by_id = {purchase_invoice["id"]: purchase_invoice for purchase_invoice in branch_purchase_invoices}

    approved_purchase_orders_by_supplier_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for purchase_order in approved_purchase_orders:
        approved_purchase_orders_by_supplier_id[purchase_order["supplier_id"]].append(purchase_order)

    purchase_invoices_by_supplier_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for purchase_invoice in branch_purchase_invoices:
        purchase_invoices_by_supplier_id[purchase_invoice["supplier_id"]].append(purchase_invoice)

    supplier_return_count_by_supplier_id: dict[str, int] = defaultdict(int)
    for supplier_return in supplier_returns:
        if supplier_return.get("branch_id") != branch_id:
            continue
        supplier_return_count_by_supplier_id[supplier_return["supplier_id"]] += 1

    mismatch_invoice_ids_by_supplier_id: dict[str, set[str]] = defaultdict(set)
    for vendor_dispute in vendor_disputes:
        if vendor_dispute.get("branch_id") != branch_id:
            continue
        if vendor_dispute.get("dispute_type") != "RATE_MISMATCH":
            continue
        purchase_invoice_id = vendor_dispute.get("purchase_invoice_id")
        if not purchase_invoice_id or purchase_invoice_id not in purchase_invoices_by_id:
            continue
        mismatch_invoice_ids_by_supplier_id[vendor_dispute["supplier_id"]].add(purchase_invoice_id)

    supplier_ids = (
        set(approved_purchase_orders_by_supplier_id)
        | set(purchase_invoices_by_supplier_id)
        | set(supplier_return_count_by_supplier_id)
        | set(mismatch_invoice_ids_by_supplier_id)
    )

    records: list[dict[str, Any]] = []
    for supplier_id in supplier_ids:
        supplier = suppliers_by_id.get(supplier_id, {})
        approved_orders = approved_purchase_orders_by_supplier_id.get(supplier_id, [])
        received_purchase_order_count = 0
        on_time_receipt_count = 0
        delay_days: list[int] = []
        for purchase_order in approved_orders:
            goods_receipt = goods_receipts_by_purchase_order_id.get(purchase_order["id"])
            if not goods_receipt:
                continue
            received_purchase_order_count += 1
            approved_on = _parse_iso_date(purchase_order.get("approved_on"))
            received_on = _parse_iso_date(goods_receipt.get("received_on"))
            if approved_on is None or received_on is None:
                continue
            receipt_delay = max(0, (received_on - approved_on).days)
            delay_days.append(receipt_delay)
            if receipt_delay <= 2:
                on_time_receipt_count += 1

        purchase_invoice_count = len(purchase_invoices_by_supplier_id.get(supplier_id, []))
        invoice_mismatch_count = len(mismatch_invoice_ids_by_supplier_id.get(supplier_id, set()))
        supplier_return_count = supplier_return_count_by_supplier_id.get(supplier_id, 0)
        on_time_receipt_rate = _ratio(on_time_receipt_count, received_purchase_order_count)
        supplier_return_rate = _ratio(supplier_return_count, purchase_invoice_count)
        invoice_mismatch_rate = _ratio(invoice_mismatch_count, purchase_invoice_count)

        records.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", "Unknown supplier"),
                "approved_purchase_order_count": len(approved_orders),
                "received_purchase_order_count": received_purchase_order_count,
                "on_time_receipt_count": on_time_receipt_count,
                "on_time_receipt_rate": on_time_receipt_rate,
                "average_receipt_delay_days": _average(delay_days),
                "purchase_invoice_count": purchase_invoice_count,
                "invoice_mismatch_count": invoice_mismatch_count,
                "invoice_mismatch_rate": invoice_mismatch_rate,
                "supplier_return_count": supplier_return_count,
                "supplier_return_rate": supplier_return_rate,
                "performance_status": _performance_status(
                    on_time_receipt_rate=on_time_receipt_rate,
                    invoice_mismatch_count=invoice_mismatch_count,
                    supplier_return_rate=supplier_return_rate,
                ),
            }
        )

    risk_order = {"AT_RISK": 0, "WATCH": 1, "STRONG": 2}
    records.sort(
        key=lambda record: (
            risk_order.get(record["performance_status"], 99),
            record["on_time_receipt_rate"],
            -record["invoice_mismatch_rate"],
            -record["supplier_return_rate"],
            record["supplier_name"],
        )
    )

    return {
        "branch_id": branch_id,
        "supplier_count": len(records),
        "strong_count": sum(1 for record in records if record["performance_status"] == "STRONG"),
        "watch_count": sum(1 for record in records if record["performance_status"] == "WATCH"),
        "at_risk_count": sum(1 for record in records if record["performance_status"] == "AT_RISK"),
        "records": records,
    }
