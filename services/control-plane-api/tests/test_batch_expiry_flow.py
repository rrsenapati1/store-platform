from datetime import timedelta

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.utils import utc_now


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def test_owner_records_goods_receipt_batch_lots_and_posts_expiry_write_off() -> None:
    database_url = sqlite_test_database_url("batch-expiry-foundation")
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
        json={"name": "Acme Retail", "slug": "acme-retail-batch"},
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

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    product = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "selling_price": 92.5,
        },
    )
    assert product.status_code == 200
    product_id = product.json()["id"]

    branch_item = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
        json={"product_id": product_id, "selling_price_override": None, "availability_status": "ACTIVE"},
    )
    assert branch_item.status_code == 200

    supplier = client.post(
        f"/v1/tenants/{tenant_id}/suppliers",
        headers=owner_headers,
        json={"name": "Acme Tea Traders", "gstin": "29AAEPM0111C1Z3", "payment_terms_days": 14},
    )
    assert supplier.status_code == 200
    supplier_id = supplier.json()["id"]

    purchase_order = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders",
        headers=owner_headers,
        json={"supplier_id": supplier_id, "lines": [{"product_id": product_id, "quantity": 10, "unit_cost": 61.5}]},
    )
    assert purchase_order.status_code == 200
    purchase_order_id = purchase_order.json()["id"]

    submitted = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval",
        headers=owner_headers,
        json={"note": "Ready for lot intake"},
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve",
        headers=owner_headers,
        json={"note": "Approved for lot intake"},
    )
    assert approved.status_code == 200

    goods_receipt = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts",
        headers=owner_headers,
        json={"purchase_order_id": purchase_order_id},
    )
    assert goods_receipt.status_code == 200
    goods_receipt_id = goods_receipt.json()["id"]

    report_as_of = utc_now().date()
    soon_expiry = (report_as_of + timedelta(days=7)).isoformat()
    fresh_expiry = (report_as_of + timedelta(days=90)).isoformat()

    batch_lots = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt_id}/batch-lots",
        headers=owner_headers,
        json={
            "lots": [
                {"product_id": product_id, "batch_number": "BATCH-A", "quantity": 6, "expiry_date": soon_expiry},
                {"product_id": product_id, "batch_number": "BATCH-B", "quantity": 4, "expiry_date": fresh_expiry},
            ]
        },
    )

    assert batch_lots.status_code == 200
    assert [record["batch_number"] for record in batch_lots.json()["records"]] == ["BATCH-A", "BATCH-B"]

    initial_report = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
        headers=owner_headers,
    )
    assert initial_report.status_code == 200
    assert initial_report.json()["tracked_lot_count"] == 2
    assert initial_report.json()["expiring_soon_count"] == 1

    sale = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/sales",
        headers=owner_headers,
        json={
            "customer_name": "Walk In",
            "customer_gstin": None,
            "payment_method": "Cash",
            "lines": [{"product_id": product_id, "quantity": 5}],
        },
    )
    assert sale.status_code == 200

    report_after_sale = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
        headers=owner_headers,
    )
    assert report_after_sale.status_code == 200
    assert report_after_sale.json()["records"][0]["remaining_quantity"] == 1.0
    assert report_after_sale.json()["records"][1]["remaining_quantity"] == 4.0

    write_off = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-lots/{batch_lots.json()['records'][0]['id']}/expiry-write-offs",
        headers=owner_headers,
        json={"quantity": 1, "reason": "Expired on shelf"},
    )
    assert write_off.status_code == 200
    assert write_off.json()["written_off_quantity"] == 1.0
    assert write_off.json()["remaining_quantity"] == 0.0

    report_after_write_off = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report",
        headers=owner_headers,
    )
    assert report_after_write_off.status_code == 200
    assert report_after_write_off.json()["tracked_lot_count"] == 1
    assert report_after_write_off.json()["records"] == [
        {
            "batch_lot_id": batch_lots.json()["records"][1]["id"],
            "product_id": product_id,
            "product_name": "Classic Tea",
            "batch_number": "BATCH-B",
            "expiry_date": fresh_expiry,
            "days_to_expiry": 90,
            "received_quantity": 4.0,
            "written_off_quantity": 0.0,
            "remaining_quantity": 4.0,
            "status": "FRESH",
        }
    ]

    inventory_ledger = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger",
        headers=owner_headers,
    )
    assert inventory_ledger.status_code == 200
    assert inventory_ledger.json()["records"][-1]["entry_type"] == "EXPIRY_WRITE_OFF"
