from fastapi.testclient import TestClient

from store_control_plane.main import create_app
from conftest import sqlite_test_database_url


def _stub_token(*, subject: str, email: str, name: str) -> str:
    return f"stub:sub={subject};email={email};name={name}"


def test_oidc_exchange_creates_platform_session_and_actor_context():
    database_url = sqlite_test_database_url("control-plane")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    exchange = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject="platform-admin-1", email="admin@store.local", name="Platform Admin")},
    )

    assert exchange.status_code == 200
    assert exchange.json()["token_type"] == "Bearer"

    me = client.get(
        "/v1/auth/me",
        headers={"authorization": f"Bearer {exchange.json()['access_token']}"},
    )

    assert me.status_code == 200
    assert me.json()["email"] == "admin@store.local"
    assert me.json()["full_name"] == "Platform Admin"
    assert me.json()["is_platform_admin"] is True
    assert me.json()["tenant_memberships"] == []
    assert me.json()["branch_memberships"] == []


def test_runtime_actor_context_rejects_suspended_tenant_access():
    database_url = sqlite_test_database_url("control-plane-runtime-suspended")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    admin_exchange = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject="platform-admin-1", email="admin@store.local", name="Platform Admin")},
    )
    assert admin_exchange.status_code == 200
    admin_headers = {"authorization": f"Bearer {admin_exchange.json()['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-auth-suspended"},
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )
    assert owner_invite.status_code == 200

    owner_exchange = client.post(
        "/v1/auth/oidc/exchange",
        json={"token": _stub_token(subject="owner-1", email="owner@acme.local", name="Acme Owner")},
    )
    assert owner_exchange.status_code == 200
    owner_headers = {"authorization": f"Bearer {owner_exchange.json()['access_token']}"}

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )
    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    staff_profile = client.post(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
        json={
            "email": "cashier@acme.local",
            "full_name": "Counter Cashier",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Counter Cashier", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "store-runtime-suspended-auth-1234",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim.json()['claim_id']}/approve",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-AUTH-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert approval.status_code == 200
    device_id = approval.json()["device"]["id"]

    activation_issue = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/desktop-activation",
        headers=owner_headers,
    )
    assert activation_issue.status_code == 200

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": "store-runtime-suspended-auth-1234",
            "activation_code": activation_issue.json()["activation_code"],
        },
    )
    assert redeem.status_code == 200
    runtime_headers = {"authorization": f"Bearer {redeem.json()['access_token']}"}

    suspend = client.post(
        f"/v1/platform/tenants/{tenant_id}/billing/suspend",
        headers=admin_headers,
        json={"reason": "Billing hold"},
    )
    assert suspend.status_code == 200

    me = client.get("/v1/auth/me", headers=runtime_headers)

    assert me.status_code == 402
    assert me.json()["detail"] == "Commercial access is suspended for this tenant. Ask the owner to update billing."
