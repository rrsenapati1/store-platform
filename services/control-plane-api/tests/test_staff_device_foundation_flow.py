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


def test_owner_bootstraps_staff_directory_and_branch_devices():
    database_url = sqlite_test_database_url("staff-devices")
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

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    staff_directory = client.get(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
    )
    assert staff_directory.status_code == 200
    assert staff_directory.json()["records"][0]["email"] == "cashier@acme.local"
    assert staff_directory.json()["records"][0]["role_names"] == ["cashier"]
    assert staff_directory.json()["records"][0]["branch_ids"] == [branch_id]

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    assert device.json()["session_surface"] == "store_desktop"

    devices = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
    )
    assert devices.status_code == 200
    assert devices.json()["records"][0]["device_code"] == "BLR-POS-01"
    assert devices.json()["records"][0]["assigned_staff_full_name"] == "Cash Counter One"

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    actor = client.get("/v1/auth/me", headers=cashier_headers)
    assert actor.status_code == 200
    assert actor.json()["branch_memberships"][0]["branch_id"] == branch_id

    refreshed_staff_directory = client.get(
        f"/v1/tenants/{tenant_id}/staff-profiles",
        headers=owner_headers,
    )
    assert refreshed_staff_directory.status_code == 200
    assert refreshed_staff_directory.json()["records"][0]["user_id"] == actor.json()["user_id"]


def test_cashier_session_lifecycle_is_governed_per_device() -> None:
    database_url = sqlite_test_database_url("cashier-session-lifecycle")
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
        json={"name": "Acme Retail", "slug": "acme-retail-cashier-session"},
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

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )
    assert branch_membership.status_code == 200

    device = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
            "assigned_staff_profile_id": staff_profile_id,
        },
    )
    assert device.status_code == 200
    device_id = device.json()["id"]

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    opened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 500.0,
            "opening_note": "Morning shift",
        },
    )
    assert opened.status_code == 200
    cashier_session_id = opened.json()["id"]
    assert opened.json()["status"] == "OPEN"
    assert opened.json()["opening_float_amount"] == 500.0

    duplicate_open = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 250.0,
            "opening_note": "Second open should be rejected",
        },
    )
    assert duplicate_open.status_code == 409

    closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/close",
        headers=cashier_headers,
        json={"closing_note": "Shift complete"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["closing_note"] == "Shift complete"

    reopened = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions",
        headers=cashier_headers,
        json={
            "device_registration_id": device_id,
            "staff_profile_id": staff_profile_id,
            "opening_float_amount": 450.0,
            "opening_note": "Evening shift",
        },
    )
    assert reopened.status_code == 200
    reopened_session_id = reopened.json()["id"]

    forced_closed = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/cashier-sessions/{reopened_session_id}/force-close",
        headers=owner_headers,
        json={"reason": "Terminal left signed in"},
    )
    assert forced_closed.status_code == 200
    assert forced_closed.json()["status"] == "FORCED_CLOSED"
    assert forced_closed.json()["force_close_reason"] == "Terminal left signed in"
