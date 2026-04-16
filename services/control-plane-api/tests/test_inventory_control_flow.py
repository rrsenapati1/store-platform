from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def test_owner_adjusts_counts_and_transfers_inventory_on_control_plane():
    database_url = sqlite_test_database_url("inventory-control")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch_one = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch_one.status_code == 200
    branch_one_id = branch_one.json()["id"]

    branch_two = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Mysuru Hub", "code": "mysuru-hub", "gstin": "29ABCDE1234F1Z6"},
    )
    assert branch_two.status_code == 200
    branch_two_id = branch_two.json()["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "8901234567890",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "selling_price": 92.5,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/purchase-orders",
        headers=owner_headers,
        json={
            "supplier_id": supplier_id,
            "lines": [{"product_id": product_id, "quantity": 24, "unit_cost": 61.5}],
        },
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Need replenishment before the weekend rush"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for branch restock"},
    )
    assert approved.status_code == 200

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200

    adjustment = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/stock-adjustments",
        headers=owner_headers,
        json={"product_id": product_id, "quantity_delta": -2, "reason": "Shelf damage", "note": "Two packs damaged"},
    )
    assert adjustment.status_code == 200
    assert adjustment.json()["resulting_stock_on_hand"] == 22.0

    stock_count_session = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/stock-count-sessions",
        headers=owner_headers,
        json={"product_id": product_id, "note": "Cycle count before transfer"},
    )
    assert stock_count_session.status_code == 200
    stock_count_session_id = stock_count_session.json()["id"]
    assert stock_count_session.json()["status"] == "OPEN"

    stock_count_board_before = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/stock-count-board",
        headers=owner_headers,
    )
    assert stock_count_board_before.status_code == 200
    assert stock_count_board_before.json()["open_count"] == 1
    assert stock_count_board_before.json()["counted_count"] == 0

    record_count = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/stock-count-sessions/{stock_count_session_id}/record",
        headers=owner_headers,
        json={"counted_quantity": 20, "note": "Cycle count before transfer"},
    )
    assert record_count.status_code == 200
    assert record_count.json()["status"] == "COUNTED"
    assert record_count.json()["expected_quantity"] == 22.0
    assert record_count.json()["variance_quantity"] == -2.0

    snapshot_before_approval = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert snapshot_before_approval.status_code == 200
    assert snapshot_before_approval.json()["records"][0]["stock_on_hand"] == 22.0

    approved_count = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/stock-count-sessions/{stock_count_session_id}/approve",
        headers=owner_headers,
        json={"review_note": "Approved after blind count review"},
    )
    assert approved_count.status_code == 200
    assert approved_count.json()["session"]["status"] == "APPROVED"
    assert approved_count.json()["stock_count"]["expected_quantity"] == 22.0
    assert approved_count.json()["stock_count"]["variance_quantity"] == -2.0
    assert approved_count.json()["stock_count"]["closing_stock"] == 20.0

    stock_count_board_after = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/stock-count-board",
        headers=owner_headers,
    )
    assert stock_count_board_after.status_code == 200
    assert stock_count_board_after.json()["approved_count"] == 1
    assert stock_count_board_after.json()["records"][0]["status"] == "APPROVED"

    transfer = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/transfers",
        headers=owner_headers,
        json={"destination_branch_id": branch_two_id, "product_id": product_id, "quantity": 5, "note": "Rebalance stock"},
    )
    assert transfer.status_code == 200
    assert transfer.json()["transfer_number"] == "TRF-BLRFLAGSHIP-0001"

    source_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert source_snapshot.status_code == 200
    assert source_snapshot.json()["records"][0]["stock_on_hand"] == 15.0

    destination_snapshot = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_two_id}/inventory-snapshot",
        headers=owner_headers,
    )
    assert destination_snapshot.status_code == 200
    assert destination_snapshot.json()["records"][0]["stock_on_hand"] == 5.0

    source_transfer_board = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/transfer-board",
        headers=owner_headers,
    )
    assert source_transfer_board.status_code == 200
    assert source_transfer_board.json()["outbound_count"] == 1
    assert source_transfer_board.json()["records"][0]["direction"] == "OUTBOUND"
    assert source_transfer_board.json()["records"][0]["counterparty_branch_name"] == "Mysuru Hub"

    inventory_ledger = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_one_id}/inventory-ledger",
        headers=owner_headers,
    )
    assert inventory_ledger.status_code == 200
    assert [record["entry_type"] for record in inventory_ledger.json()["records"]] == [
        "PURCHASE_RECEIPT",
        "ADJUSTMENT",
        "COUNT_VARIANCE",
        "TRANSFER_OUT",
    ]
