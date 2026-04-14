from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from typing import Any

from .supplier_due_schedule import build_supplier_due_schedule


def _money(value: float) -> float:
    return round(float(value), 2)


def _parse_payment_date(raw_value: Any) -> date | None:
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return None
    return None


def _risk_status(*, overdue_total: float, due_in_7_days_total: float, days_since_last_payment: int | None) -> str:
    if overdue_total > 0:
        return "HIGH"
    if due_in_7_days_total > 0:
        return "WATCH"
    if days_since_last_payment is None:
        return "WATCH"
    if days_since_last_payment > 30:
        return "WATCH"
    return "OK"


def build_supplier_settlement_report(
    *,
    branch_id: str,
    as_of_date: date,
    purchase_invoices: Iterable[dict[str, Any]],
    supplier_returns: Iterable[dict[str, Any]],
    supplier_payments: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    due_schedule = build_supplier_due_schedule(
        branch_id=branch_id,
        as_of_date=as_of_date,
        purchase_invoices=purchase_invoices,
        supplier_returns=supplier_returns,
        supplier_payments=supplier_payments,
        suppliers_by_id=suppliers_by_id,
    )

    summary_by_supplier_id: dict[str, dict[str, Any]] = {}
    for invoice_record in due_schedule["records"]:
        supplier_id = invoice_record["supplier_id"]
        supplier = suppliers_by_id.get(supplier_id, {})
        summary = summary_by_supplier_id.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", "Unknown supplier"),
                "outstanding_total": 0.0,
                "overdue_total": 0.0,
                "due_in_7_days_total": 0.0,
                "latest_payment_date": None,
                "latest_payment_number": None,
                "latest_payment_method": None,
                "latest_payment_reference": None,
                "latest_payment_amount": None,
                "days_since_last_payment": None,
                "risk_status": "OK",
            },
        )
        summary["outstanding_total"] = _money(summary["outstanding_total"] + invoice_record["outstanding_total"])

        due_status = invoice_record["due_status"]
        if due_status == "OVERDUE":
            summary["overdue_total"] = _money(summary["overdue_total"] + invoice_record["outstanding_total"])
        elif due_status in ("DUE_TODAY", "DUE_IN_7_DAYS"):
            summary["due_in_7_days_total"] = _money(
                summary["due_in_7_days_total"] + invoice_record["outstanding_total"]
            )

    payments_by_supplier_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for supplier_payment in supplier_payments:
        if supplier_payment["branch_id"] != branch_id:
            continue
        if supplier_payment["supplier_id"] not in summary_by_supplier_id:
            continue
        payments_by_supplier_id[supplier_payment["supplier_id"]].append(supplier_payment)

    for supplier_id, summary in summary_by_supplier_id.items():
        payment_candidates = payments_by_supplier_id.get(supplier_id, [])
        if payment_candidates:
            latest_payment = max(
                payment_candidates,
                key=lambda payment: (
                    payment.get("payment_date") or "",
                    payment.get("payment_number") or "",
                    payment.get("id") or "",
                ),
            )
            summary["latest_payment_date"] = latest_payment.get("payment_date")
            summary["latest_payment_number"] = latest_payment.get("payment_number")
            summary["latest_payment_method"] = latest_payment.get("payment_method")
            summary["latest_payment_reference"] = latest_payment.get("reference")
            summary["latest_payment_amount"] = _money(latest_payment["amount"])
            parsed_date = _parse_payment_date(latest_payment.get("payment_date"))
            if parsed_date is not None:
                summary["days_since_last_payment"] = max(0, (as_of_date - parsed_date).days)

        summary["risk_status"] = _risk_status(
            overdue_total=summary["overdue_total"],
            due_in_7_days_total=summary["due_in_7_days_total"],
            days_since_last_payment=summary["days_since_last_payment"],
        )

    risk_order = {"HIGH": 2, "WATCH": 1, "OK": 0}
    records = list(summary_by_supplier_id.values())
    records.sort(
        key=lambda record: (
            -risk_order.get(record["risk_status"], 0),
            -record["overdue_total"],
            -record["due_in_7_days_total"],
            -(record["days_since_last_payment"] or -1),
            record["supplier_name"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "overdue_total": _money(sum(record["overdue_total"] for record in records)),
        "due_in_7_days_total": _money(sum(record["due_in_7_days_total"] for record in records)),
        "outstanding_total": _money(sum(record["outstanding_total"] for record in records)),
        "records": records,
    }
