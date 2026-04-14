from store_control_plane.services.billing_policy import (
    build_sale_draft,
    ensure_sale_stock_available,
    sale_invoice_number,
)


def test_sale_invoice_number_normalizes_branch_code():
    assert sale_invoice_number(branch_code="blr-flagship", sequence_number=1) == "SINV-BLRFLAGSHIP-0001"


def test_sale_draft_builds_intra_state_b2b_gst_split():
    draft = build_sale_draft(
        line_inputs=[{"product_id": "product-1", "quantity": 4}],
        branch_gstin="29ABCDE1234F1Z5",
        customer_name="Acme Traders",
        customer_gstin="29AAEPM0111C1Z3",
        products_by_id={
            "product-1": {
                "product_id": "product-1",
                "name": "Classic Tea",
                "sku_code": "tea-classic-250g",
                "hsn_sac_code": "0902",
                "gst_rate": 5.0,
                "selling_price": 92.5,
            }
        },
        branch_catalog_items_by_product_id={
            "product-1": {
                "effective_selling_price": 92.5,
                "availability_status": "ACTIVE",
            }
        },
    )

    assert draft.invoice_kind == "B2B"
    assert draft.irn_status == "IRN_PENDING"
    assert draft.subtotal == 370.0
    assert draft.cgst_total == 9.25
    assert draft.sgst_total == 9.25
    assert draft.igst_total == 0.0
    assert draft.grand_total == 388.5
    assert [tax_line.tax_type for tax_line in draft.tax_lines] == ["CGST", "SGST"]


def test_sale_draft_builds_inter_state_b2b_igst():
    draft = build_sale_draft(
        line_inputs=[{"product_id": "product-1", "quantity": 2}],
        branch_gstin="29ABCDE1234F1Z5",
        customer_name="Acme Traders",
        customer_gstin="07AAEPM0111C1Z3",
        products_by_id={
            "product-1": {
                "product_id": "product-1",
                "name": "Classic Tea",
                "sku_code": "tea-classic-250g",
                "hsn_sac_code": "0902",
                "gst_rate": 5.0,
                "selling_price": 92.5,
            }
        },
        branch_catalog_items_by_product_id={
            "product-1": {
                "effective_selling_price": 92.5,
                "availability_status": "ACTIVE",
            }
        },
    )

    assert draft.invoice_kind == "B2B"
    assert draft.irn_status == "IRN_PENDING"
    assert draft.cgst_total == 0.0
    assert draft.sgst_total == 0.0
    assert draft.igst_total == 9.25
    assert [tax_line.tax_type for tax_line in draft.tax_lines] == ["IGST"]


def test_sale_stock_validation_blocks_overdraw():
    ensure_sale_stock_available(requested_quantity=4, available_quantity=8)

    try:
        ensure_sale_stock_available(requested_quantity=9, available_quantity=8)
    except ValueError as error:
        assert str(error) == "Insufficient stock for sale"
    else:
        raise AssertionError("Expected stock validation to reject overdrawn sale quantity")
