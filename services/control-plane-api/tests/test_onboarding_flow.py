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


def test_platform_admin_and_owner_complete_milestone_one_onboarding():
    database_url = sqlite_test_database_url("onboarding-flow")
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
    assert tenant.json()["onboarding_status"] == "OWNER_INVITE_PENDING"

    tenant_list = client.get("/v1/platform/tenants", headers=admin_headers)
    assert tenant_list.status_code == 200
    assert tenant_list.json()["records"][0]["tenant_id"] == tenant_id

    owner_invite = client.post(
        f"/v1/platform/tenants/{tenant_id}/owner-invites",
        headers=admin_headers,
        json={"email": "owner@acme.local", "full_name": "Acme Owner"},
    )

    assert owner_invite.status_code == 200
    assert owner_invite.json()["status"] == "PENDING"

    owner_session = _exchange(client, subject="owner-1", email="owner@acme.local", name="Acme Owner")
    owner_headers = {"authorization": f"Bearer {owner_session['access_token']}"}

    me = client.get("/v1/auth/me", headers=owner_headers)
    assert me.status_code == 200
    assert me.json()["tenant_memberships"][0]["tenant_id"] == tenant_id
    assert me.json()["tenant_memberships"][0]["role_name"] == "tenant_owner"

    branch = client.post(
        f"/v1/tenants/{tenant_id}/branches",
        headers=owner_headers,
        json={"name": "Bengaluru Flagship", "code": "blr-flagship", "gstin": "29ABCDE1234F1Z5"},
    )

    assert branch.status_code == 200
    branch_id = branch.json()["id"]

    tenant_summary = client.get(f"/v1/tenants/{tenant_id}", headers=owner_headers)
    assert tenant_summary.status_code == 200
    assert tenant_summary.json()["onboarding_status"] == "BRANCH_READY"

    branches = client.get(f"/v1/tenants/{tenant_id}/branches", headers=owner_headers)
    assert branches.status_code == 200
    assert branches.json()["records"][0]["branch_id"] == branch_id

    tenant_membership = client.post(
        f"/v1/tenants/{tenant_id}/memberships",
        headers=owner_headers,
        json={"email": "ops@acme.local", "full_name": "Operations Lead", "role_name": "inventory_admin"},
    )

    assert tenant_membership.status_code == 200
    assert tenant_membership.json()["status"] == "PENDING"

    branch_membership = client.post(
        f"/v1/tenants/{tenant_id}/branches/{branch_id}/memberships",
        headers=owner_headers,
        json={"email": "cashier@acme.local", "full_name": "Cash Counter One", "role_name": "cashier"},
    )

    assert branch_membership.status_code == 200
    assert branch_membership.json()["status"] == "PENDING"

    staff_session = _exchange(client, subject="cashier-1", email="cashier@acme.local", name="Cash Counter One")
    staff_headers = {"authorization": f"Bearer {staff_session['access_token']}"}

    staff_me = client.get("/v1/auth/me", headers=staff_headers)
    assert staff_me.status_code == 200
    assert staff_me.json()["branch_memberships"][0]["branch_id"] == branch_id
    assert staff_me.json()["branch_memberships"][0]["role_name"] == "cashier"

    audit_events = client.get(f"/v1/tenants/{tenant_id}/audit-events", headers=owner_headers)
    assert audit_events.status_code == 200
    assert [record["action"] for record in audit_events.json()["records"][:4]] == [
        "branch_membership.assigned",
        "tenant_membership.assigned",
        "branch.created",
        "owner_invite.accepted",
    ]
