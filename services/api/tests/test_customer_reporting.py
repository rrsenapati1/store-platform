from store_api.customer_reporting import build_branch_customer_report, build_customer_directory_records, build_customer_history_report


def test_customer_directory_filters_and_enriches_last_invoice_context():
    records = build_customer_directory_records(
        customers=[
            {
                "id": "customer-1",
                "name": "Acme Traders",
                "phone": "9876543210",
                "gstin": "29BBBBB2222B1Z5",
                "visit_count": 3,
                "lifetime_value": 842.4,
                "last_sale_id": "sale-1",
            },
            {
                "id": "customer-2",
                "name": "Walk In",
                "phone": "9000000000",
                "gstin": None,
                "visit_count": 0,
                "lifetime_value": 0,
                "last_sale_id": None,
            },
        ],
        sales_by_id={
            "sale-1": {
                "id": "sale-1",
                "branch_id": "branch-1",
                "invoice_id": "invoice-1",
            }
        },
        invoices_by_id={
            "invoice-1": {
                "id": "invoice-1",
                "invoice_number": "SINV-2526-000011",
            }
        },
        query="3210",
    )

    assert records == [
        {
            "customer_id": "customer-1",
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
            "visit_count": 3,
            "lifetime_value": 842.4,
            "last_sale_id": "sale-1",
            "last_invoice_number": "SINV-2526-000011",
            "last_branch_id": "branch-1",
        }
    ]


def test_customer_history_report_summarizes_sales_returns_and_exchanges():
    report = build_customer_history_report(
        customer={
            "id": "customer-1",
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
            "visit_count": 1,
            "lifetime_value": 236,
            "last_sale_id": "sale-1",
        },
        sales=[
            {
                "id": "sale-1",
                "branch_id": "branch-1",
                "invoice_id": "invoice-1",
                "customer_id": "customer-1",
                "payment_method": "cash",
            }
        ],
        invoices_by_id={
            "invoice-1": {
                "id": "invoice-1",
                "invoice_number": "SINV-2526-000011",
                "grand_total": 236,
            }
        },
        sale_returns=[
            {
                "id": "sale-return-1",
                "sale_id": "sale-1",
                "branch_id": "branch-1",
                "credit_note_id": "credit-note-1",
                "refund_amount": 118,
                "status": "REFUND_APPROVED",
            }
        ],
        credit_notes_by_id={
            "credit-note-1": {
                "id": "credit-note-1",
                "credit_note_number": "SCN-2526-000004",
                "grand_total": 118,
            }
        },
        exchange_orders=[
            {
                "id": "exchange-1",
                "sale_id": "sale-1",
                "branch_id": "branch-1",
                "return_total": 118,
                "replacement_total": 200,
                "balance_direction": "COLLECT_FROM_CUSTOMER",
                "balance_amount": 82,
            }
        ],
    )

    assert report == {
        "customer": {
            "customer_id": "customer-1",
            "name": "Acme Traders",
            "phone": "9876543210",
            "gstin": "29BBBBB2222B1Z5",
            "visit_count": 1,
            "lifetime_value": 236.0,
            "last_sale_id": "sale-1",
        },
        "sales_summary": {
            "sales_count": 1,
            "sales_total": 236.0,
            "return_count": 1,
            "credit_note_total": 118.0,
            "exchange_count": 1,
        },
        "sales": [
            {
                "sale_id": "sale-1",
                "branch_id": "branch-1",
                "invoice_id": "invoice-1",
                "invoice_number": "SINV-2526-000011",
                "grand_total": 236.0,
                "payment_method": "cash",
            }
        ],
        "returns": [
            {
                "sale_return_id": "sale-return-1",
                "sale_id": "sale-1",
                "branch_id": "branch-1",
                "credit_note_id": "credit-note-1",
                "credit_note_number": "SCN-2526-000004",
                "grand_total": 118.0,
                "refund_amount": 118.0,
                "status": "REFUND_APPROVED",
            }
        ],
        "exchanges": [
            {
                "exchange_order_id": "exchange-1",
                "sale_id": "sale-1",
                "branch_id": "branch-1",
                "return_total": 118.0,
                "replacement_total": 200.0,
                "balance_direction": "COLLECT_FROM_CUSTOMER",
                "balance_amount": 82.0,
            }
        ],
    }


def test_branch_customer_report_tracks_repeat_buyers_and_return_activity():
    report = build_branch_customer_report(
        branch_id="branch-1",
        customers_by_id={
            "customer-1": {"id": "customer-1", "name": "Acme Traders"},
            "customer-2": {"id": "customer-2", "name": "Beta Stores"},
        },
        sales=[
            {"id": "sale-1", "branch_id": "branch-1", "customer_id": "customer-1", "invoice_id": "invoice-1"},
            {"id": "sale-2", "branch_id": "branch-1", "customer_id": "customer-1", "invoice_id": "invoice-2"},
            {"id": "sale-3", "branch_id": "branch-1", "customer_id": "customer-2", "invoice_id": "invoice-3"},
            {"id": "sale-4", "branch_id": "branch-1", "customer_id": None, "invoice_id": "invoice-4"},
            {"id": "sale-5", "branch_id": "branch-2", "customer_id": "customer-1", "invoice_id": "invoice-5"},
        ],
        invoices_by_id={
            "invoice-1": {"invoice_number": "SINV-1", "grand_total": 236},
            "invoice-2": {"invoice_number": "SINV-2", "grand_total": 118},
            "invoice-3": {"invoice_number": "SINV-3", "grand_total": 118},
            "invoice-4": {"invoice_number": "SINV-4", "grand_total": 59},
            "invoice-5": {"invoice_number": "SINV-5", "grand_total": 236},
        },
        sale_returns=[
            {"sale_id": "sale-1", "credit_note_id": "credit-note-1"},
            {"sale_id": "sale-5", "credit_note_id": "credit-note-2"},
        ],
        credit_notes_by_id={
            "credit-note-1": {"grand_total": 118},
            "credit-note-2": {"grand_total": 118},
        },
        exchange_orders=[
            {"sale_id": "sale-2", "branch_id": "branch-1"},
            {"sale_id": "sale-5", "branch_id": "branch-2"},
        ],
    )

    assert report == {
        "branch_id": "branch-1",
        "customer_count": 2,
        "repeat_customer_count": 1,
        "anonymous_sales_count": 1,
        "anonymous_sales_total": 59.0,
        "top_customers": [
            {
                "customer_id": "customer-1",
                "customer_name": "Acme Traders",
                "sales_count": 2,
                "sales_total": 354.0,
                "last_invoice_number": "SINV-2",
            },
            {
                "customer_id": "customer-2",
                "customer_name": "Beta Stores",
                "sales_count": 1,
                "sales_total": 118.0,
                "last_invoice_number": "SINV-3",
            },
        ],
        "return_activity": [
            {
                "customer_id": "customer-1",
                "customer_name": "Acme Traders",
                "return_count": 1,
                "credit_note_total": 118.0,
                "exchange_count": 1,
            }
        ],
    }
