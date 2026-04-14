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
    variance = money(counted - expected)
    return StockCountResult(
        expected_quantity=expected,
        counted_quantity=counted,
        variance_quantity=variance,
        closing_stock=money(expected + variance),
    )


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
    quantity: float
    unit_cost: float
    line_total: float


def build_goods_receipt_lines(
    *,
    purchase_order_lines: Iterable[Any],
    products_by_id: Mapping[str, Any],
) -> list[GoodsReceiptLineDraft]:
    lines: list[GoodsReceiptLineDraft] = []
    for purchase_order_line in purchase_order_lines:
        product = products_by_id[str(purchase_order_line.product_id)]
        quantity = money(float(purchase_order_line.quantity))
        unit_cost = money(float(purchase_order_line.unit_cost))
        lines.append(
            GoodsReceiptLineDraft(
                product_id=str(purchase_order_line.product_id),
                product_name=product.name,
                sku_code=product.sku_code,
                quantity=quantity,
                unit_cost=unit_cost,
                line_total=money(quantity * unit_cost),
            )
        )
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
    status_priority = {"READY": 0, "BLOCKED": 1, "RECEIVED": 2}
    records: list[dict[str, Any]] = []
    for purchase_order in purchase_orders:
        goods_receipt = goods_receipts_by_purchase_order_id.get(str(purchase_order["purchase_order_id"]))
        approval_status = str(purchase_order["approval_status"])
        if goods_receipt is not None:
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
        "received_count": sum(1 for record in records if record["receiving_status"] == "RECEIVED"),
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
