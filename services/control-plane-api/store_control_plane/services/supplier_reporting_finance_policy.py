from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

from .procurement_finance_policy import build_supplier_payables_report


def _money(value: float) -> float:
    return round(float(value), 2)


def _parse_iso_date(raw_value: Any, *, fallback: date | None = None) -> date | None:
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

        invoice_date = _parse_iso_date(purchase_invoice.get("invoice_date"), fallback=as_of_date) or as_of_date
        invoice_age_days = max(0, (as_of_date - invoice_date).days)
        aging_bucket = (
            "CURRENT"
            if invoice_age_days <= 0
            else "1_30_DAYS"
            if invoice_age_days <= 30
            else "31_60_DAYS"
            if invoice_age_days <= 60
            else "61_PLUS_DAYS"
        )

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
        invoice_date = _parse_iso_date(purchase_invoice.get("invoice_date"), fallback=as_of_date) or as_of_date
        invoice_age_days = max(0, (as_of_date - invoice_date).days)

        record["invoice_count"] += 1
        record["invoiced_total"] = _money(record["invoiced_total"] + purchase_invoice["grand_total"])
        record["credit_note_total"] = _money(record["credit_note_total"] + invoice_credit_note_total)
        record["paid_total"] = _money(record["paid_total"] + invoice_paid_total)
        record["outstanding_total"] = _money(record["outstanding_total"] + invoice_outstanding_total)

        if invoice_outstanding_total > 0:
            record["open_invoice_count"] += 1
            if invoice_age_days <= 0:
                record["current_total"] = _money(record["current_total"] + invoice_outstanding_total)
            elif invoice_age_days <= 30:
                record["days_1_30_total"] = _money(record["days_1_30_total"] + invoice_outstanding_total)
            elif invoice_age_days <= 60:
                record["days_31_60_total"] = _money(record["days_31_60_total"] + invoice_outstanding_total)
            else:
                record["days_61_plus_total"] = _money(record["days_61_plus_total"] + invoice_outstanding_total)
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
        invoice_date = _parse_iso_date(purchase_invoice.get("invoice_date"), fallback=as_of_date) or as_of_date
        payment_terms_days = int(purchase_invoice.get("payment_terms_days", supplier.get("payment_terms_days", 0)) or 0)
        due_date = _parse_iso_date(
            purchase_invoice.get("due_date"),
            fallback=compute_supplier_due_date(invoice_date=invoice_date, payment_terms_days=payment_terms_days),
        ) or compute_supplier_due_date(invoice_date=invoice_date, payment_terms_days=payment_terms_days)
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


