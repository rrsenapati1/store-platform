from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def _parse_invoice_date(raw_value: Any, *, as_of_date: date) -> date:
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return as_of_date
    return as_of_date


def _aging_bucket(invoice_age_days: int) -> str:
    if invoice_age_days <= 0:
        return "CURRENT"
    if invoice_age_days <= 30:
        return "1_30_DAYS"
    if invoice_age_days <= 60:
        return "31_60_DAYS"
    return "61_PLUS_DAYS"


def build_supplier_aging_report(
    *,
    branch_id: str,
    as_of_date: date,
    purchase_invoices: Iterable[dict[str, Any]],
    supplier_returns: Iterable[dict[str, Any]],
    supplier_payments: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    credit_note_totals_by_invoice_id: dict[str, float] = {}
    for supplier_return in supplier_returns:
        purchase_invoice_id = supplier_return["purchase_invoice_id"]
        credit_note_totals_by_invoice_id[purchase_invoice_id] = _money(
            credit_note_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + supplier_return["grand_total"]
        )

    paid_totals_by_invoice_id: dict[str, float] = {}
    for supplier_payment in supplier_payments:
        purchase_invoice_id = supplier_payment["purchase_invoice_id"]
        paid_totals_by_invoice_id[purchase_invoice_id] = _money(
            paid_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + supplier_payment["amount"]
        )

    records: list[dict[str, Any]] = []
    current_total = 0.0
    days_1_30_total = 0.0
    days_31_60_total = 0.0
    days_61_plus_total = 0.0

    for purchase_invoice in purchase_invoices:
        if purchase_invoice["branch_id"] != branch_id:
            continue

        credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        paid_total = paid_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        outstanding_total = _money(max(0.0, purchase_invoice["grand_total"] - credit_note_total - paid_total))
        if outstanding_total == 0:
            continue

        invoice_date = _parse_invoice_date(purchase_invoice.get("invoice_date"), as_of_date=as_of_date)
        invoice_age_days = max(0, (as_of_date - invoice_date).days)
        aging_bucket = _aging_bucket(invoice_age_days)

        if aging_bucket == "CURRENT":
            current_total = _money(current_total + outstanding_total)
        elif aging_bucket == "1_30_DAYS":
            days_1_30_total = _money(days_1_30_total + outstanding_total)
        elif aging_bucket == "31_60_DAYS":
            days_31_60_total = _money(days_31_60_total + outstanding_total)
        else:
            days_61_plus_total = _money(days_61_plus_total + outstanding_total)

        supplier = suppliers_by_id.get(purchase_invoice["supplier_id"])
        records.append(
            {
                "purchase_invoice_id": purchase_invoice["id"],
                "purchase_invoice_number": purchase_invoice["invoice_number"],
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "invoice_date": invoice_date.isoformat(),
                "invoice_age_days": invoice_age_days,
                "grand_total": purchase_invoice["grand_total"],
                "credit_note_total": credit_note_total,
                "paid_total": paid_total,
                "outstanding_total": outstanding_total,
                "aging_bucket": aging_bucket,
            }
        )

    records.sort(
        key=lambda record: (
            -record["invoice_age_days"],
            -record["outstanding_total"],
            record["purchase_invoice_number"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "open_invoice_count": len(records),
        "current_total": current_total,
        "days_1_30_total": days_1_30_total,
        "days_31_60_total": days_31_60_total,
        "days_61_plus_total": days_61_plus_total,
        "outstanding_total": _money(current_total + days_1_30_total + days_31_60_total + days_61_plus_total),
        "records": records,
    }
