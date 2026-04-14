from __future__ import annotations

from datetime import date
from typing import Any

from .supplier_settlement_blockers import build_supplier_settlement_blocker_report
from .vendor_disputes import build_vendor_dispute_board


def _money(value: float) -> float:
    return round(float(value), 2)


def _escalation_priority(status: str) -> int:
    if status == "FINANCE_ESCALATION":
        return 0
    if status == "OWNER_ESCALATION":
        return 1
    if status == "STALE_CASE":
        return 2
    return 3


def _derive_escalation(
    *,
    age_days: int,
    overdue: bool,
    hold_status: str | None,
    blocked_release_now_total: float,
    blocked_release_this_week_total: float,
    blocked_outstanding_total: float,
) -> tuple[str, str, str]:
    if hold_status == "HARD_HOLD" or blocked_release_now_total > 0:
        return (
            "FINANCE_ESCALATION",
            "finance_admin",
            "Freeze release and resolve invoice dispute before payment",
        )
    if age_days > 14 and hold_status is None and blocked_outstanding_total == 0:
        return (
            "STALE_CASE",
            "tenant_owner",
            "Escalate stale dispute and request supplier resolution date",
        )
    if hold_status == "SOFT_HOLD" or blocked_release_this_week_total > 0 or overdue:
        return (
            "OWNER_ESCALATION",
            "tenant_owner",
            "Owner follow-up before the next payment window",
        )
    return (
        "BRANCH_FOLLOW_UP",
        "store_manager",
        "Branch follow-up and update dispute status",
    )


def build_supplier_escalation_report(
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
    dispute_board = build_vendor_dispute_board(
        branch_id=branch_id,
        as_of_date=as_of_date,
        vendor_disputes=vendor_disputes,
        goods_receipts=goods_receipts,
        purchase_invoices=purchase_invoices,
        suppliers_by_id=suppliers_by_id,
    )
    blocker_report = build_supplier_settlement_blocker_report(
        branch_id=branch_id,
        as_of_date=as_of_date,
        purchase_invoices=purchase_invoices,
        supplier_returns=supplier_returns,
        supplier_payments=supplier_payments,
        vendor_disputes=vendor_disputes,
        goods_receipts=goods_receipts,
        suppliers_by_id=suppliers_by_id,
    )

    blockers_by_supplier_id = {
        record["supplier_id"]: record for record in blocker_report["records"]
    }

    records: list[dict[str, Any]] = []
    for dispute_record in dispute_board["records"]:
        if dispute_record["status"] != "OPEN":
            continue

        blocker = blockers_by_supplier_id.get(dispute_record["supplier_id"])
        hold_status = blocker["hold_status"] if blocker else None
        blocked_release_now_total = blocker["release_now_total"] if blocker else 0.0
        blocked_release_this_week_total = blocker["release_this_week_total"] if blocker else 0.0
        blocked_outstanding_total = blocker["outstanding_total"] if blocker else 0.0
        next_due_invoice_number = blocker["next_due_invoice_number"] if blocker else None
        most_urgent_status = blocker["most_urgent_status"] if blocker else None

        escalation_status, escalation_target, next_action = _derive_escalation(
            age_days=dispute_record["age_days"],
            overdue=dispute_record["overdue"],
            hold_status=hold_status,
            blocked_release_now_total=blocked_release_now_total,
            blocked_release_this_week_total=blocked_release_this_week_total,
            blocked_outstanding_total=blocked_outstanding_total,
        )

        records.append(
            {
                "dispute_id": dispute_record["dispute_id"],
                "supplier_id": dispute_record["supplier_id"],
                "supplier_name": dispute_record["supplier_name"],
                "reference_type": dispute_record["reference_type"],
                "reference_number": dispute_record["reference_number"],
                "dispute_type": dispute_record["dispute_type"],
                "opened_on": dispute_record["opened_on"],
                "age_days": dispute_record["age_days"],
                "overdue": dispute_record["overdue"],
                "hold_status": hold_status,
                "blocked_release_now_total": _money(blocked_release_now_total),
                "blocked_release_this_week_total": _money(blocked_release_this_week_total),
                "blocked_outstanding_total": _money(blocked_outstanding_total),
                "next_due_invoice_number": next_due_invoice_number,
                "most_urgent_status": most_urgent_status,
                "escalation_status": escalation_status,
                "escalation_target": escalation_target,
                "next_action": next_action,
            }
        )

    records.sort(
        key=lambda record: (
            _escalation_priority(record["escalation_status"]),
            -record["blocked_release_now_total"],
            -record["blocked_release_this_week_total"],
            -record["age_days"],
            record["supplier_name"],
            record["dispute_id"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "open_case_count": len(records),
        "finance_escalation_count": sum(1 for record in records if record["escalation_status"] == "FINANCE_ESCALATION"),
        "owner_escalation_count": sum(1 for record in records if record["escalation_status"] == "OWNER_ESCALATION"),
        "stale_case_count": sum(1 for record in records if record["escalation_status"] == "STALE_CASE"),
        "branch_follow_up_count": sum(1 for record in records if record["escalation_status"] == "BRANCH_FOLLOW_UP"),
        "blocked_release_now_total": _money(sum(record["blocked_release_now_total"] for record in records)),
        "blocked_release_this_week_total": _money(sum(record["blocked_release_this_week_total"] for record in records)),
        "blocked_outstanding_total": _money(sum(record["blocked_outstanding_total"] for record in records)),
        "records": records,
    }
