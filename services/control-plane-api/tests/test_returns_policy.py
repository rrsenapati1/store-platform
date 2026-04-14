from store_control_plane.services.returns_policy import (
    build_sale_return_draft,
    credit_note_number,
    ensure_refund_amount_allowed,
)


def test_credit_note_number_normalizes_branch_code() -> None:
    assert credit_note_number(branch_code="blr-flagship", sequence_number=7) == "SCN-BLRFLAGSHIP-0007"


def test_build_sale_return_draft_generates_intra_state_credit_note_totals() -> None:
    draft = build_sale_return_draft(
        branch_gstin="29ABCDE1234F1Z5",
        sale_customer_name="Acme Traders",
        sale_customer_gstin="29AAEPM0111C1Z3",
        sale_lines_by_product_id={
            "product-1": {
                "product_id": "product-1",
                "product_name": "Classic Tea",
                "sku_code": "tea-classic-250g",
                "hsn_sac_code": "0902",
                "quantity": 4.0,
                "unit_price": 92.5,
                "gst_rate": 5.0,
            }
        },
        prior_returned_quantities_by_product_id={"product-1": 1.0},
        requested_lines=[{"product_id": "product-1", "quantity": 2.0}],
    )

    assert draft.subtotal == 185.0
    assert draft.cgst_total == 4.62
    assert draft.sgst_total == 4.63
    assert draft.igst_total == 0.0
    assert draft.grand_total == 194.25
    assert [tax_line.tax_type for tax_line in draft.tax_lines] == ["CGST", "SGST"]


def test_build_sale_return_draft_rejects_excess_return_quantity() -> None:
    try:
        build_sale_return_draft(
            branch_gstin="29ABCDE1234F1Z5",
            sale_customer_name="Acme Traders",
            sale_customer_gstin="29AAEPM0111C1Z3",
            sale_lines_by_product_id={
                "product-1": {
                    "product_id": "product-1",
                    "product_name": "Classic Tea",
                    "sku_code": "tea-classic-250g",
                    "hsn_sac_code": "0902",
                    "quantity": 4.0,
                    "unit_price": 92.5,
                    "gst_rate": 5.0,
                }
            },
            prior_returned_quantities_by_product_id={"product-1": 3.0},
            requested_lines=[{"product_id": "product-1", "quantity": 2.0}],
        )
    except ValueError as error:
        assert str(error) == "Return quantity exceeds remaining sale quantity"
    else:
        raise AssertionError("Expected sale return draft to reject excessive quantity")


def test_refund_amount_must_fit_credit_note_and_remaining_balance() -> None:
    ensure_refund_amount_allowed(
        requested_refund_amount=97.12,
        credit_note_total=97.12,
        remaining_refundable_amount=291.37,
    )

    for requested_refund_amount, expected_message in (
        (97.13, "Refund exceeds credit note value"),
        (300.0, "Refund exceeds remaining sale balance"),
    ):
        try:
            ensure_refund_amount_allowed(
                requested_refund_amount=requested_refund_amount,
                credit_note_total=97.12,
                remaining_refundable_amount=291.37,
            )
        except ValueError as error:
            assert str(error) == expected_message
        else:
            raise AssertionError("Expected refund validation to reject invalid amount")
