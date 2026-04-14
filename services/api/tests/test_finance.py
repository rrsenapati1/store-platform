from store_api.finance import compute_cash_session_close, compute_exchange_balance, next_credit_note_number


def test_credit_note_sequence_uses_a_dedicated_counter():
    sequence: dict[tuple[str, str], int] = {}

    assert next_credit_note_number(sequence, branch_id="branch-1", fiscal_year="2526") == "SCN-2526-000001"
    assert next_credit_note_number(sequence, branch_id="branch-1", fiscal_year="2526") == "SCN-2526-000002"
    assert next_credit_note_number(sequence, branch_id="branch-2", fiscal_year="2526") == "SCN-2526-000001"


def test_cash_session_close_uses_expected_cash_position():
    assert compute_cash_session_close(opening_float=500, cash_sales_total=236, closing_amount=736) == {
        "expected_close_amount": 736.0,
        "variance_amount": 0.0,
    }


def test_exchange_balance_direction_covers_even_collect_and_refund_cases():
    assert compute_exchange_balance(return_total=118, replacement_total=118) == {
        "balance_direction": "EVEN",
        "balance_amount": 0.0,
    }
    assert compute_exchange_balance(return_total=118, replacement_total=177) == {
        "balance_direction": "COLLECT_FROM_CUSTOMER",
        "balance_amount": 59.0,
    }
    assert compute_exchange_balance(return_total=118, replacement_total=59) == {
        "balance_direction": "REFUND_TO_CUSTOMER",
        "balance_amount": 59.0,
    }
