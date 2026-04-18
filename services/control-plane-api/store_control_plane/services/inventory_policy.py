from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from .purchase_policy import money


SUPPORTED_LEDGER_ENTRY_TYPES = {
    "OPENING",
    "PURCHASE_RECEIPT",
    "SALE",
    "SALE_RETURN",
    "TRANSFER_OUT",
    "TRANSFER_IN",
    "ADJUSTMENT",
    "DAMAGE",
    "EXPIRY_WRITE_OFF",
    "CUSTOMER_RETURN",
    "SUPPLIER_RETURN",
    "COUNT_VARIANCE",
}


def goods_receipt_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"GRN-{branch_segment}-{sequence_number:04d}"


def ensure_purchase_order_receivable(*, purchase_order: Any, existing_goods_receipt: Mapping[str, Any] | None) -> None:
    if purchase_order.approval_status != "APPROVED":
        raise ValueError("Purchase order must be approved before receiving")
    if existing_goods_receipt is not None:
        raise ValueError("Goods receipt already exists for purchase order")


def ensure_stock_adjustment_allowed(*, quantity_delta: float) -> None:
    if money(quantity_delta) == 0:
        raise ValueError("Stock adjustment quantity must not be zero")


@dataclass(slots=True)
class StockCountResult:
    expected_quantity: float
    counted_quantity: float
    variance_quantity: float
    closing_stock: float


def build_stock_count_result(*, expected_quantity: float, counted_quantity: float) -> StockCountResult:
    expected = money(expected_quantity)
    counted = money(counted_quantity)
    if counted < 0:
        raise ValueError("Counted quantity must not be negative")
    variance = money(counted - expected)
    return StockCountResult(
        expected_quantity=expected,
        counted_quantity=counted,
        variance_quantity=variance,
        closing_stock=money(expected + variance),
    )


def stock_count_session_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"SCN-{branch_segment}-{sequence_number:04d}"


def ensure_stock_count_review_recordable(*, status: str) -> None:
    if status != "OPEN":
        raise ValueError("Blind count already recorded for session")


def ensure_stock_count_review_approvable(*, status: str) -> None:
    if status != "COUNTED":
        raise ValueError("Stock count session must be counted before approval")


def ensure_stock_count_review_cancelable(*, status: str) -> None:
    if status == "APPROVED":
        raise ValueError("Approved stock count sessions cannot be canceled")
    if status == "CANCELED":
        raise ValueError("Stock count session already canceled")


