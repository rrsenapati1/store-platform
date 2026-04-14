from store_control_plane.verification import run_control_plane_smoke
from conftest import sqlite_test_database_url


def test_run_control_plane_smoke_covers_admin_owner_and_runtime_paths() -> None:
    database_url = sqlite_test_database_url("control-plane-smoke")

    result = run_control_plane_smoke(database_url=database_url)

    assert result.allocated_barcode == "ACMETEACLASSIC"
    assert result.barcode_price_label == "Rs. 92.50"
    assert result.scanned_product_name == "Classic Tea"
    assert result.goods_receipt_number == "GRN-BLRFLAGSHIP-0001"
    assert result.tracked_batch_lot_count == 2
    assert result.expiring_batch_lot_count == 1
    assert result.batch_write_off_status == "EXPIRING_SOON"
    assert result.batch_write_off_remaining_quantity == 10.0
    assert result.sale_invoice_number == "SINV-BLRFLAGSHIP-0001"
    assert result.gst_export_status == "IRN_ATTACHED"
    assert result.attached_irn == "IRN-SMOKE-001"
    assert result.customer_directory_count == 1
    assert result.customer_history_sales_count == 1
    assert result.customer_report_repeat_count == 0
    assert result.queued_print_job_count == 1
    assert result.heartbeat_job_count == 1
    assert result.completed_print_job_status == "COMPLETED"
    assert result.failed_print_job_status == "FAILED"
    assert result.inventory_stock_on_hand == 19.0
    assert result.ledger_entry_types == ["PURCHASE_RECEIPT", "EXPIRY_WRITE_OFF", "SALE", "CUSTOMER_RETURN"]
