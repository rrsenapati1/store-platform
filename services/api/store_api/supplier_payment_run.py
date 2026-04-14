from __future__ import annotations

from datetime import date
from typing import Any

from .supplier_due_schedule import build_supplier_due_schedule


def _money(value: float) -> float:
    return round(float(value), 2)


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