def build_stock_count_board(
    *,
    branch_id: str,
    review_sessions: Iterable[Mapping[str, Any]],
    products_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    status_priority = {"OPEN": 0, "COUNTED": 1, "APPROVED": 2, "CANCELED": 3}
    records: list[dict[str, Any]] = []
    for session in review_sessions:
        product_id = str(session["product_id"])
        product = products_by_id.get(product_id, {})
        status = str(session["status"])
        records.append(
            {
                "stock_count_session_id": str(session["stock_count_session_id"]),
                "session_number": str(session["session_number"]) if session.get("session_number") is not None else str(session["stock_count_session_id"]),
                "product_id": product_id,
                "product_name": str(product.get("product_name", product_id)),
                "sku_code": str(product.get("sku_code", product_id)),
                "status": status,
                "expected_quantity": None if status == "OPEN" else money(float(session["expected_quantity"])),
                "counted_quantity": None if session.get("counted_quantity") is None else money(float(session["counted_quantity"])),
                "variance_quantity": None if session.get("variance_quantity") is None else money(float(session["variance_quantity"])),
                "note": session.get("note"),
                "review_note": session.get("review_note"),
            }
        )

    records.sort(
        key=lambda record: (
            status_priority.get(record["status"], 99),
            record["product_name"],
            record["session_number"],
        )
    )
    return {
        "branch_id": branch_id,
        "open_count": sum(1 for record in records if record["status"] == "OPEN"),
        "counted_count": sum(1 for record in records if record["status"] == "COUNTED"),
        "approved_count": sum(1 for record in records if record["status"] == "APPROVED"),
        "canceled_count": sum(1 for record in records if record["status"] == "CANCELED"),
        "records": records,
    }


SUPPORTED_RESTOCK_SOURCE_POSTURES = {
    "BACKROOM_AVAILABLE",
    "BACKROOM_UNCERTAIN",
    "BACKROOM_UNAVAILABLE",
}


def restock_task_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"RST-{branch_segment}-{sequence_number:04d}"


def ensure_restock_task_creatable(*, requested_quantity: float, existing_active_task: Mapping[str, Any] | None) -> None:
    if money(requested_quantity) <= 0:
        raise ValueError("Restock task quantity must be greater than zero")
    if existing_active_task is not None:
        raise ValueError("Active restock task already exists for product")


def ensure_restock_task_pickable(*, status: str, requested_quantity: float, picked_quantity: float) -> None:
    if status != "OPEN":
        raise ValueError("Restock task must be open before picking")
    if money(picked_quantity) < 0:
        raise ValueError("Picked quantity must not be negative")
    if money(picked_quantity) > money(requested_quantity):
        raise ValueError("Picked quantity cannot exceed requested quantity")


def ensure_restock_task_completable(*, status: str) -> None:
    if status != "PICKED":
        raise ValueError("Restock task must be picked before completion")


def ensure_restock_task_cancelable(*, status: str) -> None:
    if status == "COMPLETED":
        raise ValueError("Completed restock tasks cannot be canceled")
    if status == "CANCELED":
        raise ValueError("Restock task already canceled")


def build_restock_board(
    *,
    branch_id: str,
    task_sessions: Iterable[Mapping[str, Any]],
    products_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    status_priority = {"OPEN": 0, "PICKED": 1, "COMPLETED": 2, "CANCELED": 3}
    records: list[dict[str, Any]] = []
    for session in task_sessions:
        product_id = str(session["product_id"])
        product = products_by_id.get(product_id, {})
        status = str(session["status"])
        records.append(
            {
                "restock_task_id": str(session["restock_task_id"]),
                "task_number": str(session["task_number"]) if session.get("task_number") is not None else str(session["restock_task_id"]),
                "product_id": product_id,
                "product_name": str(product.get("product_name", product_id)),
                "sku_code": str(product.get("sku_code", product_id)),
                "status": status,
                "stock_on_hand_snapshot": money(float(session["stock_on_hand_snapshot"])),
                "reorder_point_snapshot": money(float(session["reorder_point_snapshot"])),
                "target_stock_snapshot": money(float(session["target_stock_snapshot"])),
                "suggested_quantity_snapshot": money(float(session["suggested_quantity_snapshot"])),
                "requested_quantity": money(float(session["requested_quantity"])),
                "picked_quantity": None if session.get("picked_quantity") is None else money(float(session["picked_quantity"])),
                "source_posture": str(session["source_posture"]),
                "note": session.get("note"),
                "completion_note": session.get("completion_note"),
                "has_active_task": status in {"OPEN", "PICKED"},
            }
        )

    records.sort(
        key=lambda record: (
            status_priority.get(record["status"], 99),
            record["product_name"],
            record["task_number"],
        )
    )
    return {
        "branch_id": branch_id,
        "open_count": sum(1 for record in records if record["status"] == "OPEN"),
        "picked_count": sum(1 for record in records if record["status"] == "PICKED"),
        "completed_count": sum(1 for record in records if record["status"] == "COMPLETED"),
        "canceled_count": sum(1 for record in records if record["status"] == "CANCELED"),
        "records": records,
    }


def transfer_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"TRF-{branch_segment}-{sequence_number:04d}"


def ensure_transfer_allowed(
    *,
    source_branch_id: str,
    destination_branch_id: str,
    quantity: float,
    available_quantity: float,
) -> None:
    if source_branch_id == destination_branch_id:
        raise ValueError("Transfer destination must be a different branch")
    if money(quantity) <= 0:
        raise ValueError("Transfer quantity must be greater than zero")
    if money(quantity) > money(available_quantity):
        raise ValueError("Insufficient stock for transfer")


@dataclass(slots=True)
class GoodsReceiptLineDraft:
    product_id: str
    product_name: str
    sku_code: str
    ordered_quantity: float
    quantity: float
    variance_quantity: float
    unit_cost: float
    line_total: float
    discrepancy_note: str | None
    serial_numbers: list[str]


def build_goods_receipt_lines(
    *,
    purchase_order_lines: Iterable[Any],
    reviewed_lines: Iterable[Mapping[str, Any]] | None = None,
    products_by_id: Mapping[str, Any],
) -> list[GoodsReceiptLineDraft]:
    purchase_order_line_list = list(purchase_order_lines)
    reviewed_by_product_id: dict[str, Mapping[str, Any]] | None = None
    if reviewed_lines is not None:
        reviewed_by_product_id = {}
        for reviewed_line in reviewed_lines:
            product_id = str(reviewed_line["product_id"])
            if product_id in reviewed_by_product_id:
                raise ValueError("Reviewed receipt lines must match purchase order lines")
            reviewed_by_product_id[product_id] = reviewed_line

    lines: list[GoodsReceiptLineDraft] = []
    total_received_quantity = 0.0
    expected_product_ids = {str(purchase_order_line.product_id) for purchase_order_line in purchase_order_line_list}
    if reviewed_by_product_id is not None and set(reviewed_by_product_id) != expected_product_ids:
        raise ValueError("Reviewed receipt lines must match purchase order lines")

    for purchase_order_line in purchase_order_line_list:
        product = products_by_id[str(purchase_order_line.product_id)]
        ordered_quantity = money(float(purchase_order_line.quantity))
        quantity = ordered_quantity
        discrepancy_note = None
        serial_numbers: list[str] = []
        if reviewed_by_product_id is not None:
            reviewed_line = reviewed_by_product_id[str(purchase_order_line.product_id)]
            quantity = money(float(reviewed_line["received_quantity"]))
            if quantity < 0:
                raise ValueError("Received quantity must not be negative")
            if quantity > ordered_quantity:
                raise ValueError("Received quantity exceeds ordered quantity")
            discrepancy_note = str(reviewed_line["discrepancy_note"]).strip() or None if reviewed_line.get("discrepancy_note") is not None else None
            serial_numbers = list(reviewed_line.get("serial_numbers") or [])
        unit_cost = money(float(purchase_order_line.unit_cost))
        variance_quantity = money(ordered_quantity - quantity)
        total_received_quantity = money(total_received_quantity + quantity)
        lines.append(
            GoodsReceiptLineDraft(
                product_id=str(purchase_order_line.product_id),
                product_name=product.name,
                sku_code=product.sku_code,
                ordered_quantity=ordered_quantity,
                quantity=quantity,
                variance_quantity=variance_quantity,
                unit_cost=unit_cost,
                line_total=money(quantity * unit_cost),
                discrepancy_note=discrepancy_note,
                serial_numbers=serial_numbers,
            )
        )
    if total_received_quantity <= 0:
        raise ValueError("Goods receipt must include at least one received quantity")
    return lines


def build_receiving_board(
    *,
    branch_id: str,
    purchase_orders: Iterable[Mapping[str, Any]],
    suppliers_by_id: Mapping[str, Mapping[str, Any]],
    goods_receipts: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    goods_receipts_by_purchase_order_id = {
        str(goods_receipt["purchase_order_id"]): goods_receipt
        for goods_receipt in goods_receipts
        if goods_receipt.get("branch_id") == branch_id or goods_receipt.get("branch_id") is None
    }
    status_priority = {"READY": 0, "BLOCKED": 1, "RECEIVED_WITH_VARIANCE": 2, "RECEIVED": 3}
    records: list[dict[str, Any]] = []
    for purchase_order in purchase_orders:
        goods_receipt = goods_receipts_by_purchase_order_id.get(str(purchase_order["purchase_order_id"]))
        approval_status = str(purchase_order["approval_status"])
        if goods_receipt is not None:
            has_discrepancy = bool(goods_receipt.get("has_discrepancy"))
            receiving_status = "RECEIVED_WITH_VARIANCE" if has_discrepancy else "RECEIVED"
            can_receive = False
            blocked_reason = None
            variance_quantity = money(float(goods_receipt.get("variance_quantity") or 0.0))
        elif approval_status == "APPROVED":
            receiving_status = "READY"
            can_receive = True
            blocked_reason = None
            has_discrepancy = False
            variance_quantity = 0.0
        elif approval_status == "PENDING_APPROVAL":
            receiving_status = "BLOCKED"
            can_receive = False
            blocked_reason = "Awaiting approval"
            has_discrepancy = False
            variance_quantity = 0.0
        elif approval_status == "REJECTED":
            receiving_status = "BLOCKED"
            can_receive = False
            blocked_reason = "Purchase order rejected"
            has_discrepancy = False
            variance_quantity = 0.0
        else:
            receiving_status = "BLOCKED"
            can_receive = False
            blocked_reason = "Approval not requested"
            has_discrepancy = False
            variance_quantity = 0.0

        supplier_name = str(
            purchase_order.get("supplier_name")
            or suppliers_by_id.get(str(purchase_order["supplier_id"]), {}).get("name")
            or purchase_order["supplier_id"]
        )
        records.append(
            {
                "purchase_order_id": str(purchase_order["purchase_order_id"]),
                "purchase_order_number": str(purchase_order["purchase_order_number"]),
                "supplier_name": supplier_name,
                "approval_status": approval_status,
                "receiving_status": receiving_status,
                "can_receive": can_receive,
                "has_discrepancy": has_discrepancy,
                "variance_quantity": variance_quantity,
                "blocked_reason": blocked_reason,
                "goods_receipt_id": goods_receipt["goods_receipt_id"] if goods_receipt is not None else None,
            }
        )

    records.sort(
        key=lambda record: (
            status_priority.get(record["receiving_status"], 99),
            record["supplier_name"],
            record["purchase_order_number"],
        )
    )
    return {
        "branch_id": branch_id,
        "blocked_count": sum(1 for record in records if record["receiving_status"] == "BLOCKED"),
        "ready_count": sum(1 for record in records if record["receiving_status"] == "READY"),
        "received_count": sum(1 for record in records if record["receiving_status"] in {"RECEIVED", "RECEIVED_WITH_VARIANCE"}),
        "received_with_variance_count": sum(1 for record in records if record["receiving_status"] == "RECEIVED_WITH_VARIANCE"),
        "records": records,
    }


def build_inventory_snapshot(
    *,
    branch_id: str,
    inventory_ledger: Iterable[Mapping[str, Any]],
    products_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    stock_by_product_id: dict[str, float] = {}
    last_entry_type_by_product_id: dict[str, str] = {}
    for entry in inventory_ledger:
        if str(entry["branch_id"]) != branch_id:
            continue
        product_id = str(entry["product_id"])
        stock_by_product_id[product_id] = money(stock_by_product_id.get(product_id, 0.0) + float(entry["quantity"]))
        last_entry_type_by_product_id[product_id] = str(entry["entry_type"])

    records = [
        {
            "product_id": product_id,
            "product_name": str(products_by_id.get(product_id, {}).get("product_name", product_id)),
            "sku_code": str(products_by_id.get(product_id, {}).get("sku_code", product_id)),
            "stock_on_hand": stock_on_hand,
            "last_entry_type": last_entry_type_by_product_id[product_id],
        }
        for product_id, stock_on_hand in stock_by_product_id.items()
        if stock_on_hand != 0
    ]
    records.sort(key=lambda record: (record["product_name"], record["sku_code"]))
    return {"branch_id": branch_id, "records": records}


def build_replenishment_board(
    *,
    branch_id: str,
    branch_catalog_items: Iterable[Mapping[str, Any]],
    stock_by_product_id: Mapping[str, float],
) -> dict[str, Any]:
    status_priority = {"LOW_STOCK": 0, "ADEQUATE": 1}
    records: list[dict[str, Any]] = []
    for item in branch_catalog_items:
        if str(item.get("availability_status", "ACTIVE")) != "ACTIVE":
            continue
        reorder_point = item.get("reorder_point")
        target_stock = item.get("target_stock")
        if reorder_point is None or target_stock is None:
            continue
        product_id = str(item["product_id"])
        stock_on_hand = money(float(stock_by_product_id.get(product_id, 0.0)))
        reorder_point_value = money(float(reorder_point))
        target_stock_value = money(float(target_stock))
        replenishment_status = "LOW_STOCK" if stock_on_hand < reorder_point_value else "ADEQUATE"
        suggested_reorder_quantity = money(max(target_stock_value - stock_on_hand, 0.0)) if replenishment_status == "LOW_STOCK" else 0.0
        records.append(
            {
                "product_id": product_id,
                "product_name": str(item["product_name"]),
                "sku_code": str(item["sku_code"]),
                "availability_status": "ACTIVE",
                "stock_on_hand": stock_on_hand,
                "reorder_point": reorder_point_value,
                "target_stock": target_stock_value,
                "suggested_reorder_quantity": suggested_reorder_quantity,
                "replenishment_status": replenishment_status,
            }
        )

    records.sort(key=lambda record: (status_priority.get(record["replenishment_status"], 99), record["product_name"], record["sku_code"]))
    return {
        "branch_id": branch_id,
        "low_stock_count": sum(1 for record in records if record["replenishment_status"] == "LOW_STOCK"),
        "adequate_count": sum(1 for record in records if record["replenishment_status"] == "ADEQUATE"),
        "records": records,
    }


def build_transfer_board(
    *,
    branch_id: str,
    transfers: Iterable[Mapping[str, Any]],
    branches_by_id: Mapping[str, Mapping[str, Any]],
    products_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for transfer in transfers:
        source_branch_id = str(transfer["source_branch_id"])
        destination_branch_id = str(transfer["destination_branch_id"])
        direction = "OUTBOUND" if source_branch_id == branch_id else "INBOUND"
        counterparty_branch_id = destination_branch_id if direction == "OUTBOUND" else source_branch_id
        product = products_by_id.get(str(transfer["product_id"]), {})
        records.append(
            {
                "transfer_order_id": str(transfer["transfer_order_id"]),
                "transfer_number": str(transfer["transfer_number"]),
                "direction": direction,
                "counterparty_branch_id": counterparty_branch_id,
                "counterparty_branch_name": str(branches_by_id.get(counterparty_branch_id, {}).get("name", counterparty_branch_id)),
                "product_id": str(transfer["product_id"]),
                "product_name": str(product.get("product_name", transfer["product_id"])),
                "sku_code": str(product.get("sku_code", transfer["product_id"])),
                "quantity": money(float(transfer["quantity"])),
                "status": str(transfer["status"]),
            }
        )

    direction_priority = {"OUTBOUND": 0, "INBOUND": 1}
    records.sort(key=lambda record: (direction_priority.get(record["direction"], 99), record["counterparty_branch_name"], record["transfer_number"]))
    return {
        "branch_id": branch_id,
        "outbound_count": sum(1 for record in records if record["direction"] == "OUTBOUND"),
        "inbound_count": sum(1 for record in records if record["direction"] == "INBOUND"),
        "records": records,
    }
