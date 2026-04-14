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


def test_mobile_store_spoke_can_redeem_activation_and_receive_runtime_session():
    database_url = sqlite_test_database_url("store-mobile-activation")
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
        json={"name": "Acme Retail", "slug": "acme-retail-mobile"},
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
        json={"name": "Bengaluru Flagship", "code": "blr-flagship-mobile", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "associate@acme.local",
            "full_name": "Floor Associate One",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "associate@acme.local", "full_name": "Floor Associate One", "role_name": "sales_associate"},
    )
    assert membership.status_code == 200

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "store-mobile-runtime-abcd1234efgh5678",
            "runtime_kind": "android_handheld",
            "hostname": "MOBILE-01",
            "operating_system": "android",
            "architecture": "arm64-v8a",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim.json()['claim_id']}/approve",
        headers=owner_headers,
        json={
            "device_name": "Handheld 1",
            "device_code": "BLR-MOB-01",
            "session_surface": "store_mobile",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert approval.status_code == 200
    device_id = approval.json()["device"]["id"]

    activation_issue = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/runtime-activation",
        headers=owner_headers,
    )
    assert activation_issue.status_code == 200
    activation_code = activation_issue.json()["activation_code"]

    response = client.post(
        "/v1/auth/runtime/activate",
        json={
            "installation_id": "store-mobile-runtime-abcd1234efgh5678",
            "activation_code": activation_code,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["device_id"] == device_id
    assert payload["staff_profile_id"] == staff_profile_id
    assert payload["runtime_profile"] == "mobile_store_spoke"
    assert payload["session_surface"] == "store_mobile"

    runtime_headers = {"authorization": f"Bearer {payload['access_token']}"}
    runtime_actor = client.get("/v1/auth/me", headers=runtime_headers)
    assert runtime_actor.status_code == 200
    assert runtime_actor.json()["email"] == "associate@acme.local"


def test_inventory_tablet_spoke_can_redeem_activation_and_receive_runtime_session():
    database_url = sqlite_test_database_url("inventory-tablet-activation")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_session = _exchange(client, subject="platform-admin-2", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail Tablet", "slug": "acme-retail-tablet"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner-tablet@acme.local", "full_name": "Tablet Owner"},
    )
    assert owner_invite.status_code == 200

    owner_session = _exchange(client, subject="owner-2", email="owner-tablet@acme.local", name="Tablet Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Tablet Branch", "code": "blr-tablet-branch", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "tablet-op@acme.local",
            "full_name": "Inventory Tablet Operator",
            "phone_number": "9999999999",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "tablet-op@acme.local", "full_name": "Inventory Tablet Operator", "role_name": "inventory_manager"},
    )
    assert membership.status_code == 200

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "inventory-tablet-runtime-abcd1234efgh5678",
            "runtime_kind": "android_tablet",
            "hostname": "TABLET-01",
            "operating_system": "android",
            "architecture": "arm64-v8a",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim.json()['claim_id']}/approve",
        headers=owner_headers,
        json={
            "device_name": "Inventory Tablet 1",
            "device_code": "BLR-TAB-01",
            "session_surface": "inventory_tablet",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert approval.status_code == 200
    device_id = approval.json()["device"]["id"]

    activation_issue = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/runtime-activation",
        headers=owner_headers,
    )
    assert activation_issue.status_code == 200
    activation_code = activation_issue.json()["activation_code"]

    response = client.post(
        "/v1/auth/runtime/activate",
        json={
            "installation_id": "inventory-tablet-runtime-abcd1234efgh5678",
            "activation_code": activation_code,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["device_id"] == device_id
    assert payload["staff_profile_id"] == staff_profile_id
    assert payload["runtime_profile"] == "inventory_tablet_spoke"
    assert payload["session_surface"] == "inventory_tablet"
