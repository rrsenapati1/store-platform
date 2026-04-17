from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def _exchange(client: TestClient, *, subject: str, email: str, name: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject=subject, email=email, name=name)},
    )
    assert response.status_code == 200
    return response.json()


def _create_owner_context(*, slug: str) -> tuple[TestClient, str, dict[str, str]]:
    database_url = sqlite_test_database_url(slug)
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
        json={"name": "Acme Retail", "slug": slug},
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
    return client, tenant_id, owner_headers


def test_promotion_campaign_can_be_created_updated_and_listed() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-campaign-create")

    created = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Diwali Welcome",
            "status": "ACTIVE",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "minimum_order_amount": 100.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": 500,
        },
    )
    assert created.status_code == 200
    campaign_id = created.json()["id"]
    assert created.json()["name"] == "Diwali Welcome"
    assert created.json()["discount_type"] == "FLAT_AMOUNT"
    assert created.json()["discount_value"] == 20.0
    assert created.json()["status"] == "ACTIVE"
    assert created.json()["priority"] == 100
    assert created.json()["stacking_rule"] == "STACKABLE"

    updated = client.patch(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}",
        headers=owner_headers,
        json={
            "name": "Diwali Welcome Updated",
            "minimum_order_amount": 150.0,
            "redemption_limit_total": 750,
            "priority": 250,
            "stacking_rule": "EXCLUSIVE",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Diwali Welcome Updated"
    assert updated.json()["minimum_order_amount"] == 150.0
    assert updated.json()["redemption_limit_total"] == 750
    assert updated.json()["priority"] == 250
    assert updated.json()["stacking_rule"] == "EXCLUSIVE"

    listed = client.get(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert [record["id"] for record in listed.json()["records"]] == [campaign_id]
    assert listed.json()["records"][0]["name"] == "Diwali Welcome Updated"
    assert listed.json()["records"][0]["priority"] == 250
    assert listed.json()["records"][0]["stacking_rule"] == "EXCLUSIVE"


def test_promotion_campaign_rejects_invalid_stacking_rule() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-campaign-invalid-stacking")

    created = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Broken stacking campaign",
            "status": "ACTIVE",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "priority": 100,
            "stacking_rule": "BROKEN",
        },
    )
    assert created.status_code == 400
    assert created.json()["detail"] == "Unsupported stacking rule"


def test_shared_promotion_codes_track_duplicates_and_campaign_status() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-code-duplicate")

    campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Weekend Percentage",
            "status": "ACTIVE",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": 200.0,
            "maximum_discount_amount": 40.0,
            "redemption_limit_total": None,
        },
    )
    assert campaign.status_code == 200
    campaign_id = campaign.json()["id"]

    code = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={
            "code": "WEEKEND10",
            "status": "ACTIVE",
            "redemption_limit_per_code": 100,
        },
    )
    assert code.status_code == 200
    assert code.json()["code"] == "WEEKEND10"
    assert code.json()["redemption_limit_per_code"] == 100
    assert code.json()["redemption_count"] == 0

    duplicate = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={
            "code": "WEEKEND10",
            "status": "ACTIVE",
            "redemption_limit_per_code": None,
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Promotion code already exists"

    disabled = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/disable",
        headers=owner_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"

    reactivated = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/reactivate",
        headers=owner_headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"


def test_automatic_promotion_campaign_supports_cart_and_item_category_rules() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-campaign-automatic")

    automatic_cart = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Weekend automatic cart",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "CART",
            "discount_type": "PERCENTAGE",
            "discount_value": 5.0,
            "minimum_order_amount": 100.0,
            "maximum_discount_amount": 40.0,
            "redemption_limit_total": None,
        },
    )
    assert automatic_cart.status_code == 200
    assert automatic_cart.json()["trigger_mode"] == "AUTOMATIC"
    assert automatic_cart.json()["scope"] == "CART"
    assert automatic_cart.json()["target_product_ids"] == []
    assert automatic_cart.json()["target_category_codes"] == []

    automatic_item_category = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Tea automatic discount",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "ITEM_CATEGORY",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
            "target_product_ids": ["product-tea-1"],
            "target_category_codes": ["TEA"],
        },
    )
    assert automatic_item_category.status_code == 200
    assert automatic_item_category.json()["trigger_mode"] == "AUTOMATIC"
    assert automatic_item_category.json()["scope"] == "ITEM_CATEGORY"
    assert automatic_item_category.json()["target_product_ids"] == ["product-tea-1"]
    assert automatic_item_category.json()["target_category_codes"] == ["TEA"]