def build_supplier_payment_run(
    *,
    branch_id: str,
    as_of_date: date,
    purchase_invoices: list[dict[str, Any]],
    supplier_returns: list[dict[str, Any]],
    supplier_payments: list[dict[str, Any]],
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

    records_by_supplier_id: dict[str, dict[str, Any]] = {}
    for invoice_record in due_schedule["records"]:
        supplier_id = invoice_record["supplier_id"]
        supplier_record = records_by_supplier_id.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": invoice_record["supplier_name"],
                "open_invoice_count": 0,
                "overdue_total": 0.0,
                "due_today_total": 0.0,
                "due_in_7_days_total": 0.0,
                "due_in_8_30_days_total": 0.0,
                "due_later_total": 0.0,
                "release_now_total": 0.0,
                "release_this_week_total": 0.0,
                "release_this_month_total": 0.0,
                "outstanding_total": 0.0,
                "next_due_date": None,
                "next_due_invoice_number": None,
                "most_urgent_status": None,
            },
        )
        supplier_record["open_invoice_count"] += 1
        supplier_record["outstanding_total"] = _money(
            supplier_record["outstanding_total"] + invoice_record["outstanding_total"]
        )

        due_status = invoice_record["due_status"]
        if due_status == "OVERDUE":
            supplier_record["overdue_total"] = _money(
                supplier_record["overdue_total"] + invoice_record["outstanding_total"]
            )
        elif due_status == "DUE_TODAY":
            supplier_record["due_today_total"] = _money(
                supplier_record["due_today_total"] + invoice_record["outstanding_total"]
            )
        elif due_status == "DUE_IN_7_DAYS":
            supplier_record["due_in_7_days_total"] = _money(
                supplier_record["due_in_7_days_total"] + invoice_record["outstanding_total"]
            )
        elif due_status == "DUE_IN_8_30_DAYS":
            supplier_record["due_in_8_30_days_total"] = _money(
                supplier_record["due_in_8_30_days_total"] + invoice_record["outstanding_total"]
            )
        else:
            supplier_record["due_later_total"] = _money(
                supplier_record["due_later_total"] + invoice_record["outstanding_total"]
            )

        supplier_record["release_now_total"] = _money(
            supplier_record["overdue_total"] + supplier_record["due_today_total"]
        )
        supplier_record["release_this_week_total"] = _money(
            supplier_record["release_now_total"] + supplier_record["due_in_7_days_total"]
        )
        supplier_record["release_this_month_total"] = _money(
            supplier_record["release_this_week_total"] + supplier_record["due_in_8_30_days_total"]
        )

        next_due_date = supplier_record["next_due_date"]
        if next_due_date is None or invoice_record["due_date"] < next_due_date:
            supplier_record["next_due_date"] = invoice_record["due_date"]
            supplier_record["next_due_invoice_number"] = invoice_record["purchase_invoice_number"]
            supplier_record["most_urgent_status"] = due_status

    records = list(records_by_supplier_id.values())
    records.sort(
        key=lambda record: (
            -record["release_now_total"],
            record["next_due_date"] or "9999-12-31",
            -record["outstanding_total"],
            record["supplier_name"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "release_now_total": _money(sum(record["release_now_total"] for record in records)),
        "release_this_week_total": _money(sum(record["release_this_week_total"] for record in records)),
        "release_this_month_total": _money(sum(record["release_this_month_total"] for record in records)),
        "outstanding_total": _money(sum(record["outstanding_total"] for record in records)),
        "records": records,
    }


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
            parsed_date = _parse_iso_date(latest_payment.get("payment_date"))
            if parsed_date is not None:
                summary["days_since_last_payment"] = max(0, (as_of_date - parsed_date).days)

        if summary["overdue_total"] > 0:
            summary["risk_status"] = "HIGH"
        elif summary["due_in_7_days_total"] > 0 or summary["days_since_last_payment"] is None or summary["days_since_last_payment"] > 30:
            summary["risk_status"] = "WATCH"
        else:
            summary["risk_status"] = "OK"

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


def build_supplier_payment_activity_report(
    *,
    branch_id: str,
    as_of_date: date,
    supplier_payments: Iterable[dict[str, Any]],
    purchase_invoices: Iterable[dict[str, Any]],
    supplier_returns: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    purchase_invoices_by_id = {
        purchase_invoice["id"]: purchase_invoice
        for purchase_invoice in purchase_invoices
        if purchase_invoice["branch_id"] == branch_id
    }
    credit_note_totals_by_invoice_id: dict[str, float] = {}
    for supplier_return in supplier_returns:
        purchase_invoice_id = supplier_return["purchase_invoice_id"]
        if purchase_invoice_id not in purchase_invoices_by_id:
            continue
        credit_note_totals_by_invoice_id[purchase_invoice_id] = _money(
            credit_note_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + supplier_return["grand_total"]
        )

    paid_totals_by_invoice_id: dict[str, float] = defaultdict(float)
    payments_by_supplier_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for supplier_payment in supplier_payments:
        if supplier_payment["branch_id"] != branch_id:
            continue
        purchase_invoice_id = supplier_payment["purchase_invoice_id"]
        if purchase_invoice_id not in purchase_invoices_by_id:
            continue
        paid_totals_by_invoice_id[purchase_invoice_id] = _money(
            paid_totals_by_invoice_id[purchase_invoice_id] + supplier_payment["amount"]
        )
        payments_by_supplier_id[supplier_payment["supplier_id"]].append(supplier_payment)

    outstanding_totals_by_supplier_id: dict[str, float] = defaultdict(float)
    for purchase_invoice in purchase_invoices_by_id.values():
        invoice_credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_paid_total = paid_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_outstanding_total = _money(max(0.0, purchase_invoice["grand_total"] - invoice_credit_note_total - invoice_paid_total))
        outstanding_totals_by_supplier_id[purchase_invoice["supplier_id"]] = _money(
            outstanding_totals_by_supplier_id[purchase_invoice["supplier_id"]] + invoice_outstanding_total
        )

    recent_cutoff = as_of_date - timedelta(days=29)
    records: list[dict[str, Any]] = []
    for supplier_id, supplier_payments_for_supplier in payments_by_supplier_id.items():
        supplier = suppliers_by_id.get(supplier_id, {})
        sorted_payments = sorted(
            supplier_payments_for_supplier,
            key=lambda payment: (
                payment.get("payment_date") or "",
                payment.get("payment_number") or "",
                payment.get("id") or "",
            ),
            reverse=True,
        )
        last_payment = sorted_payments[0]
        paid_total = _money(sum(payment["amount"] for payment in supplier_payments_for_supplier))
        recent_paid_total = 0.0
        for payment in supplier_payments_for_supplier:
            payment_date = _parse_iso_date(payment.get("payment_date"))
            if payment_date is not None and payment_date > recent_cutoff:
                recent_paid_total = _money(recent_paid_total + payment["amount"])

        records.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", "Unknown supplier"),
                "payment_count": len(supplier_payments_for_supplier),
                "paid_total": paid_total,
                "recent_30_days_paid_total": recent_paid_total,
                "average_payment_value": _money(paid_total / len(supplier_payments_for_supplier)),
                "outstanding_total": outstanding_totals_by_supplier_id.get(supplier_id, 0.0),
                "last_payment_date": last_payment.get("payment_date"),
                "last_payment_number": last_payment.get("payment_number"),
                "last_payment_method": last_payment.get("payment_method"),
                "last_payment_reference": last_payment.get("reference"),
                "last_payment_amount": _money(last_payment["amount"]),
            }
        )

    records.sort(
        key=lambda record: (
            record["last_payment_date"] or "",
            record["last_payment_number"] or "",
            record["supplier_name"],
        ),
        reverse=True,
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "payment_count": sum(record["payment_count"] for record in records),
        "paid_total": _money(sum(record["paid_total"] for record in records)),
        "recent_30_days_paid_total": _money(sum(record["recent_30_days_paid_total"] for record in records)),
        "records": records,
    }
