from __future__ import annotations


def _money(value: float) -> float:
    return round(float(value), 2)


def next_credit_note_number(sequence: dict[tuple[str, str], int], *, branch_id: str, fiscal_year: str) -> str:
    key = (f"{branch_id}:credit_note", fiscal_year)
    sequence[key] = sequence.get(key, 0) + 1
    return f"SCN-{fiscal_year}-{sequence[key]:06d}"


def compute_cash_session_close(*, opening_float: float, cash_sales_total: float, closing_amount: float) -> dict[str, float]:
    expected_close_amount = _money(opening_float + cash_sales_total)
    return {
        "expected_close_amount": expected_close_amount,
        "variance_amount": _money(closing_amount - expected_close_amount),
    }


def compute_exchange_balance(*, return_total: float, replacement_total: float) -> dict[str, float | str]:
    difference = _money(replacement_total - return_total)
    if difference > 0:
        return {"balance_direction": "COLLECT_FROM_CUSTOMER", "balance_amount": difference}
    if difference < 0:
        return {"balance_direction": "REFUND_TO_CUSTOMER", "balance_amount": _money(abs(difference))}
    return {"balance_direction": "EVEN", "balance_amount": 0.0}


def compute_tax_inclusive_total(*, subtotal: float, tax_rate_percent: float) -> float:
    tax_total = _money(subtotal * tax_rate_percent / 100)
    return _money(subtotal + tax_total)
