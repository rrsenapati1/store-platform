from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def ensure_purchase_invoice_not_already_created(
    *,
    goods_receipt_id: str,
    purchase_invoices: Iterable[dict[str, Any]],
) -> None:
    if any(invoice["goods_receipt_id"] == goods_receipt_id for invoice in purchase_invoices):
        raise ValueError("Purchase invoice already exists for goods receipt")


def build_vendor_billing_board(
    *,
    branch_id: str,
    goods_receipts: Iterable[dict[str, Any]],
    purchase_invoices: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    purchase_invoices_by_receipt_id = {
        purchase_invoice["goods_receipt_id"]: purchase_invoice for purchase_invoice in purchase_invoices
    }

    records: list[dict[str, Any]] = []
    awaiting_invoice_count = 0
    invoiced_count = 0

    for goods_receipt in goods_receipts:
        if goods_receipt["branch_id"] != branch_id:
            continue

        purchase_invoice = purchase_invoices_by_receipt_id.get(goods_receipt["id"])
        supplier = suppliers_by_id.get(goods_receipt["supplier_id"])
        if purchase_invoice is None:
            awaiting_invoice_count += 1
            records.append(
                {
                    "goods_receipt_id": goods_receipt["id"],
                    "purchase_order_id": goods_receipt["purchase_order_id"],
                    "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                    "billing_status": "AWAITING_INVOICE",
                    "purchase_invoice_id": None,
                    "purchase_invoice_number": None,
                    "grand_total": None,
                }
            )
            continue

        invoiced_count += 1
        records.append(
            {
                "goods_receipt_id": goods_receipt["id"],
                "purchase_order_id": goods_receipt["purchase_order_id"],
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "billing_status": "INVOICED",
                "purchase_invoice_id": purchase_invoice["id"],
                "purchase_invoice_number": purchase_invoice["invoice_number"],
                "grand_total": purchase_invoice["grand_total"],
            }
        )

    return {
        "branch_id": branch_id,
        "awaiting_invoice_count": awaiting_invoice_count,
        "invoiced_count": invoiced_count,
        "records": records,
    }
