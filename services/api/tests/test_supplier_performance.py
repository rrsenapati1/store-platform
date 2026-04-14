from store_api.supplier_performance import build_supplier_performance_report


def test_build_supplier_performance_report_flags_at_risk_suppliers():
    report = build_supplier_performance_report(
        branch_id="branch-1",
        purchase_orders=[
            {
                "id": "po-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "approval_status": "APPROVED",
                "approved_on": "2026-04-01",
            },
            {
                "id": "po-2",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "approval_status": "APPROVED",
                "approved_on": "2026-04-01",
            },
        ],
        goods_receipts=[
            {"id": "grn-1", "branch_id": "branch-1", "purchase_order_id": "po-1", "supplier_id": "supplier-1", "received_on": "2026-04-02"},
            {"id": "grn-2", "branch_id": "branch-1", "purchase_order_id": "po-2", "supplier_id": "supplier-2", "received_on": "2026-04-06"},
        ],
        purchase_invoices=[
            {"id": "pinv-1", "branch_id": "branch-1", "supplier_id": "supplier-1", "goods_receipt_id": "grn-1", "invoice_number": "SPINV-2526-000021"},
            {"id": "pinv-2", "branch_id": "branch-1", "supplier_id": "supplier-2", "goods_receipt_id": "grn-2", "invoice_number": "SPINV-2526-000022"},
        ],
        supplier_returns=[
            {"id": "sret-1", "branch_id": "branch-1", "supplier_id": "supplier-2", "purchase_invoice_id": "pinv-2"},
        ],
        vendor_disputes=[
            {
                "id": "vdis-1",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "purchase_invoice_id": "pinv-2",
                "goods_receipt_id": None,
                "dispute_type": "RATE_MISMATCH",
                "status": "RESOLVED",
            }
        ],
        suppliers_by_id={
            "supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"},
            "supplier-2": {"id": "supplier-2", "name": "Ink Wholesale"},
        },
    )

    assert report == {
        "branch_id": "branch-1",
        "supplier_count": 2,
        "strong_count": 1,
        "watch_count": 0,
        "at_risk_count": 1,
        "records": [
            {
                "supplier_id": "supplier-2",
                "supplier_name": "Ink Wholesale",
                "approved_purchase_order_count": 1,
                "received_purchase_order_count": 1,
                "on_time_receipt_count": 0,
                "on_time_receipt_rate": 0.0,
                "average_receipt_delay_days": 5.0,
                "purchase_invoice_count": 1,
                "invoice_mismatch_count": 1,
                "invoice_mismatch_rate": 1.0,
                "supplier_return_count": 1,
                "supplier_return_rate": 1.0,
                "performance_status": "AT_RISK",
            },
            {
                "supplier_id": "supplier-1",
                "supplier_name": "Paper Supply Co",
                "approved_purchase_order_count": 1,
                "received_purchase_order_count": 1,
                "on_time_receipt_count": 1,
                "on_time_receipt_rate": 1.0,
                "average_receipt_delay_days": 1.0,
                "purchase_invoice_count": 1,
                "invoice_mismatch_count": 0,
                "invoice_mismatch_rate": 0.0,
                "supplier_return_count": 0,
                "supplier_return_rate": 0.0,
                "performance_status": "STRONG",
            },
        ],
    }
