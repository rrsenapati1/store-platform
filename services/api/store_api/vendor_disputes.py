from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any


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
    return "goods_receipt", goods_receipt_id


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
