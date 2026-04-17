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


def _seed_pricing_context(client: TestClient, *, slug: str) -> dict[str, object]:
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

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    tea = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "barcode": "8901234567890",
            "hsn_sac_code": "0902",
            "gst_rate": 5.0,
            "mrp": 120.0,
            "category_code": "TEA",
            "selling_price": 92.5,
        },
    )
    assert tea.status_code == 200
    tea_product_id = tea.json()["id"]

    coffee = client.post(
        f"/v1/tenants/{tenant_id}/catalog/products",
        headers=owner_headers,
        json={
            "name": "Roast Coffee",
            "sku_code": "coffee-roast-200g",
            "barcode": "8901234567891",
            "hsn_sac_code": "0901",
            "gst_rate": 5.0,
            "mrp": 150.0,
            "category_code": "COFFEE",
            "selling_price": 110.0,
        },
    )
    assert coffee.status_code == 200
    coffee_product_id = coffee.json()["id"]

    for product_id in (tea_product_id, coffee_product_id):
        branch_catalog_item = client.post(
            f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
            headers=owner_headers,
            json={
                "product_id": product_id,
                "selling_price_override": None,
                "availability_status": "ACTIVE",
            },
        )
        assert branch_catalog_item.status_code == 200

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "owner_headers": owner_headers,
        "tea_product_id": tea_product_id,
        "coffee_product_id": coffee_product_id,
    }


def test_checkout_price_preview_applies_best_automatic_item_discount_before_code_discount() -> None:
    database_url = sqlite_test_database_url("checkout-price-preview-best-automatic")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_pricing_context(client, slug="checkout-price-preview-best-automatic")

    cart_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
        json={
            "name": "Weekend cart discount",
            "status": "ACTIVE",
            "trigger_mode": "AUTOMATIC",
            "scope": "CART",
            "discount_type": "PERCENTAGE",
            "discount_value": 5.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert cart_campaign.status_code == 200

    item_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
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
            "target_category_codes": ["TEA"],
        },
    )
    assert item_campaign.status_code == 200

    code_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
        json={
            "name": "WELCOME flat discount",
            "status": "ACTIVE",
            "trigger_mode": "CODE",
            "scope": "CART",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert code_campaign.status_code == 200

    code = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns/{code_campaign.json()['id']}/codes",
        headers=context["owner_headers"],
        json={"code": "WELCOME20", "status": "ACTIVE", "redemption_limit_per_code": None},
    )
    assert code.status_code == 200

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["owner_headers"],
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "promotion_code": "WELCOME20",
            "loyalty_points_to_redeem": 0,
            "store_credit_amount": 0,
            "lines": [{"product_id": context["tea_product_id"], "quantity": 1}],
        },
    )
    assert preview.status_code == 200
    assert preview.json()["automatic_campaign"]["name"] == "Tea automatic discount"
    assert preview.json()["promotion_code_campaign"]["code"] == "WELCOME20"
    assert preview.json()["summary"]["mrp_total"] == 120.0
    assert preview.json()["summary"]["selling_price_subtotal"] == 92.5
    assert preview.json()["summary"]["automatic_discount_total"] == 9.25
    assert preview.json()["summary"]["promotion_code_discount_total"] == 20.0
    assert preview.json()["summary"]["invoice_total"] == 66.41
    assert preview.json()["summary"]["final_payable_amount"] == 66.41
    assert preview.json()["lines"] == [
        {
            "product_id": context["tea_product_id"],
            "product_name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "quantity": 1.0,
            "mrp": 120.0,
            "unit_selling_price": 92.5,
            "automatic_discount_amount": 9.25,
            "promotion_code_discount_amount": 20.0,
            "promotion_discount_source": "AUTOMATIC_ITEM_CATEGORY+CODE",
            "taxable_amount": 63.25,
            "tax_amount": 3.16,
            "line_total": 66.41,
        }
    ]


def test_checkout_price_preview_applies_category_targets_only_to_matching_lines() -> None:
    database_url = sqlite_test_database_url("checkout-price-preview-category-targets")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_pricing_context(client, slug="checkout-price-preview-category-targets")

    item_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
        json={
            "name": "Tea-only discount",
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
    assert item_campaign.status_code == 200

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["owner_headers"],
        json={
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "lines": [
                {"product_id": context["tea_product_id"], "quantity": 1},
                {"product_id": context["coffee_product_id"], "quantity": 1},
            ],
        },
    )
    assert preview.status_code == 200
    assert preview.json()["summary"]["automatic_discount_total"] == 9.25
    assert preview.json()["summary"]["selling_price_subtotal"] == 202.5
    assert preview.json()["summary"]["invoice_total"] == 202.91
    assert preview.json()["lines"][0]["product_id"] == context["tea_product_id"]
    assert preview.json()["lines"][0]["automatic_discount_amount"] == 9.25
    assert preview.json()["lines"][1]["product_id"] == context["coffee_product_id"]
    assert preview.json()["lines"][1]["automatic_discount_amount"] == 0.0


