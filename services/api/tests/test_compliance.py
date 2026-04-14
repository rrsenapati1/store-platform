from store_api.compliance import (
    attach_irn_to_invoice,
    calculate_invoice_taxes,
    next_invoice_number,
    prepare_gst_export_job,
)


def test_same_state_gstin_splits_tax_between_cgst_and_sgst():
    tax = calculate_invoice_taxes(
        seller_gstin="29ABCDE1234F1Z5",
        buyer_gstin="29AAAAA9999A1Z5",
        taxable_total=1000,
        tax_rate_percent=18,
    )

    assert tax["cgst"] == 90.0
    assert tax["sgst"] == 90.0
    assert tax["igst"] == 0.0


def test_invoice_numbers_increment_with_branch_scope():
    sequence = {}

    assert next_invoice_number(sequence, branch_id="b1", fiscal_year="2526") == "SINV-2526-000001"
    assert next_invoice_number(sequence, branch_id="b1", fiscal_year="2526") == "SINV-2526-000002"


def test_gst_export_marks_invoice_irn_pending_and_attach_updates_it():
    export_job = prepare_gst_export_job(
        invoice_id="inv-1",
        invoice_number="SINV-2526-000001",
        seller_gstin="29ABCDE1234F1Z5",
        buyer_gstin="29AAAAA9999A1Z5",
        hsn_sac_code="4820",
        grand_total=1180.0,
    )

    assert export_job.status == "IRN_PENDING"
    attachment = attach_irn_to_invoice(
        invoice_id="inv-1",
        irn="7d07f5f1",
        signed_qr_payload="qr-payload",
        ack_no="12345",
    )

    assert attachment.invoice_id == "inv-1"
    assert attachment.irn == "7d07f5f1"
