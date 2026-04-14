from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from .vendor_disputes import _parse_iso_date, _resolve_reference


def _record_priority(status: str) -> int:
    if status == "ATTENTION":
        return 0
    if status == "OPEN":
        return 1
    return 2


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
            _record_priority(record["status"]),
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
