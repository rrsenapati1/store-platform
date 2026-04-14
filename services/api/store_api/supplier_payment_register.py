from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def build_supplier_payment_register(
    *,
    branch_id: str,
    supplier_payments: Iterable[dict[str, Any]],
    purchase_invoices: Iterable[dict[str, Any]],
    supplier_returns: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    purchase_invoices_by_id = {
        purchase_invoice["id"]: purchase_invoice
        for purchase_invoice in purchase_invoices
        if purchase_invoice["branch_id"] == branch_id
    }
    credit_note_totals_by_invoice_id: dict[str, float] = {}
    for supplier_return in supplier_returns:
        purchase_invoice_id = supplier_return["purchase_invoice_id"]
        if purchase_invoice_id not in purchase_invoices_by_id:
            continue
        credit_note_totals_by_invoice_id[purchase_invoice_id] = _money(
            credit_note_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + supplier_return["grand_total"]
        )

    payments_by_invoice_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for supplier_payment in supplier_payments:
        if supplier_payment["branch_id"] != branch_id:
            continue
        purchase_invoice_id = supplier_payment["purchase_invoice_id"]
        if purchase_invoice_id not in purchase_invoices_by_id:
            continue
        payments_by_invoice_id[purchase_invoice_id].append(supplier_payment)

    records: list[dict[str, Any]] = []
    method_totals = {"bank_transfer": 0.0, "cash": 0.0, "upi": 0.0, "other": 0.0}
    latest_payment_date: str | None = None

    for purchase_invoice_id, invoice_payments in payments_by_invoice_id.items():
        purchase_invoice = purchase_invoices_by_id[purchase_invoice_id]
        credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice_id, 0.0)
        running_paid_total = 0.0

        for supplier_payment in sorted(
            invoice_payments,
            key=lambda payment: (
                payment.get("payment_date") or "",
                payment.get("payment_number") or "",
                payment.get("id") or "",
            ),
        ):
            running_paid_total = _money(running_paid_total + supplier_payment["amount"])
            remaining_outstanding_total = _money(
                max(0.0, purchase_invoice["grand_total"] - credit_note_total - running_paid_total)
            )
            settlement_status_after_payment = "SETTLED" if remaining_outstanding_total == 0 else "PARTIALLY_SETTLED"
            supplier = suppliers_by_id.get(supplier_payment["supplier_id"], {})

            payment_method = supplier_payment["payment_method"]
            if payment_method in method_totals:
                method_totals[payment_method] = _money(method_totals[payment_method] + supplier_payment["amount"])
            else:
                method_totals["other"] = _money(method_totals["other"] + supplier_payment["amount"])

            payment_date = supplier_payment.get("payment_date")
            if payment_date and (latest_payment_date is None or payment_date > latest_payment_date):
                latest_payment_date = payment_date

            records.append(
                {
                    "payment_id": supplier_payment["id"],
                    "payment_number": supplier_payment["payment_number"],
                    "payment_date": payment_date,
                    "supplier_id": supplier_payment["supplier_id"],
                    "supplier_name": supplier.get("name", "Unknown supplier"),
                    "purchase_invoice_id": purchase_invoice_id,
                    "purchase_invoice_number": purchase_invoice["invoice_number"],
                    "payment_method": payment_method,
                    "reference": supplier_payment.get("reference"),
                    "amount": supplier_payment["amount"],
                    "invoice_grand_total": purchase_invoice["grand_total"],
                    "invoice_credit_note_total": credit_note_total,
                    "invoice_paid_total_after_payment": running_paid_total,
                    "remaining_outstanding_total": remaining_outstanding_total,
                    "settlement_status_after_payment": settlement_status_after_payment,
                }
            )

    records.sort(
        key=lambda record: (
            record["payment_date"] or "",
            record["payment_number"],
            record["payment_id"],
        ),
        reverse=True,
    )

    return {
        "branch_id": branch_id,
        "payment_count": len(records),
        "supplier_count": len({record["supplier_id"] for record in records}),
        "paid_total": _money(sum(record["amount"] for record in records)),
        "bank_transfer_total": method_totals["bank_transfer"],
        "cash_total": method_totals["cash"],
        "upi_total": method_totals["upi"],
        "other_total": method_totals["other"],
        "latest_payment_date": latest_payment_date,
        "records": records,
    }
