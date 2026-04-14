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


def test_packaged_runtime_claim_requires_owner_approval_before_device_binding():
    database_url = sqlite_test_database_url("device-claims")
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

    cashier_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    cashier_headers = {"authorization": f"Bearer {cashier_session['access_token']}"}

    first_claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=cashier_headers,
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert first_claim.status_code == 200
    assert first_claim.json()["status"] == "PENDING"
    assert first_claim.json()["bound_device_id"] is None
    claim_id = first_claim.json()["claim_id"]

    claim_list = client.get(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/device-claims",
        headers=owner_headers,
    )
    assert claim_list.status_code == 200
    assert claim_list.json()["records"][0]["claim_code"] == first_claim.json()["claim_code"]
    assert claim_list.json()["records"][0]["status"] == "PENDING"

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
    assert approval.json()["device"]["device_code"] == "BLR-POS-01"
    assert approval.json()["claim"]["status"] == "APPROVED"

    second_claim = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/device-claim",
        headers=cashier_headers,
        json={
            "installation_id": "store-runtime-abcd1234efgh5678",
            "runtime_kind": "packaged_desktop",
            "hostname": "COUNTER-01",
            "operating_system": "windows",
            "architecture": "x86_64",
            "app_version": "0.1.0",
        },
    )
    assert second_claim.status_code == 200
    assert second_claim.json()["status"] == "APPROVED"
    assert second_claim.json()["bound_device_id"] == approval.json()["device"]["id"]
    assert second_claim.json()["bound_device_code"] == "BLR-POS-01"
