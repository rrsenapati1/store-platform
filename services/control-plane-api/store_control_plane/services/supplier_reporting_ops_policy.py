from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from typing import Any

from .supplier_reporting_finance_policy import build_supplier_payment_run


def _money(value: float) -> float:
    return round(float(value), 2)


def _parse_iso_date(raw_value: Any) -> date | None:
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return None
    return None


def _resolve_reference(
    dispute: dict[str, Any],
    *,
    goods_receipts_by_id: dict[str, dict[str, Any]],
    purchase_invoices_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str | None]:
    purchase_invoice_id = dispute.get("purchase_invoice_id")
    if purchase_invoice_id:
        purchase_invoice = purchase_invoices_by_id.get(purchase_invoice_id)
        return "purchase_invoice", purchase_invoice.get("invoice_number") if purchase_invoice else purchase_invoice_id

    goods_receipt_id = dispute.get("goods_receipt_id")
    goods_receipt = goods_receipts_by_id.get(goods_receipt_id)
    return "goods_receipt", goods_receipt.get("goods_receipt_number") if goods_receipt else goods_receipt_id


def build_vendor_dispute_board(
    *,
    branch_id: str,
    as_of_date: date,
    vendor_disputes: Iterable[dict[str, Any]],
    goods_receipts: Iterable[dict[str, Any]],
    purchase_invoices: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    goods_receipts_by_id = {goods_receipt["id"]: goods_receipt for goods_receipt in goods_receipts}
    purchase_invoices_by_id = {purchase_invoice["id"]: purchase_invoice for purchase_invoice in purchase_invoices}

    records: list[dict[str, Any]] = []
    open_count = 0
    resolved_count = 0
    overdue_open_count = 0

    for dispute in vendor_disputes:
        if dispute["branch_id"] != branch_id:
            continue

        opened_on = _parse_iso_date(dispute.get("opened_on"))
        age_days = max(0, (as_of_date - opened_on).days) if opened_on else 0
        is_open = dispute.get("status") == "OPEN"
        overdue = is_open and age_days > 7
        if is_open:
            open_count += 1
            if overdue:
                overdue_open_count += 1
        else:
            resolved_count += 1

        reference_type, reference_number = _resolve_reference(
            dispute,
            goods_receipts_by_id=goods_receipts_by_id,
            purchase_invoices_by_id=purchase_invoices_by_id,
        )
        supplier = suppliers_by_id.get(dispute["supplier_id"])

        records.append(
            {
                "dispute_id": dispute["id"],
                "supplier_id": dispute["supplier_id"],
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "reference_type": reference_type,
                "reference_number": reference_number,
                "dispute_type": dispute["dispute_type"],
                "status": dispute["status"],
                "opened_on": dispute.get("opened_on"),
                "resolved_on": dispute.get("resolved_on"),
                "age_days": age_days,
                "overdue": overdue,
                "note": dispute.get("note"),
                "resolution_note": dispute.get("resolution_note"),
            }
        )

    records.sort(
        key=lambda record: (
            0 if record["status"] == "OPEN" else 1,
            -int(record["overdue"]),
            -record["age_days"],
            record["supplier_name"],
            record["dispute_id"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "open_count": open_count,
        "resolved_count": resolved_count,
        "overdue_open_count": overdue_open_count,
        "records": records,
    }


def build_supplier_exception_report(
    *,
    branch_id: str,
    as_of_date: date,
    vendor_disputes: Iterable[dict[str, Any]],
    goods_receipts: Iterable[dict[str, Any]],
    purchase_invoices: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    goods_receipts_by_id = {goods_receipt["id"]: goods_receipt for goods_receipt in goods_receipts}
    purchase_invoices_by_id = {purchase_invoice["id"]: purchase_invoice for purchase_invoice in purchase_invoices}

    grouped: dict[str, dict[str, Any]] = {}
    for dispute in vendor_disputes:
        if dispute["branch_id"] != branch_id:
            continue

        supplier_id = dispute["supplier_id"]
        supplier = suppliers_by_id.get(supplier_id)
        group = grouped.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "dispute_count": 0,
                "open_count": 0,
                "resolved_count": 0,
                "overdue_open_count": 0,
                "latest_dispute_type": None,
                "latest_reference_type": None,
                "latest_reference_number": None,
                "latest_opened_on": None,
                "_latest_opened_date": None,
            },
        )

        group["dispute_count"] += 1
        opened_on = _parse_iso_date(dispute.get("opened_on"))
        is_open = dispute.get("status") == "OPEN"
        if is_open:
            group["open_count"] += 1
            if opened_on and (as_of_date - opened_on).days > 7:
                group["overdue_open_count"] += 1
        else:
            group["resolved_count"] += 1

        if group["_latest_opened_date"] is None or (opened_on and opened_on >= group["_latest_opened_date"]):
            reference_type, reference_number = _resolve_reference(
                dispute,
                goods_receipts_by_id=goods_receipts_by_id,
                purchase_invoices_by_id=purchase_invoices_by_id,
            )
            group["latest_dispute_type"] = dispute.get("dispute_type")
            group["latest_reference_type"] = reference_type
            group["latest_reference_number"] = reference_number
            group["latest_opened_on"] = opened_on.isoformat() if opened_on else dispute.get("opened_on")
            group["_latest_opened_date"] = opened_on

    records: list[dict[str, Any]] = []
    suppliers_with_open_disputes = 0
    suppliers_with_overdue_disputes = 0

    for group in grouped.values():
        if group["open_count"] > 0:
            suppliers_with_open_disputes += 1
        if group["overdue_open_count"] > 0:
            suppliers_with_overdue_disputes += 1

        status = "RESOLVED"
        if group["overdue_open_count"] > 0:
            status = "ATTENTION"
        elif group["open_count"] > 0:
            status = "OPEN"

        records.append(
            {
                "supplier_id": group["supplier_id"],
                "supplier_name": group["supplier_name"],
                "dispute_count": group["dispute_count"],
                "open_count": group["open_count"],
                "resolved_count": group["resolved_count"],
                "overdue_open_count": group["overdue_open_count"],
                "latest_dispute_type": group["latest_dispute_type"],
                "latest_reference_type": group["latest_reference_type"],
                "latest_reference_number": group["latest_reference_number"],
                "latest_opened_on": group["latest_opened_on"],
                "status": status,
            }
        )

    records.sort(
        key=lambda record: (
            0 if record["status"] == "ATTENTION" else 1 if record["status"] == "OPEN" else 2,
            -(date.fromisoformat(record["latest_opened_on"]).toordinal() if record["latest_opened_on"] else 0),
            record["supplier_name"],
            record["supplier_id"],
        )
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "suppliers_with_open_disputes": suppliers_with_open_disputes,
        "suppliers_with_overdue_disputes": suppliers_with_overdue_disputes,
        "records": records,
    }


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
            0 if record["hold_status"] == "HARD_HOLD" else 1,
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

    blockers_by_supplier_id = {record["supplier_id"]: record for record in blocker_report["records"]}
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

        if hold_status == "HARD_HOLD" or blocked_release_now_total > 0:
            escalation_status, escalation_target, next_action = (
                "FINANCE_ESCALATION",
                "finance_admin",
                "Freeze release and resolve invoice dispute before payment",
            )
        elif dispute_record["age_days"] > 14 and hold_status is None and blocked_outstanding_total == 0:
            escalation_status, escalation_target, next_action = (
                "STALE_CASE",
                "tenant_owner",
                "Escalate stale dispute and request supplier resolution date",
            )
        elif hold_status == "SOFT_HOLD" or blocked_release_this_week_total > 0 or dispute_record["overdue"]:
            escalation_status, escalation_target, next_action = (
                "OWNER_ESCALATION",
                "tenant_owner",
                "Owner follow-up before the next payment window",
            )
        else:
            escalation_status, escalation_target, next_action = (
                "BRANCH_FOLLOW_UP",
                "store_manager",
                "Branch follow-up and update dispute status",
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

    priority = {"FINANCE_ESCALATION": 0, "OWNER_ESCALATION": 1, "STALE_CASE": 2, "BRANCH_FOLLOW_UP": 3}
    records.sort(
        key=lambda record: (
            priority.get(record["escalation_status"], 99),
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
        on_time_receipt_rate = round(float(on_time_receipt_count) / float(received_purchase_order_count), 2) if received_purchase_order_count else 0.0
        supplier_return_rate = round(float(supplier_return_count) / float(purchase_invoice_count), 2) if purchase_invoice_count else 0.0
        invoice_mismatch_rate = round(float(invoice_mismatch_count) / float(purchase_invoice_count), 2) if purchase_invoice_count else 0.0
        if invoice_mismatch_count > 0 or supplier_return_rate >= 0.5 or on_time_receipt_rate < 0.5:
            performance_status = "AT_RISK"
        elif supplier_return_rate > 0.0 or on_time_receipt_rate < 1.0:
            performance_status = "WATCH"
        else:
            performance_status = "STRONG"

        records.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", "Unknown supplier"),
                "approved_purchase_order_count": len(approved_orders),
                "received_purchase_order_count": received_purchase_order_count,
                "on_time_receipt_count": on_time_receipt_count,
                "on_time_receipt_rate": on_time_receipt_rate,
                "average_receipt_delay_days": round(sum(delay_days) / len(delay_days), 2) if delay_days else 0.0,
                "purchase_invoice_count": purchase_invoice_count,
                "invoice_mismatch_count": invoice_mismatch_count,
                "invoice_mismatch_rate": invoice_mismatch_rate,
                "supplier_return_count": supplier_return_count,
                "supplier_return_rate": supplier_return_rate,
                "performance_status": performance_status,
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
