from __future__ import annotations

from collections.abc import Iterable

from .compliance import calculate_invoice_taxes


def _money(value: float) -> float:
    return round(float(value), 2)


def next_purchase_invoice_number(sequence: dict[tuple[str, str], int], *, branch_id: str, fiscal_year: str) -> str:
    key = (f"{branch_id}:purchase_invoice", fiscal_year)
    sequence[key] = sequence.get(key, 0) + 1
    return f"SPINV-{fiscal_year}-{sequence[key]:06d}"


def next_supplier_credit_note_number(sequence: dict[tuple[str, str], int], *, branch_id: str, fiscal_year: str) -> str:
    key = (f"{branch_id}:supplier_credit_note", fiscal_year)
    sequence[key] = sequence.get(key, 0) + 1
    return f"SRCN-{fiscal_year}-{sequence[key]:06d}"


def compute_purchase_totals(
    *,
    seller_gstin: str | None,
    buyer_gstin: str | None,
    lines: Iterable[dict[str, float]],
) -> dict[str, float | dict[str, float]]:
    subtotal = 0.0
    tax_totals = {"cgst": 0.0, "sgst": 0.0, "igst": 0.0, "tax_total": 0.0}

    for line in lines:
        line_subtotal = _money(line["quantity"] * line["unit_cost"])
        line_tax = calculate_invoice_taxes(
            seller_gstin=seller_gstin,
            buyer_gstin=buyer_gstin,
            taxable_total=line_subtotal,
            tax_rate_percent=line["tax_rate_percent"],
        )
        subtotal = _money(subtotal + line_subtotal)
        for key, value in line_tax.items():
            tax_totals[key] = _money(tax_totals[key] + value)

    return {
        "subtotal": subtotal,
        "tax": tax_totals,
        "grand_total": _money(subtotal + tax_totals["tax_total"]),
    }
