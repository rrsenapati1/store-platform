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


def _seed_owner_branch(client: TestClient) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-compliance-profile"},
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

    return {
        "tenant_id": tenant_id,
        "branch_id": branch.json()["id"],
        "owner_access_token": owner_session["access_token"],
    }


def test_owner_can_save_branch_irp_profile_without_reading_back_password() -> None:
    database_url = sqlite_test_database_url("compliance-provider-profile")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
            compliance_secret_key="4YwWqS6E2m2Gf2m74tNw-KH6nB5c1ETb8T-WcC1wh6g=",
            compliance_irp_mode="stub",
        )
    )
    context = _seed_owner_branch(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    profile = client.put(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/provider-profile",
        headers=owner_headers,
        json={
            "provider_name": "iris_direct",
            "api_username": "acme-irp-user",
            "api_password": "super-secret",
        },
    )
    assert profile.status_code == 200
    assert profile.json() == {
        "provider_name": "iris_direct",
        "api_username": "acme-irp-user",
        "has_password": True,
        "status": "CONFIGURED",
        "last_error_message": None,
    }

    loaded = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/provider-profile",
        headers=owner_headers,
    )
    assert loaded.status_code == 200
    assert loaded.json() == {
        "provider_name": "iris_direct",
        "api_username": "acme-irp-user",
        "has_password": True,
        "status": "CONFIGURED",
        "last_error_message": None,
    }

