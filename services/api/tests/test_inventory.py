from store_api.inventory import InventoryLedgerService


def test_purchase_sale_and_return_update_stock_snapshot():
    service = InventoryLedgerService()
    service.post_entry(item_id="sku-1", branch_id="branch-1", quantity=10, entry_type="PURCHASE_RECEIPT")
    service.post_entry(item_id="sku-1", branch_id="branch-1", quantity=-3, entry_type="SALE")
    service.post_entry(item_id="sku-1", branch_id="branch-1", quantity=1, entry_type="CUSTOMER_RETURN")

    assert service.stock_on_hand(item_id="sku-1", branch_id="branch-1") == 8


def test_ledger_rejects_unknown_entry_type():
    service = InventoryLedgerService()

    try:
        service.post_entry(item_id="sku-1", branch_id="branch-1", quantity=1, entry_type="UNKNOWN")
    except ValueError as exc:
        assert "Unsupported ledger entry type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown ledger entry type")


def test_transfer_stock_posts_outbound_and_inbound_entries():
    service = InventoryLedgerService()
    service.post_entry(item_id="sku-1", branch_id="branch-a", quantity=10, entry_type="PURCHASE_RECEIPT")

    result = service.transfer_stock(
        item_id="sku-1",
        source_branch_id="branch-a",
        destination_branch_id="branch-b",
        quantity=4,
    )

    assert result == {
        "product_id": "sku-1",
        "quantity": 4,
        "source_stock_after": 6,
        "destination_stock_after": 4,
    }


def test_stock_count_posts_variance_to_match_counted_quantity():
    service = InventoryLedgerService()
    service.post_entry(item_id="sku-1", branch_id="branch-a", quantity=10, entry_type="PURCHASE_RECEIPT")

    result = service.apply_stock_count(
        item_id="sku-1",
        branch_id="branch-a",
        counted_quantity=8,
    )

    assert result == {
        "product_id": "sku-1",
        "expected_quantity": 10,
        "counted_quantity": 8,
        "variance_quantity": -2,
        "closing_stock": 8,
    }
