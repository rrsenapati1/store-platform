from store_api.supplier_payables import (
    build_supplier_payables_report,
    ensure_supplier_payment_within_outstanding,
)


def test_build_supplier_payables_report_tracks_credit_paid_and_outstanding_totals():
    report = build_supplier_payables_report(
        branch_id="branch-1",
        purchase_invoices=[
            {
                "id": "pinv-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "invoice_number": "SPINV-2526-000001",
                "grand_total": 354.0,
            }
        ],
        supplier_returns=[
            {
                "id": "sret-1",
                "purchase_invoice_id": "pinv-1",
                "grand_total": 59.0,
            }
        ],
        supplier_payments=[
            {
                "id": "spay-1",
                "purchase_invoice_id": "pinv-1",
                "amount": 200.0,
            }
        ],
        suppliers_by_id={"supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"}},
    )

    assert report == {
        "branch_id": "branch-1",
        "invoiced_total": 354.0,
        "credit_note_total": 59.0,
        "paid_total": 200.0,
        "outstanding_total": 95.0,
        "records": [
            {
                "purchase_invoice_id": "pinv-1",
                "purchase_invoice_number": "SPINV-2526-000001",
                "supplier_name": "Paper Supply Co",
                "grand_total": 354.0,
                "credit_note_total": 59.0,
                "paid_total": 200.0,
                "outstanding_total": 95.0,
                "settlement_status": "PARTIALLY_SETTLED",
            }
        ],
    }


def test_ensure_supplier_payment_within_outstanding_raises_for_overpayment():
    try:
        ensure_supplier_payment_within_outstanding(
            invoice_total=354.0,
            credit_note_total=59.0,
            paid_total=200.0,
            payment_amount=100.0,
        )
    except ValueError as exc:
        assert str(exc) == "Supplier payment exceeds outstanding amount"
    else:
        raise AssertionError("Expected supplier payment guard to raise")
