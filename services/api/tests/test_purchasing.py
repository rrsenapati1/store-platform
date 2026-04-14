from store_api.purchasing import (
    compute_purchase_totals,
    next_purchase_invoice_number,
    next_supplier_credit_note_number,
)


def test_purchase_and_supplier_credit_sequences_are_independent():
    sequence: dict[tuple[str, str], int] = {}

    assert next_purchase_invoice_number(sequence, branch_id="branch-1", fiscal_year="2526") == "SPINV-2526-000001"
    assert next_purchase_invoice_number(sequence, branch_id="branch-1", fiscal_year="2526") == "SPINV-2526-000002"
    assert next_supplier_credit_note_number(sequence, branch_id="branch-1", fiscal_year="2526") == "SRCN-2526-000001"


def test_purchase_totals_split_tax_for_same_state_supplier_invoice():
    totals = compute_purchase_totals(
        seller_gstin="29AAAAA1111A1Z5",
        buyer_gstin="29ABCDE1234F1Z5",
        lines=[{"quantity": 2, "unit_cost": 50, "tax_rate_percent": 18}],
    )

    assert totals == {
        "subtotal": 100.0,
        "tax": {"cgst": 9.0, "sgst": 9.0, "igst": 0.0, "tax_total": 18.0},
        "grand_total": 118.0,
    }
