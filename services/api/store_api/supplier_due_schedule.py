from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def _parse_iso_date(raw_value: Any, *, fallback: date) -> date:
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return fallback
    return fallback


def compute_supplier_due_date(*, invoice_date: date, payment_terms_days: int) -> date:
    return invoice_date + timedelta(days=max(0, int(payment_terms_days)))


def _resolve_due_status(days_until_due: int) -> str:
    if days_until_due < 0:
        return "OVERDUE"
    if days_until_due == 0:
        return "DUE_TODAY"
    if days_until_due <= 7:
        return "DUE_IN_7_DAYS"
    if days_until_due <= 30:
        return "DUE_IN_8_30_DAYS"
    return "DUE_LATER"


def build_supplier_due_schedule(
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
    overdue_total = 0.0
    due_today_total = 0.0
    due_in_7_days_total = 0.0
    due_in_8_30_days_total = 0.0
    due_later_total = 0.0

    for purchase_invoice in purchase_invoices:
        if purchase_invoice["branch_id"] != branch_id:
            continue

        credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        paid_total = paid_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        outstanding_total = _money(max(0.0, purchase_invoice["grand_total"] - credit_note_total - paid_total))
        if outstanding_total == 0:
            continue

        supplier = suppliers_by_id.get(purchase_invoice["supplier_id"], {})
        invoice_date = _parse_iso_date(purchase_invoice.get("invoice_date"), fallback=as_of_date)
        payment_terms_days = int(purchase_invoice.get("payment_terms_days", supplier.get("payment_terms_days", 0)) or 0)
        due_date = _parse_iso_date(
            purchase_invoice.get("due_date"),
            fallback=compute_supplier_due_date(invoice_date=invoice_date, payment_terms_days=payment_terms_days),
        )
        days_until_due = (due_date - as_of_date).days
        due_status = _resolve_due_status(days_until_due)

        if due_status == "OVERDUE":
            overdue_total = _money(overdue_total + outstanding_total)
        elif due_status == "DUE_TODAY":
            due_today_total = _money(due_today_total + outstanding_total)
        elif due_status == "DUE_IN_7_DAYS":
            due_in_7_days_total = _money(due_in_7_days_total + outstanding_total)
        elif due_status == "DUE_IN_8_30_DAYS":
            due_in_8_30_days_total = _money(due_in_8_30_days_total + outstanding_total)
        else:
            due_later_total = _money(due_later_total + outstanding_total)

        records.append(
            {
                "purchase_invoice_id": purchase_invoice["id"],
                "purchase_invoice_number": purchase_invoice["invoice_number"],
                "supplier_id": purchase_invoice["supplier_id"],
                "supplier_name": supplier.get("name", "Unknown supplier"),
                "invoice_date": invoice_date.isoformat(),
                "due_date": due_date.isoformat(),
                "payment_terms_days": payment_terms_days,
                "grand_total": purchase_invoice["grand_total"],
                "credit_note_total": credit_note_total,
                "paid_total": paid_total,
                "outstanding_total": outstanding_total,
                "days_until_due": days_until_due,
                "due_status": due_status,
            }
        )

    records.sort(
        key=lambda record: (
            record["due_date"],
            -record["outstanding_total"],
            record["purchase_invoice_number"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "open_invoice_count": len(records),
        "overdue_invoice_count": sum(1 for record in records if record["due_status"] == "OVERDUE"),
        "overdue_total": overdue_total,
        "due_today_total": due_today_total,
        "due_in_7_days_total": due_in_7_days_total,
        "due_in_8_30_days_total": due_in_8_30_days_total,
        "due_later_total": due_later_total,
        "outstanding_total": _money(
            overdue_total + due_today_total + due_in_7_days_total + due_in_8_30_days_total + due_later_total
        ),
        "records": records,
    }