def test_automatic_item_category_campaign_requires_targets_and_rejects_shared_codes() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-campaign-automatic-invalid")

    missing_targets = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Broken automatic item discount",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "ITEM_CATEGORY",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
            "target_product_ids": [],
            "target_category_codes": [],
        },
    )
    assert missing_targets.status_code == 400
    assert missing_targets.json()["detail"] == "Automatic item or category campaigns require at least one target"

    automatic_item_category = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Tea automatic item discount",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "ITEM_CATEGORY",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
            "target_category_codes": ["TEA"],
        },
    )
    assert automatic_item_category.status_code == 200
    campaign_id = automatic_item_category.json()["id"]

    shared_code = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={
            "code": "TEA10",
            "status": "ACTIVE",
            "redemption_limit_per_code": 100,
        },
    )
    assert shared_code.status_code == 400
    assert shared_code.json()["detail"] == "Automatic campaigns do not support shared promotion codes"


def test_assigned_voucher_campaign_requires_cart_flat_amount_and_rejects_shared_codes() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="promotion-campaign-assigned-voucher")

    invalid_scope = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Customer tea voucher",
            "status": "ACTIVE",
            "trigger_mode": "ASSIGNED_VOUCHER",
            "scope": "ITEM_CATEGORY",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 25.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert invalid_scope.status_code == 400
    assert invalid_scope.json()["detail"] == "Assigned voucher campaigns must use cart scope"

    invalid_discount_type = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Customer percentage voucher",
            "status": "ACTIVE",
            "trigger_mode": "ASSIGNED_VOUCHER",
            "scope": "CART",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "minimum_order_amount": None,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert invalid_discount_type.status_code == 400
    assert invalid_discount_type.json()["detail"] == "Assigned voucher campaigns must use flat amount discounts"

    assigned_voucher_campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "Customer welcome voucher",
            "status": "ACTIVE",
            "trigger_mode": "ASSIGNED_VOUCHER",
            "scope": "CART",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 25.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert assigned_voucher_campaign.status_code == 200
    campaign_id = assigned_voucher_campaign.json()["id"]
    assert assigned_voucher_campaign.json()["trigger_mode"] == "ASSIGNED_VOUCHER"

    shared_code = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns/{campaign_id}/codes",
        headers=owner_headers,
        json={
            "code": "WELCOME25",
            "status": "ACTIVE",
            "redemption_limit_per_code": 100,
        },
    )
    assert shared_code.status_code == 400
    assert shared_code.json()["detail"] == "Assigned voucher campaigns do not support shared promotion codes"


def test_customer_vouchers_can_be_issued_listed_and_canceled() -> None:
    client, tenant_id, owner_headers = _create_owner_context(slug="customer-voucher-issue")

    campaign = client.post(
        f"/v1/tenants/{tenant_id}/promotion-campaigns",
        headers=owner_headers,
        json={
            "name": "VIP voucher",
            "status": "ACTIVE",
            "trigger_mode": "ASSIGNED_VOUCHER",
            "scope": "CART",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 50.0,
            "minimum_order_amount": 100.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert campaign.status_code == 200
    campaign_id = campaign.json()["id"]

    customer_profile = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles",
        headers=owner_headers,
        json={
            "full_name": "Acme Traders",
            "phone": "+919999999999",
            "email": "billing@acme.example",
            "gstin": "29AAEPM0111C1Z3",
            "default_note": "Wholesale customer",
            "tags": ["wholesale"],
        },
    )
    assert customer_profile.status_code == 200
    customer_profile_id = customer_profile.json()["id"]

    issued = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers",
        headers=owner_headers,
        json={
            "campaign_id": campaign_id,
            "note": "Owner goodwill voucher",
        },
    )
    assert issued.status_code == 200
    assert issued.json()["campaign_id"] == campaign_id
    assert issued.json()["customer_profile_id"] == customer_profile_id
    assert issued.json()["voucher_amount"] == 50.0
    assert issued.json()["status"] == "ACTIVE"
    assert issued.json()["voucher_code"]
    voucher_id = issued.json()["id"]

    listed = client.get(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert [record["id"] for record in listed.json()["records"]] == [voucher_id]

    canceled = client.post(
        f"/v1/tenants/{tenant_id}/customer-profiles/{customer_profile_id}/vouchers/{voucher_id}/cancel",
        headers=owner_headers,
        json={"note": "Voucher voided before checkout"},
    )
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "CANCELED"
