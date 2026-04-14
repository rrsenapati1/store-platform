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


def _apply_bucket_totals(record: dict[str, Any], *, outstanding_total: float, invoice_age_days: int) -> None:
    if invoice_age_days <= 0:
        record["current_total"] = _money(record["current_total"] + outstanding_total)
    elif invoice_age_days <= 30:
        record["days_1_30_total"] = _money(record["days_1_30_total"] + outstanding_total)
    elif invoice_age_days <= 60:
        record["days_31_60_total"] = _money(record["days_31_60_total"] + outstanding_total)
    else:
        record["days_61_plus_total"] = _money(record["days_61_plus_total"] + outstanding_total)


def build_supplier_statement_report(
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

    records_by_supplier_id: dict[str, dict[str, Any]] = {}
    for purchase_invoice in purchase_invoices:
        if purchase_invoice["branch_id"] != branch_id:
            continue

        supplier_id = purchase_invoice["supplier_id"]
        supplier = suppliers_by_id.get(supplier_id)
        record = records_by_supplier_id.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "invoice_count": 0,
                "open_invoice_count": 0,
                "invoiced_total": 0.0,
                "credit_note_total": 0.0,
                "paid_total": 0.0,
                "outstanding_total": 0.0,
                "current_total": 0.0,
                "days_1_30_total": 0.0,
                "days_31_60_total": 0.0,
                "days_61_plus_total": 0.0,
                "oldest_open_invoice_date": None,
                "oldest_open_invoice_number": None,
            },
        )

        invoice_credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_paid_total = paid_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_outstanding_total = _money(max(0.0, purchase_invoice["grand_total"] - invoice_credit_note_total - invoice_paid_total))
        invoice_date = _parse_invoice_date(purchase_invoice.get("invoice_date"), as_of_date=as_of_date)
        invoice_age_days = max(0, (as_of_date - invoice_date).days)

        record["invoice_count"] += 1
        record["invoiced_total"] = _money(record["invoiced_total"] + purchase_invoice["grand_total"])
        record["credit_note_total"] = _money(record["credit_note_total"] + invoice_credit_note_total)
        record["paid_total"] = _money(record["paid_total"] + invoice_paid_total)
        record["outstanding_total"] = _money(record["outstanding_total"] + invoice_outstanding_total)

        if invoice_outstanding_total > 0:
            record["open_invoice_count"] += 1
            _apply_bucket_totals(record, outstanding_total=invoice_outstanding_total, invoice_age_days=invoice_age_days)
            oldest_open_invoice_date = record["oldest_open_invoice_date"]
            if oldest_open_invoice_date is None or invoice_date.isoformat() < oldest_open_invoice_date:
                record["oldest_open_invoice_date"] = invoice_date.isoformat()
                record["oldest_open_invoice_number"] = purchase_invoice["invoice_number"]

    records = list(records_by_supplier_id.values())
    records.sort(
        key=lambda record: (
            -record["outstanding_total"],
            record["oldest_open_invoice_date"] or "9999-12-31",
            record["supplier_name"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "open_supplier_count": sum(1 for record in records if record["outstanding_total"] > 0),
        "outstanding_total": _money(sum(record["outstanding_total"] for record in records)),
        "records": records,
    }
