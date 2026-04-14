from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def _normalized(text: str | None) -> str:
    return (text or "").strip().lower()


def build_customer_directory_records(
    *,
    customers: Iterable[dict[str, Any]],
    sales_by_id: dict[str, dict[str, Any]],
    invoices_by_id: dict[str, dict[str, Any]],
    query: str | None = None,
) -> list[dict[str, Any]]:
    query_value = _normalized(query)
    records: list[dict[str, Any]] = []
    for customer in customers:
        searchable_fields = (
            customer.get("name"),
            customer.get("phone"),
            customer.get("gstin"),
            customer.get("email"),
        )
        if query_value and not any(query_value in _normalized(field) for field in searchable_fields):
            continue

        last_sale = sales_by_id.get(customer.get("last_sale_id") or "")
        last_invoice = invoices_by_id.get(last_sale["invoice_id"]) if last_sale else None
        records.append(
            {
                "customer_id": customer["id"],
                "name": customer["name"],
                "phone": customer["phone"],
                "gstin": customer.get("gstin"),
                "visit_count": int(customer.get("visit_count", 0)),
                "lifetime_value": _money(customer.get("lifetime_value", 0.0)),
                "last_sale_id": customer.get("last_sale_id"),
                "last_invoice_number": last_invoice["invoice_number"] if last_invoice else None,
                "last_branch_id": last_sale["branch_id"] if last_sale else None,
            }
        )
    return sorted(records, key=lambda record: (record["name"], record["phone"]))


