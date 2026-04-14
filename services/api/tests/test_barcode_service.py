from store_api.barcode_service import allocate_barcode, build_barcode_label_model, normalize_barcode


def test_allocate_barcode_prefers_existing_and_falls_back_to_tenant_plus_sku():
    assert allocate_barcode(tenant_name="Acme Retail", sku_code="SKU-001", existing=" 8901234567890 ") == "8901234567890"
    assert allocate_barcode(tenant_name="Acme Retail", sku_code="SKU-001", existing="") == "ACMESKU001"


def test_build_barcode_label_model_formats_print_friendly_price():
    assert build_barcode_label_model(
        sku_code="SKU-001",
        product_name="Notebook",
        barcode=normalize_barcode(" 8901234567890 "),
        selling_price=112,
    ) == {
        "sku_code": "SKU-001",
        "product_name": "Notebook",
        "barcode": "8901234567890",
        "price_label": "Rs. 112.00",
    }
