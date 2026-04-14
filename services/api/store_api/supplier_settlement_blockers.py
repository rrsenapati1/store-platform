from __future__ import annotations

from datetime import date
from typing import Any

from .supplier_exceptions import build_supplier_exception_report
from .supplier_payment_run import build_supplier_payment_run


def _money(value: float) -> float:
    return round(float(value), 2)


def _hold_priority(hold_status: str) -> int:
    if hold_status == "HARD_HOLD":
        return 0
    return 1


def build_supplier_settlement_blocker_report(
    *,
    branch_id: str,
    as_of_date: date,
    purchase_invoices: list[dict[str, Any]],
    supplier_returns: list[dict[str, Any]],
    supplier_payments: list[dict[str, Any]],
    vendor_disputes: list[dict[str, Any]],
    goods_receipts: list[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    payment_run = build_supplier_payment_run(
        branch_id=branch_id,
        as_of_date=as_of_date,
        purchase_invoices=purchase_invoices,
        supplier_returns=supplier_returns,
        supplier_payments=supplier_payments,
        suppliers_by_id=suppliers_by_id,
    )
    exception_report = build_supplier_exception_report(
        branch_id=branch_id,
        as_of_date=as_of_date,
        vendor_disputes=vendor_disputes,
        goods_receipts=goods_receipts,
        purchase_invoices=purchase_invoices,
        suppliers_by_id=suppliers_by_id,
    )

    exceptions_by_supplier_id = {
        record["supplier_id"]: record
        for record in exception_report["records"]
        if record["open_count"] > 0
    }

    records: list[dict[str, Any]] = []
    for payment_record in payment_run["records"]:
        if payment_record["outstanding_total"] <= 0:
            continue

        exception_record = exceptions_by_supplier_id.get(payment_record["supplier_id"])
        if exception_record is None:
            continue

        hold_status = "HARD_HOLD" if exception_record["overdue_open_count"] > 0 else "SOFT_HOLD"
        records.append(
            {
                "supplier_id": payment_record["supplier_id"],
                "supplier_name": payment_record["supplier_name"],
                "hold_status": hold_status,
                "open_dispute_count": exception_record["open_count"],
                "overdue_open_dispute_count": exception_record["overdue_open_count"],
                "latest_dispute_type": exception_record["latest_dispute_type"],
                "latest_reference_type": exception_record["latest_reference_type"],
                "latest_reference_number": exception_record["latest_reference_number"],
                "latest_opened_on": exception_record["latest_opened_on"],
                "outstanding_total": payment_record["outstanding_total"],
                "release_now_total": payment_record["release_now_total"],
                "release_this_week_total": payment_record["release_this_week_total"],
                "next_due_date": payment_record["next_due_date"],
                "next_due_invoice_number": payment_record["next_due_invoice_number"],
                "most_urgent_status": payment_record["most_urgent_status"],
            }
        )

    records.sort(
        key=lambda record: (
            _hold_priority(record["hold_status"]),
            -record["release_now_total"],
            -record["release_this_week_total"],
            record["next_due_date"] or "9999-12-31",
            record["supplier_name"],
            record["supplier_id"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "hard_hold_count": sum(1 for record in records if record["hold_status"] == "HARD_HOLD"),
        "soft_hold_count": sum(1 for record in records if record["hold_status"] == "SOFT_HOLD"),
        "blocked_release_now_total": _money(sum(record["release_now_total"] for record in records)),
        "blocked_release_this_week_total": _money(sum(record["release_this_week_total"] for record in records)),
        "blocked_outstanding_total": _money(sum(record["outstanding_total"] for record in records)),
        "records": records,
    }
