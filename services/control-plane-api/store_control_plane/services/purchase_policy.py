from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any


def money(value: float) -> float:
    return round(float(value), 2)


def normalize_gstin(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


def purchase_order_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"PO-{branch_segment}-{sequence_number:04d}"


@dataclass(slots=True)
class PurchaseOrderLineDraft:
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    unit_cost: float
    gst_rate: float
    line_total: float
    tax_total: float


@dataclass(slots=True)
class PurchaseOrderTotals:
    lines: list[PurchaseOrderLineDraft]
    subtotal: float
    tax_total: float
    grand_total: float
    ordered_quantity: float


def build_purchase_order_totals(
    *,
    line_inputs: Iterable[Mapping[str, Any]],
    products_by_id: Mapping[str, Any],
) -> PurchaseOrderTotals:
    drafts: list[PurchaseOrderLineDraft] = []
    subtotal = 0.0
    tax_total = 0.0
    ordered_quantity = 0.0

    for line_input in line_inputs:
        product_id = str(line_input["product_id"])
        product = products_by_id[product_id]
        quantity = money(float(line_input["quantity"]))
        unit_cost = money(float(line_input["unit_cost"]))
        line_total = money(quantity * unit_cost)
        line_tax_total = money(line_total * float(product.gst_rate) / 100)
        subtotal += line_total
        tax_total += line_tax_total
        ordered_quantity += quantity
        drafts.append(
            PurchaseOrderLineDraft(
                product_id=product_id,
                product_name=product.name,
                sku_code=product.sku_code,
                quantity=quantity,
                unit_cost=unit_cost,
                gst_rate=money(float(product.gst_rate)),
                line_total=line_total,
                tax_total=line_tax_total,
            )
        )

    return PurchaseOrderTotals(
        lines=drafts,
        subtotal=money(subtotal),
        tax_total=money(tax_total),
        grand_total=money(subtotal + tax_total),
        ordered_quantity=money(ordered_quantity),
    )


def submit_purchase_order_approval(*, purchase_order: Any, note: str | None, requested_at: datetime) -> Any:
    if purchase_order.approval_status not in {"NOT_REQUESTED", "REJECTED"}:
        raise ValueError("Purchase order cannot be submitted for approval in its current status")
    purchase_order.approval_status = "PENDING_APPROVAL"
    purchase_order.approval_requested_note = note
    purchase_order.approval_requested_at = requested_at
    purchase_order.approval_decision_note = None
    purchase_order.approval_decided_at = None
    purchase_order.approved_at = None
    return purchase_order


def decide_purchase_order(*, purchase_order: Any, decision: str, note: str | None, decided_at: datetime) -> Any:
    if purchase_order.approval_status != "PENDING_APPROVAL":
        raise ValueError("Purchase order is not pending approval")
    if decision not in {"APPROVED", "REJECTED"}:
        raise ValueError("Unsupported purchase order decision")
    purchase_order.approval_status = decision
    purchase_order.approval_decision_note = note
    purchase_order.approval_decided_at = decided_at
    purchase_order.approved_at = decided_at if decision == "APPROVED" else None
    return purchase_order


def build_purchase_approval_report(
    *,
    branch_id: str,
    purchase_orders: Iterable[Mapping[str, Any]],
    suppliers_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    status_priority = {
        "PENDING_APPROVAL": 0,
        "NOT_REQUESTED": 1,
        "APPROVED": 2,
        "REJECTED": 3,
    }
    records = [
        {
            "purchase_order_id": purchase_order["purchase_order_id"],
            "purchase_order_number": purchase_order["purchase_order_number"],
            "supplier_name": suppliers_by_id.get(purchase_order["supplier_id"], {}).get("name", purchase_order["supplier_id"]),
            "approval_status": purchase_order["approval_status"],
            "line_count": purchase_order["line_count"],
            "ordered_quantity": purchase_order["ordered_quantity"],
            "grand_total": purchase_order["grand_total"],
            "approval_requested_note": purchase_order.get("approval_requested_note"),
            "approval_decision_note": purchase_order.get("approval_decision_note"),
        }
        for purchase_order in purchase_orders
    ]
    records.sort(
        key=lambda record: (
            status_priority.get(record["approval_status"], 99),
            record["supplier_name"],
            record["purchase_order_number"],
        )
    )
    return {
        "branch_id": branch_id,
        "not_requested_count": sum(1 for record in records if record["approval_status"] == "NOT_REQUESTED"),
        "pending_approval_count": sum(1 for record in records if record["approval_status"] == "PENDING_APPROVAL"),
        "approved_count": sum(1 for record in records if record["approval_status"] == "APPROVED"),
        "rejected_count": sum(1 for record in records if record["approval_status"] == "REJECTED"),
        "records": records,
    }