def test_checkout_price_preview_applies_customer_voucher_after_automatic_discount() -> None:
    database_url = sqlite_test_database_url("checkout-price-preview-customer-voucher")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_pricing_context(client, slug="checkout-price-preview-customer-voucher")

    automatic_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
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
            "target_category_codes": ["TEA"],
        },
    )
    assert automatic_campaign.status_code == 200

    voucher_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
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
    assert voucher_campaign.status_code == 200

    customer_profile = client.post(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles",
        headers=context["owner_headers"],
        json={
            "full_name": "Acme Traders",
            "phone": "+919999999999",
            "email": "billing@acme.example",
            "gstin": "29AAEPM0111C1Z3",
        },
    )
    assert customer_profile.status_code == 200
    customer_profile_id = customer_profile.json()["id"]

    issued_voucher = client.post(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles/{customer_profile_id}/vouchers",
        headers=context["owner_headers"],
        json={"campaign_id": voucher_campaign.json()["id"]},
    )
    assert issued_voucher.status_code == 200
    voucher_id = issued_voucher.json()["id"]

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["owner_headers"],
        json={
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "customer_gstin": "29AAEPM0111C1Z3",
            "customer_voucher_id": voucher_id,
            "lines": [{"product_id": context["tea_product_id"], "quantity": 1}],
        },
    )
    assert preview.status_code == 200
    assert preview.json()["automatic_campaign"]["name"] == "Tea automatic discount"
    assert preview.json()["customer_voucher"]["id"] == voucher_id
    assert preview.json()["summary"]["automatic_discount_total"] == 9.25
    assert preview.json()["summary"]["customer_voucher_discount_total"] == 25.0
    assert preview.json()["summary"]["invoice_total"] == 61.16
    assert preview.json()["summary"]["final_payable_amount"] == 61.16
    assert preview.json()["lines"] == [
        {
            "product_id": context["tea_product_id"],
            "product_name": "Classic Tea",
            "sku_code": "tea-classic-250g",
            "quantity": 1.0,
            "mrp": 120.0,
            "unit_selling_price": 92.5,
            "automatic_discount_amount": 9.25,
            "promotion_code_discount_amount": 0.0,
            "customer_voucher_discount_amount": 25.0,
            "promotion_discount_source": "AUTOMATIC_ITEM_CATEGORY+ASSIGNED_VOUCHER",
            "taxable_amount": 58.25,
            "tax_amount": 2.91,
            "line_total": 61.16,
        }
    ]


def test_checkout_price_preview_rejects_code_and_customer_voucher_together() -> None:
    database_url = sqlite_test_database_url("checkout-price-preview-voucher-conflict")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _seed_pricing_context(client, slug="checkout-price-preview-voucher-conflict")

    code_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
        json={
            "name": "WELCOME flat discount",
            "status": "ACTIVE",
            "trigger_mode": "CODE",
            "scope": "CART",
            "discount_type": "FLAT_AMOUNT",
            "discount_value": 20.0,
            "minimum_order_amount": 50.0,
            "maximum_discount_amount": None,
            "redemption_limit_total": None,
        },
    )
    assert code_campaign.status_code == 200

    created_code = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns/{code_campaign.json()['id']}/codes",
        headers=context["owner_headers"],
        json={"code": "WELCOME20", "status": "ACTIVE", "redemption_limit_per_code": None},
    )
    assert created_code.status_code == 200

    voucher_campaign = client.post(
        f"/v1/tenants/{context['tenant_id']}/promotion-campaigns",
        headers=context["owner_headers"],
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
    assert voucher_campaign.status_code == 200

    customer_profile = client.post(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles",
        headers=context["owner_headers"],
        json={"full_name": "Acme Traders"},
    )
    assert customer_profile.status_code == 200
    customer_profile_id = customer_profile.json()["id"]

    issued_voucher = client.post(
        f"/v1/tenants/{context['tenant_id']}/customer-profiles/{customer_profile_id}/vouchers",
        headers=context["owner_headers"],
        json={"campaign_id": voucher_campaign.json()["id"]},
    )
    assert issued_voucher.status_code == 200

    preview = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/checkout-price-preview",
        headers=context["owner_headers"],
        json={
            "customer_profile_id": customer_profile_id,
            "customer_name": "Acme Traders",
            "promotion_code": "WELCOME20",
            "customer_voucher_id": issued_voucher.json()["id"],
            "lines": [{"product_id": context["tea_product_id"], "quantity": 1}],
        },
    )
    assert preview.status_code == 400
    assert preview.json()["detail"] == "Shared promotion codes and customer vouchers cannot be combined"
