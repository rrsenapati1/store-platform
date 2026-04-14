from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def ensure_goods_receipt_not_already_created(
    *,
    purchase_order_id: str,
    goods_receipts: Iterable[dict[str, Any]],
) -> None:
    if any(goods_receipt.get("purchase_order_id") == purchase_order_id for goods_receipt in goods_receipts):
        raise ValueError("Goods receipt already exists for purchase order")


def build_receiving_board(
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
        "READY": 0,
        "BLOCKED": 1,
        "RECEIVED": 2,
    }
    records: list[dict[str, Any]] = []
    for purchase_order in branch_purchase_orders:
        approval_status = purchase_order.get("approval_status", "NOT_REQUESTED")
        goods_receipt = goods_receipt_by_purchase_order_id.get(purchase_order["id"])
        if goods_receipt:
            receiving_status = "RECEIVED"
            can_receive = False
            blocked_reason = None
        elif approval_status == "APPROVED":
            receiving_status = "READY"
            can_receive = True
            blocked_reason = None
        elif approval_status == "PENDING_APPROVAL":
            receiving_status = "BLOCKED"
            can_receive = False
            blocked_reason = "Awaiting approval"
        elif approval_status == "REJECTED":
            receiving_status = "BLOCKED"
            can_receive = False
            blocked_reason = "Purchase order rejected"
        else:
            receiving_status = "BLOCKED"
            can_receive = False
            blocked_reason = "Approval not requested"

        supplier = suppliers_by_id.get(purchase_order["supplier_id"], {})
        records.append(
            {
                "purchase_order_id": purchase_order["id"],
                "supplier_name": supplier.get("name", purchase_order["supplier_id"]),
                "approval_status": approval_status,
                "receiving_status": receiving_status,
                "can_receive": can_receive,
                "blocked_reason": blocked_reason,
                "goods_receipt_id": goods_receipt["id"] if goods_receipt else None,
            }
        )

    records.sort(
        key=lambda record: (
            status_priority.get(record["receiving_status"], 99),
            record["supplier_name"],
            record["purchase_order_id"],
        )
    )

    return {
        "branch_id": branch_id,
        "blocked_count": sum(1 for record in records if record["receiving_status"] == "BLOCKED"),
        "ready_count": sum(1 for record in records if record["receiving_status"] == "READY"),
        "received_count": sum(1 for record in records if record["receiving_status"] == "RECEIVED"),
        "records": records,
    }
