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


def test_owner_issues_store_desktop_activation_and_packaged_runtime_redeems_it_without_staff_oidc_login():
    database_url = sqlite_test_database_url("store-desktop-activation")
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
            "full_name": "Cash Counter One",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert membership.status_code == 200
    assert membership.json()["status"] == "PENDING"

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200
    claim_id = claim.json()["claim_id"]

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim_id}/approve",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
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
    activation_code = activation_issue.json()["activation_code"]
    assert activation_issue.json()["staff_profile_id"] == staff_profile_id

    redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "activation_code": activation_code,
        },
    )
    assert redeem.status_code == 200
    assert redeem.json()["access_token"]
    assert redeem.json()["device_id"] == device_id
    assert redeem.json()["staff_profile_id"] == staff_profile_id
    assert redeem.json()["local_auth_token"]
    assert redeem.json()["offline_valid_until"]
    assert redeem.json()["activation_version"] == 1

    runtime_headers = {"authorization": f"Bearer {redeem.json()['access_token']}"}
    runtime_actor = client.get("/v1/auth/me", headers=runtime_headers)
    assert runtime_actor.status_code == 200
    assert runtime_actor.json()["email"] == "cashier@acme.local"
    assert runtime_actor.json()["branch_memberships"][0]["branch_id"] == branch_id
    assert runtime_actor.json()["branch_memberships"][0]["role_name"] == "cashier"
    assert redeem.json()["expires_at"]

    refresh = client.post("/v1/auth/refresh", headers=runtime_headers)
    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != redeem.json()["access_token"]
    assert refresh.json()["expires_at"]

    old_runtime_actor = client.get("/v1/auth/me", headers=runtime_headers)
    assert old_runtime_actor.status_code == 401

    refreshed_headers = {"authorization": f"Bearer {refresh.json()['access_token']}"}
    refreshed_runtime_actor = client.get("/v1/auth/me", headers=refreshed_headers)
    assert refreshed_runtime_actor.status_code == 200

    sign_out = client.post("/v1/auth/sign-out", headers=refreshed_headers)
    assert sign_out.status_code == 200
    assert sign_out.json()["status"] == "signed_out"

    runtime_actor_after_sign_out = client.get("/v1/auth/me", headers=refreshed_headers)
    assert runtime_actor_after_sign_out.status_code == 401

    unlock = client.post(
        "/v1/auth/store-desktop/unlock",
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "local_auth_token": redeem.json()["local_auth_token"],
        },
    )
    assert unlock.status_code == 200
    assert unlock.json()["access_token"]
    assert unlock.json()["access_token"] != refresh.json()["access_token"]
    assert unlock.json()["device_id"] == device_id
    assert unlock.json()["staff_profile_id"] == staff_profile_id
    assert unlock.json()["activation_version"] == 1
    assert unlock.json()["offline_valid_until"]

    staff_directory = client.get(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
    )
    assert staff_directory.status_code == 200
    assert staff_directory.json()["records"][0]["user_id"] == runtime_actor.json()["user_id"]

    second_redeem = client.post(
        "/v1/auth/store-desktop/activate",
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "activation_code": activation_code,
        },
    )
    assert second_redeem.status_code == 401


def test_store_desktop_activation_rejects_staff_profiles_that_reuse_owner_web_identity():
    database_url = sqlite_test_database_url("store-desktop-activation-owner-conflict")
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
            "email": "owner@acme.local",
            "full_name": "Acme Owner",
            "phone_number": "9876543210",
            "primary_branch_id": branch_id,
        },
    )
    assert staff_profile.status_code == 200
    staff_profile_id = staff_profile.json()["id"]

    membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner", "role_name": "cashier"},
    )
    assert membership.status_code == 200

    claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=owner_headers,
        json={
            "installation_id": "store-runtime-ownerconflict1234",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert claim.status_code == 200
    claim_id = claim.json()["claim_id"]

    approval = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims/{claim_id}/approve",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-02",
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
            "installation_id": "store-runtime-ownerconflict1234",
            "activation_code": activation_issue.json()["activation_code"],
        },
    )
    assert redeem.status_code == 409
    assert redeem.json()["detail"] == "Staff profile email is already bound to an interactive user"
