from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def request_purchase_order_approval(
    *,
    purchase_order: dict[str, Any],
    note: str | None,
    actor_roles: list[str],
    requested_on: str | None = None,
) -> dict[str, Any]:
    current_status = purchase_order.get("approval_status", "NOT_REQUESTED")
    if current_status not in {"NOT_REQUESTED", "REJECTED"}:
        raise ValueError("Purchase order cannot be submitted for approval in its current status")
    purchase_order["approval_status"] = "PENDING_APPROVAL"
    purchase_order["approval_requested_note"] = note
    purchase_order["approval_requested_by_roles"] = list(actor_roles)
    purchase_order["approval_requested_on"] = requested_on
    purchase_order["approval_decision_note"] = None
    purchase_order["approval_decided_by_roles"] = None
    purchase_order["approval_decided_on"] = None
    purchase_order["approved_on"] = None
    return purchase_order


def decide_purchase_order_approval(
    *,
    purchase_order: dict[str, Any],
    decision: str,
    note: str | None,
    actor_roles: list[str],
    decided_on: str | None = None,
) -> dict[str, Any]:
    if purchase_order.get("approval_status") != "PENDING_APPROVAL":
        raise ValueError("Purchase order is not pending approval")
    if decision not in {"APPROVED", "REJECTED"}:
        raise ValueError("Unsupported purchase order decision")
    purchase_order["approval_status"] = decision
    purchase_order["approval_decision_note"] = note
    purchase_order["approval_decided_by_roles"] = list(actor_roles)
    purchase_order["approval_decided_on"] = decided_on
    purchase_order["approved_on"] = decided_on if decision == "APPROVED" else None
    return purchase_order


def ensure_purchase_order_receivable(*, purchase_order: dict[str, Any]) -> dict[str, Any]:
    if purchase_order.get("approval_status") != "APPROVED":
        raise ValueError("Purchase order must be approved before receiving")
    return purchase_order


def build_purchase_approval_report(
    *,
    branch_id: str,
    purchase_orders: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
    goods_receipts: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    goods_receipt_by_purchase_order_id = {
        goods_receipt["purchase_order_id"]: goods_receipt
        for goods_receipt in goods_receipts
        if goods_receipt.get("branch_id") == branch_id
    }
    branch_purchase_orders = [purchase_order for purchase_order in purchase_orders if purchase_order.get("branch_id") == branch_id]

    status_priority = {
        "PENDING_APPROVAL": 0,
        "NOT_REQUESTED": 1,
        "APPROVED": 2,
        "REJECTED": 3,
    }
    records: list[dict[str, Any]] = []
    for purchase_order in branch_purchase_orders:
        status_value = purchase_order.get("approval_status", "NOT_REQUESTED")
        goods_receipt = goods_receipt_by_purchase_order_id.get(purchase_order["id"])
        if goods_receipt:
            receiving_status = "RECEIVED"
        elif status_value == "APPROVED":
            receiving_status = "READY_FOR_RECEIPT"
        elif status_value == "PENDING_APPROVAL":
            receiving_status = "AWAITING_APPROVAL"
        elif status_value == "REJECTED":
            receiving_status = "BLOCKED"
        else:
            receiving_status = "NOT_REQUESTED"
        supplier = suppliers_by_id.get(purchase_order["supplier_id"], {})
        records.append(
            {
                "purchase_order_id": purchase_order["id"],
                "supplier_name": supplier.get("name", purchase_order["supplier_id"]),
                "approval_status": status_value,
                "line_count": len(purchase_order.get("lines", [])),
                "ordered_quantity": _money(sum(float(line.get("quantity", 0.0)) for line in purchase_order.get("lines", []))),
                "receiving_status": receiving_status,
                "approval_requested_note": purchase_order.get("approval_requested_note"),
                "approval_decision_note": purchase_order.get("approval_decision_note"),
                "goods_receipt_id": goods_receipt["id"] if goods_receipt else None,
            }
        )

    records.sort(
        key=lambda record: (
            status_priority.get(record["approval_status"], 99),
            record["supplier_name"],
            record["purchase_order_id"],
        )
    )
    return {
        "branch_id": branch_id,
        "not_requested_count": sum(1 for purchase_order in branch_purchase_orders if purchase_order.get("approval_status", "NOT_REQUESTED") == "NOT_REQUESTED"),
        "pending_approval_count": sum(1 for purchase_order in branch_purchase_orders if purchase_order.get("approval_status") == "PENDING_APPROVAL"),
        "approved_count": sum(1 for purchase_order in branch_purchase_orders if purchase_order.get("approval_status") == "APPROVED"),
        "rejected_count": sum(1 for purchase_order in branch_purchase_orders if purchase_order.get("approval_status") == "REJECTED"),
        "received_count": sum(1 for record in records if record["goods_receipt_id"] is not None),
        "records": records,
    }
