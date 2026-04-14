from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def _parse_payment_date(raw_value: Any) -> date | None:
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            return None
    return None


def build_supplier_payment_activity_report(
    *,
    branch_id: str,
    as_of_date: date,
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

    paid_totals_by_invoice_id: dict[str, float] = defaultdict(float)
    payments_by_supplier_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for supplier_payment in supplier_payments:
        if supplier_payment["branch_id"] != branch_id:
            continue
        purchase_invoice_id = supplier_payment["purchase_invoice_id"]
        if purchase_invoice_id not in purchase_invoices_by_id:
            continue
        paid_totals_by_invoice_id[purchase_invoice_id] = _money(
            paid_totals_by_invoice_id[purchase_invoice_id] + supplier_payment["amount"]
        )
        payments_by_supplier_id[supplier_payment["supplier_id"]].append(supplier_payment)

    outstanding_totals_by_supplier_id: dict[str, float] = defaultdict(float)
    for purchase_invoice in purchase_invoices_by_id.values():
        invoice_credit_note_total = credit_note_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_paid_total = paid_totals_by_invoice_id.get(purchase_invoice["id"], 0.0)
        invoice_outstanding_total = _money(max(0.0, purchase_invoice["grand_total"] - invoice_credit_note_total - invoice_paid_total))
        outstanding_totals_by_supplier_id[purchase_invoice["supplier_id"]] = _money(
            outstanding_totals_by_supplier_id[purchase_invoice["supplier_id"]] + invoice_outstanding_total
        )

    recent_cutoff = as_of_date - timedelta(days=29)
    records: list[dict[str, Any]] = []
    for supplier_id, supplier_payments_for_supplier in payments_by_supplier_id.items():
        supplier = suppliers_by_id.get(supplier_id, {})
        sorted_payments = sorted(
            supplier_payments_for_supplier,
            key=lambda payment: (
                payment.get("payment_date") or "",
                payment.get("payment_number") or "",
                payment.get("id") or "",
            ),
            reverse=True,
        )
        last_payment = sorted_payments[0]
        paid_total = _money(sum(payment["amount"] for payment in supplier_payments_for_supplier))
        recent_paid_total = 0.0
        for payment in supplier_payments_for_supplier:
            payment_date = _parse_payment_date(payment.get("payment_date"))
            if payment_date is not None and payment_date > recent_cutoff:
                recent_paid_total = _money(recent_paid_total + payment["amount"])

        records.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", "Unknown supplier"),
                "payment_count": len(supplier_payments_for_supplier),
                "paid_total": paid_total,
                "recent_30_days_paid_total": recent_paid_total,
                "average_payment_value": _money(paid_total / len(supplier_payments_for_supplier)),
                "outstanding_total": outstanding_totals_by_supplier_id.get(supplier_id, 0.0),
                "last_payment_date": last_payment.get("payment_date"),
                "last_payment_number": last_payment.get("payment_number"),
                "last_payment_method": last_payment.get("payment_method"),
                "last_payment_reference": last_payment.get("reference"),
                "last_payment_amount": _money(last_payment["amount"]),
            }
        )

    records.sort(
        key=lambda record: (
            record["last_payment_date"] or "",
            record["last_payment_number"] or "",
            record["supplier_name"],
        ),
        reverse=True,
    )

    return {
        "branch_id": branch_id,
        "as_of_date": as_of_date.isoformat(),
        "supplier_count": len(records),
        "payment_count": sum(record["payment_count"] for record in records),
        "paid_total": _money(sum(record["paid_total"] for record in records)),
        "recent_30_days_paid_total": _money(sum(record["recent_30_days_paid_total"] for record in records)),
        "records": records,
    }
