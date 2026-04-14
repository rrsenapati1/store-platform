from store_api.print_service import build_invoice_receipt_lines, build_print_job, complete_print_job


def test_build_invoice_receipt_lines_include_tax_and_irn_fields():
    lines = build_invoice_receipt_lines(
        invoice_number="SINV-2526-000021",
        customer_name="Acme Traders",
        customer_gstin="29ABCDE1234F1Z5",
        items=[{"name": "Notebook", "qty": 2, "unit_price": 100, "line_total": 200}],
        totals={"subtotal": 200, "cgst": 18, "sgst": 18, "igst": 0, "grand_total": 236},
        irn_status="IRN_PENDING",
    )

    assert lines[:4] == [
        "STORE TAX INVOICE",
        "Invoice: SINV-2526-000021",
        "Customer: Acme Traders",
        "GSTIN: 29ABCDE1234F1Z5",
    ]
    assert lines[-2:] == ["Grand Total: 236.00", "IRN Status: IRN_PENDING"]


def test_build_and_complete_print_job_tracks_queue_status():
    job = build_print_job(
        job_id="job-1",
        tenant_id="tenant-1",
        branch_id="branch-1",
        device_id="device-1",
        job_type="SALES_INVOICE",
        copies=1,
        payload={"invoice_id": "invoice-1", "receipt_lines": ["line-1"]},
        actor_roles=["cashier"],
    )

    assert job["status"] == "QUEUED"
    assert job["payload"]["invoice_id"] == "invoice-1"

    completed = complete_print_job(job=job, status="COMPLETED")

    assert completed["status"] == "COMPLETED"
    assert completed["failure_reason"] is None
