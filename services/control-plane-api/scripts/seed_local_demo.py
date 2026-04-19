from __future__ import annotations

import argparse
import asyncio

import httpx


DEFAULT_API_ORIGIN = "http://127.0.0.1:18000"
PLATFORM_TOKEN = "stub:sub=platform-1;email=admin@store.local;name=Platform Admin"
OWNER_TOKEN = "stub:sub=owner-1;email=owner@acme.local;name=Acme Owner"


async def exchange_session(client: httpx.AsyncClient, token: str) -> str:
    response = await client.post("/v1/auth/oidc/exchange", json={"token": token})
    response.raise_for_status()
    return response.json()["access_token"]


async def ensure_tenant(client: httpx.AsyncClient, platform_headers: dict[str, str]) -> str:
    tenants_response = await client.get("/v1/platform/tenants", headers=platform_headers)
    tenants_response.raise_for_status()
    tenant_record = next((record for record in tenants_response.json()["records"] if record["slug"] == "acme-retail"), None)
    if tenant_record is None:
        tenant_response = await client.post(
            "/v1/platform/tenants",
            json={"name": "Acme Retail", "slug": "acme-retail"},
            headers=platform_headers,
        )
        tenant_response.raise_for_status()
        tenant_record = tenant_response.json()
    return tenant_record.get("tenant_id") or tenant_record["id"]


async def ensure_owner_invite(client: httpx.AsyncClient, tenant_id: str, platform_headers: dict[str, str]) -> None:
    response = await client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
        headers=platform_headers,
    )
    if response.status_code not in {200, 409}:
        response.raise_for_status()


async def ensure_branch(client: httpx.AsyncClient, tenant_id: str, owner_headers: dict[str, str]) -> str:
    branches_response = await client.get(f"/v1/tenants/{tenant_id}/branches", headers=owner_headers)
    branches_response.raise_for_status()
    branch_record = next((record for record in branches_response.json()["records"] if record["code"] == "blr-flagship"), None)
    if branch_record is None:
        branch_response = await client.post(
            f"/v1/tenants/{tenant_id}/branches",
            json={
                "name": "Bengaluru Flagship",
                "code": "blr-flagship",
                "gstin": "29AAEPM0111C1Z3",
                "timezone": "Asia/Calcutta",
            },
            headers=owner_headers,
        )
        branch_response.raise_for_status()
        branch_record = branch_response.json()
    return branch_record.get("branch_id") or branch_record["id"]


async def ensure_staff_profile(client: httpx.AsyncClient, tenant_id: str, branch_id: str, owner_headers: dict[str, str]) -> str:
    staff_profiles_response = await client.get(f"/v1/tenants/{tenant_id}/staff-profiles", headers=owner_headers)
    staff_profiles_response.raise_for_status()
    staff_record = next((record for record in staff_profiles_response.json()["records"] if record["email"] == "cashier@acme.local"), None)
    if staff_record is None:
        staff_response = await client.post(
            f"/v1/tenants/{tenant_id}/staff-profiles",
            json={
                "email": "cashier@acme.local",
                "full_name": "Counter Cashier",
                "phone_number": "9999999999",
                "primary_branch_id": branch_id,
            },
            headers=owner_headers,
        )
        staff_response.raise_for_status()
        staff_record = staff_response.json()
    return staff_record["id"]


async def ensure_branch_membership(client: httpx.AsyncClient, tenant_id: str, branch_id: str, owner_headers: dict[str, str]) -> None:
    response = await client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        json={
            "email": "cashier@acme.local",
            "full_name": "Counter Cashier",
            "role_name": "cashier",
        },
        headers=owner_headers,
    )
    if response.status_code not in {200, 409}:
        response.raise_for_status()


async def ensure_device(
    client: httpx.AsyncClient,
    tenant_id: str,
    branch_id: str,
    staff_profile_id: str,
    owner_headers: dict[str, str],
) -> None:
    devices_response = await client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
    )
    devices_response.raise_for_status()
    if any(record["device_code"] == "counter-1" for record in devices_response.json()["records"]):
        return
    device_response = await client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "counter-1",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
            "is_branch_hub": False,
        },
        headers=owner_headers,
    )
    device_response.raise_for_status()


async def ensure_catalog_product(client: httpx.AsyncClient, tenant_id: str, owner_headers: dict[str, str]) -> str:
    products_response = await client.get(f"/v1/tenants/{tenant_id}/catalog/products", headers=owner_headers)
    products_response.raise_for_status()
    product_record = next((record for record in products_response.json()["records"] if record["sku_code"] == "TEA-250G"), None)
    if product_record is None:
        product_response = await client.post(
            f"/v1/tenants/{tenant_id}/catalog/products",
            json={
                "name": "Masala Tea 250g",
                "sku_code": "TEA-250G",
                "barcode": "8901234567890",
                "hsn_sac_code": "0902",
                "gst_rate": 5,
                "mrp": 199,
                "category_code": "tea",
                "tracking_mode": "STANDARD",
                "compliance_profile": "NONE",
                "selling_price": 179,
            },
            headers=owner_headers,
        )
        product_response.raise_for_status()
        product_record = product_response.json()
    return product_record.get("product_id") or product_record["id"]


async def ensure_branch_catalog_item(
    client: httpx.AsyncClient,
    tenant_id: str,
    branch_id: str,
    product_id: str,
    owner_headers: dict[str, str],
) -> None:
    branch_catalog_response = await client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        headers=owner_headers,
    )
    branch_catalog_response.raise_for_status()
    if any(record["product_id"] == product_id for record in branch_catalog_response.json()["records"]):
        return
    branch_catalog_create = await client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items",
        json={
            "product_id": product_id,
            "selling_price_override": 169,
            "availability_status": "ACTIVE",
            "reorder_point": 5,
            "target_stock": 20,
        },
        headers=owner_headers,
    )
    branch_catalog_create.raise_for_status()


async def seed_local_demo(api_origin: str) -> None:
    async with httpx.AsyncClient(base_url=api_origin, timeout=15.0) as client:
        platform_access_token = await exchange_session(client, PLATFORM_TOKEN)
        platform_headers = {"authorization": f"Bearer {platform_access_token}"}
        tenant_id = await ensure_tenant(client, platform_headers)
        await ensure_owner_invite(client, tenant_id, platform_headers)

        owner_access_token = await exchange_session(client, OWNER_TOKEN)
        owner_headers = {"authorization": f"Bearer {owner_access_token}"}

        branch_id = await ensure_branch(client, tenant_id, owner_headers)
        staff_profile_id = await ensure_staff_profile(client, tenant_id, branch_id, owner_headers)
        await ensure_branch_membership(client, tenant_id, branch_id, owner_headers)
        await ensure_device(client, tenant_id, branch_id, staff_profile_id, owner_headers)
        product_id = await ensure_catalog_product(client, tenant_id, owner_headers)
        await ensure_branch_catalog_item(client, tenant_id, branch_id, product_id, owner_headers)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a local Store demo tenant, branch, device, and product.")
    parser.add_argument("--api-origin", default=DEFAULT_API_ORIGIN, help="Control-plane API origin.")
    args = parser.parse_args()
    asyncio.run(seed_local_demo(args.api_origin))


if __name__ == "__main__":
    main()