def build_customer_history_report(
    *,
    customer: dict[str, Any],
    sales: Iterable[dict[str, Any]],
    invoices_by_id: dict[str, dict[str, Any]],
    sale_returns: Iterable[dict[str, Any]],
    credit_notes_by_id: dict[str, dict[str, Any]],
    exchange_orders: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    customer_sales = [sale for sale in sales if sale.get("customer_id") == customer["id"]]
    customer_sale_ids = {sale["id"] for sale in customer_sales}
    sales_records = [
        {
            "sale_id": sale["id"],
            "branch_id": sale["branch_id"],
            "invoice_id": sale["invoice_id"],
            "invoice_number": invoices_by_id[sale["invoice_id"]]["invoice_number"],
            "grand_total": _money(invoices_by_id[sale["invoice_id"]]["grand_total"]),
            "payment_method": sale["payment_method"],
        }
        for sale in customer_sales
    ]
    return_records = []
    for sale_return in sale_returns:
        if sale_return["sale_id"] not in customer_sale_ids:
            continue
        credit_note = credit_notes_by_id[sale_return["credit_note_id"]]
        return_records.append(
            {
                "sale_return_id": sale_return["id"],
                "sale_id": sale_return["sale_id"],
                "branch_id": sale_return["branch_id"],
                "credit_note_id": credit_note["id"],
                "credit_note_number": credit_note["credit_note_number"],
                "grand_total": _money(credit_note["grand_total"]),
                "refund_amount": _money(sale_return["refund_amount"]),
                "status": sale_return["status"],
            }
        )
    exchange_records = [
        {
            "exchange_order_id": exchange_order["id"],
            "sale_id": exchange_order["sale_id"],
            "branch_id": exchange_order["branch_id"],
            "return_total": _money(exchange_order["return_total"]),
            "replacement_total": _money(exchange_order["replacement_total"]),
            "balance_direction": exchange_order["balance_direction"],
            "balance_amount": _money(exchange_order["balance_amount"]),
        }
        for exchange_order in exchange_orders
        if exchange_order["sale_id"] in customer_sale_ids
    ]
    return {
        "customer": {
            "customer_id": customer["id"],
            "name": customer["name"],
            "phone": customer["phone"],
            "gstin": customer.get("gstin"),
            "visit_count": int(customer.get("visit_count", 0)),
            "lifetime_value": _money(customer.get("lifetime_value", 0.0)),
            "last_sale_id": customer.get("last_sale_id"),
        },
        "sales_summary": {
            "sales_count": len(sales_records),
            "sales_total": _money(sum(record["grand_total"] for record in sales_records)),
            "return_count": len(return_records),
            "credit_note_total": _money(sum(record["grand_total"] for record in return_records)),
            "exchange_count": len(exchange_records),
        },
        "sales": sales_records,
        "returns": return_records,
        "exchanges": exchange_records,
    }


def build_branch_customer_report(
    *,
    branch_id: str,
    customers_by_id: dict[str, dict[str, Any]],
    sales: Iterable[dict[str, Any]],
    invoices_by_id: dict[str, dict[str, Any]],
    sale_returns: Iterable[dict[str, Any]],
    credit_notes_by_id: dict[str, dict[str, Any]],
    exchange_orders: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    branch_sales = [sale for sale in sales if sale.get("branch_id") == branch_id]
    branch_sales_by_id = {sale["id"]: sale for sale in branch_sales}
    customer_records: dict[str, dict[str, Any]] = {}
    anonymous_sales_count = 0
    anonymous_sales_total = 0.0

    for sale in branch_sales:
        invoice = invoices_by_id.get(sale["invoice_id"], {})
        grand_total = _money(invoice.get("grand_total", 0.0))
        customer_id = sale.get("customer_id")
        if not customer_id:
            anonymous_sales_count += 1
            anonymous_sales_total += grand_total
            continue

        customer = customers_by_id.get(customer_id, {})
        record = customer_records.setdefault(
            customer_id,
            {
                "customer_id": customer_id,
                "customer_name": customer.get("name") or sale.get("customer_name") or customer_id,
                "sales_count": 0,
                "sales_total": 0.0,
                "last_invoice_number": None,
            },
        )
        record["sales_count"] += 1
        record["sales_total"] += grand_total
        record["last_invoice_number"] = invoice.get("invoice_number")

    return_activity: dict[str, dict[str, Any]] = {}
    for sale_return in sale_returns:
        sale = branch_sales_by_id.get(sale_return["sale_id"])
        if not sale or not sale.get("customer_id"):
            continue
        customer_id = sale["customer_id"]
        customer = customers_by_id.get(customer_id, {})
        credit_note = credit_notes_by_id.get(sale_return["credit_note_id"], {})
        record = return_activity.setdefault(
            customer_id,
            {
                "customer_id": customer_id,
                "customer_name": customer.get("name") or sale.get("customer_name") or customer_id,
                "return_count": 0,
                "credit_note_total": 0.0,
                "exchange_count": 0,
            },
        )
        record["return_count"] += 1
        record["credit_note_total"] += _money(credit_note.get("grand_total", 0.0))

    for exchange_order in exchange_orders:
        if exchange_order.get("branch_id") != branch_id:
            continue
        sale = branch_sales_by_id.get(exchange_order["sale_id"])
        if not sale or not sale.get("customer_id"):
            continue
        customer_id = sale["customer_id"]
        customer = customers_by_id.get(customer_id, {})
        record = return_activity.setdefault(
            customer_id,
            {
                "customer_id": customer_id,
                "customer_name": customer.get("name") or sale.get("customer_name") or customer_id,
                "return_count": 0,
                "credit_note_total": 0.0,
                "exchange_count": 0,
            },
        )
        record["exchange_count"] += 1

    top_customers = sorted(
        [
            {
                **record,
                "sales_total": _money(record["sales_total"]),
            }
            for record in customer_records.values()
        ],
        key=lambda record: (-record["sales_total"], -record["sales_count"], record["customer_name"]),
    )
    return_records = sorted(
        [
            {
                **record,
                "credit_note_total": _money(record["credit_note_total"]),
            }
            for record in return_activity.values()
            if record["return_count"] > 0 or record["exchange_count"] > 0
        ],
        key=lambda record: (-record["credit_note_total"], -record["exchange_count"], record["customer_name"]),
    )
    return {
        "branch_id": branch_id,
        "customer_count": len(customer_records),
        "repeat_customer_count": sum(1 for record in customer_records.values() if record["sales_count"] > 1),
        "anonymous_sales_count": anonymous_sales_count,
        "anonymous_sales_total": _money(anonymous_sales_total),
        "top_customers": top_customers,
        "return_activity": return_records,
    }
