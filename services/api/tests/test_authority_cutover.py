from fastapi.testclient import TestClient

from store_api.main import create_app


def test_legacy_api_marks_migrated_writes_as_deprecated_in_shadow_mode():
    client = TestClient(create_app())

    response = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    )

    assert response.status_code == 200
    assert response.headers["X-Store-Legacy-Authority-Status"] == "deprecated"
    assert response.headers["X-Store-Legacy-Domain"] == "onboarding"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_blocks_migrated_writes_in_cutover_mode():
    client = TestClient(create_app(legacy_write_mode="cutover"))

    response = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Legacy API write is disabled for migrated domain: onboarding"
    assert response.headers["X-Store-Legacy-Authority-Status"] == "cutover"
    assert response.headers["X-Store-Legacy-Domain"] == "onboarding"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_marks_barcode_foundation_writes_as_deprecated_in_shadow_mode():
    client = TestClient(create_app())

    tenant_response = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    )
    assert tenant_response.status_code == 200
    tenant_id = tenant_response.json()["id"]

    response = client.post(
        f"/v1/tenants/{tenant_id}/barcode-allocations",
        headers={"x-actor-role": "tenant_owner"},
        json={"sku_code": "tea-classic-250g"},
    )

    assert response.status_code == 200
    assert response.headers["X-Store-Legacy-Authority-Status"] == "deprecated"
    assert response.headers["X-Store-Legacy-Domain"] == "barcode_foundation"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_marks_batch_tracking_writes_as_deprecated_in_shadow_mode():
    client = TestClient(create_app())

    tenant_response = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    )
    assert tenant_response.status_code == 200
    tenant_id = tenant_response.json()["id"]

    branch_response = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Bengaluru Flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch_response.status_code == 200
    branch_id = branch_response.json()["id"]

    product_response = client.post(
        f"/v1/tenants/{tenant_id}/products",
        headers={"x-actor-role": "catalog_admin"},
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "ACMETEACLASSIC",
            "tax_rate_percent": 5.0,
            "hsn_sac_code": "0902",
            "selling_price": 92.5,
        },
    )
    assert product_response.status_code == 200
    product_id = product_response.json()["id"]

    supplier_response = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers={"x-actor-role": "inventory_admin"},
        json={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3"},
    )
    assert supplier_response.status_code == 200
    supplier_id = supplier_response.json()["id"]

    purchase_order_response = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers={"x-actor-role": "inventory_admin"},
        json={"supplier_id": supplier_id, "lines": [{"product_id": product_id, "quantity": 10, "unit_cost": 61.5}]},
    )
    assert purchase_order_response.status_code == 200
    purchase_order_id = purchase_order_response.json()["id"]

    submit_response = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers={"x-actor-role": "inventory_admin"},
        json={"note": "Ready"},
    )
    assert submit_response.status_code == 200

    approve_response = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers={"x-actor-role": "tenant_owner"},
        json={"note": "Approved"},
    )
    assert approve_response.status_code == 200

    goods_receipt_response = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers={"x-actor-role": "inventory_admin"},
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt_response.status_code == 200
    goods_receipt_id = goods_receipt_response.json()["id"]

    response = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt_id}/batch-lots",
        headers={"x-actor-role": "inventory_admin"},
        json={
            "lots": [
                {"product_id": product_id, "batch_number": "BATCH-A", "quantity": 10, "expiry_date": "2026-04-21"}
            ]
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Store-Legacy-Authority-Status"] == "deprecated"
    assert response.headers["X-Store-Legacy-Domain"] == "batch_tracking"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_blocks_compliance_export_writes_in_cutover_mode():
    client = TestClient(create_app(legacy_write_mode="cutover"))

    response = client.post(
        "/v1/tenants/tenant-acme/branches/branch-1/compliance/gst-exports",
        headers={"x-actor-role": "tenant_owner"},
        json={"invoice_id": "invoice-1"},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Legacy API write is disabled for migrated domain: compliance_exports"
    assert response.headers["X-Store-Legacy-Authority-Status"] == "cutover"
    assert response.headers["X-Store-Legacy-Domain"] == "compliance_exports"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_blocks_customer_reporting_writes_in_cutover_mode():
    client = TestClient(create_app(legacy_write_mode="cutover"))

    response = client.post(
        "/v1/tenants/tenant-acme/customers",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Walk In", "phone": "9876543210"},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Legacy API write is disabled for migrated domain: customer_reporting"
    assert response.headers["X-Store-Legacy-Authority-Status"] == "cutover"
    assert response.headers["X-Store-Legacy-Domain"] == "customer_reporting"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_blocks_supplier_reporting_writes_in_cutover_mode():
    client = TestClient(create_app(legacy_write_mode="cutover"))

    response = client.post(
        "/v1/tenants/tenant-acme/branches/branch-1/vendor-disputes",
        headers={"x-actor-role": "tenant_owner"},
        json={"goods_receipt_id": "grn-1", "dispute_type": "SHORT_SUPPLY", "note": "Boxes missing"},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Legacy API write is disabled for migrated domain: supplier_reporting"
    assert response.headers["X-Store-Legacy-Authority-Status"] == "cutover"
    assert response.headers["X-Store-Legacy-Domain"] == "supplier_reporting"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_blocks_sync_runtime_writes_in_cutover_mode():
    client = TestClient(create_app(legacy_write_mode="cutover"))

    response = client.post(
        "/v1/sync/push",
        headers={"x-actor-role": "store_manager"},
        json={"record_id": "sale-1", "client_version": 1, "server_version": 1},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Legacy API write is disabled for migrated domain: sync_runtime"
    assert response.headers["X-Store-Legacy-Authority-Status"] == "cutover"
    assert response.headers["X-Store-Legacy-Domain"] == "sync_runtime"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"


def test_legacy_api_blocks_runtime_print_writes_in_cutover_mode():
    client = TestClient(create_app(legacy_write_mode="cutover"))

    response = client.post(
        "/v1/tenants/tenant-acme/branches/branch-1/print-jobs/barcode-labels",
        headers={"x-actor-role": "catalog_admin"},
        json={"product_id": "product-1", "device_id": "device-1", "copies": 2},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Legacy API write is disabled for migrated domain: runtime_print"
    assert response.headers["X-Store-Legacy-Authority-Status"] == "cutover"
    assert response.headers["X-Store-Legacy-Domain"] == "runtime_print"
    assert response.headers["X-Store-Authority-Owner"] == "control-plane"
