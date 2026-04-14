from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def next_supplier_payment_number(sequence: dict[tuple[str, str], int], *, branch_id: str, fiscal_year: str) -> str:
    key = (f"{branch_id}:supplier_payment", fiscal_year)
    sequence[key] = sequence.get(key, 0) + 1
    return f"SPAY-{fiscal_year}-{sequence[key]:06d}"


def ensure_supplier_payment_within_outstanding(
    *,
    invoice_total: float,
    credit_note_total: float,
    paid_total: float,
    payment_amount: float,
) -> None:
    outstanding_total = _money(max(0.0, invoice_total - credit_note_total - paid_total))
    if _money(payment_amount) > outstanding_total:
        raise ValueError("Supplier payment exceeds outstanding amount")


def build_supplier_payables_report(
    *,
    branch_id: str,
    purchase_invoices: Iterable[dict[str, Any]],
    supplier_returns: Iterable[dict[str, Any]],
    supplier_payments: Iterable[dict[str, Any]],
    suppliers_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    credit_note_totals_by_invoice_id: dict[str, float] = {}
    for supplier_return in supplier_returns:
        purchase_invoice_id = supplier_return["purchase_invoice_id"]
        credit_note_totals_by_invoice_id[purchase_invoice_id] = _money(
            credit_note_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + supplier_return["grand_total"]
        )

    paid_totals_by_invoice_id: dict[str, float] = {}
    for supplier_payment in supplier_payments:
        purchase_invoice_id = supplier_payment["purchase_invoice_id"]
        paid_totals_by_invoice_id[purchase_invoice_id] = _money(
            paid_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + supplier_payment["amount"]
        )

    records: list[dict[str, Any]] = []
    invoiced_total = 0.0
    credit_note_total = 0.0
    paid_total = 0.0
    outstanding_total = 0.0

    for purchase_invoice in purchase_invoices:
        if purchase_invoice["branch_id"] != branch_id:
            continue

        invoice_credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_paid_total = paid_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_outstanding_total = _money(
            max(0.0, purchase_invoice["grand_total"] - invoice_credit_note_total - invoice_paid_total)
        )
        settlement_status = "UNPAID"
        if invoice_outstanding_total == 0:
            settlement_status = "SETTLED"
        elif invoice_credit_note_total > 0 or invoice_paid_total > 0:
            settlement_status = "PARTIALLY_SETTLED"

        supplier = suppliers_by_id.get(purchase_invoice["supplier_id"])
        records.append(
            {
                "purchase_invoice_id": purchase_invoice["id"],
                "purchase_invoice_number": purchase_invoice["invoice_number"],
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "grand_total": purchase_invoice["grand_total"],
                "credit_note_total": invoice_credit_note_total,
                "paid_total": invoice_paid_total,
                "outstanding_total": invoice_outstanding_total,
                "settlement_status": settlement_status,
            }
        )
        invoiced_total = _money(invoiced_total + purchase_invoice["grand_total"])
        credit_note_total = _money(credit_note_total + invoice_credit_note_total)
        paid_total = _money(paid_total + invoice_paid_total)
        outstanding_total = _money(outstanding_total + invoice_outstanding_total)

    return {
        "branch_id": branch_id,
        "invoiced_total": invoiced_total,
        "credit_note_total": credit_note_total,
        "paid_total": paid_total,
        "outstanding_total": outstanding_total,
        "records": records,
    }
