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


def _bootstrap_owner_context(client: TestClient) -> dict[str, str]:
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}

    tenant = client.post(
        "/v1/platform/tenants",
        headers=admin_headers,
        json={"name": "Acme Retail", "slug": "acme-retail-spokes"},
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


def test_branch_device_runtime_profiles_are_explicit() -> None:
    database_url = sqlite_test_database_url("spoke-runtime-profiles")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_owner_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    branch_hub = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
        json={
            "device_name": "Branch Hub",
            "device_code": "BLR-HUB-01",
            "session_surface": "store_desktop",
            "is_branch_hub": True,
        },
    )
    assert branch_hub.status_code == 200
    assert branch_hub.json()["runtime_profile"] == "branch_hub"

    spoke = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 2",
            "device_code": "BLR-POS-02",
            "session_surface": "store_desktop",
        },
    )
    assert spoke.status_code == 200
    assert spoke.json()["runtime_profile"] == "desktop_spoke"

    devices = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
    )
    assert devices.status_code == 200
    assert [record["runtime_profile"] for record in devices.json()["records"]] == [
        "branch_hub",
        "desktop_spoke",
    ]


def test_branch_hub_can_issue_spoke_runtime_activation_for_supported_profiles() -> None:
    database_url = sqlite_test_database_url("spoke-runtime-activation")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_owner_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    branch_hub = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
        json={
            "device_name": "Branch Hub",
            "device_code": "BLR-HUB-01",
            "session_surface": "store_desktop",
            "is_branch_hub": True,
        },
    )
    assert branch_hub.status_code == 200
    hub_payload = branch_hub.json()
    device_headers = {
        "x-store-device-id": hub_payload["id"],
        "x-store-device-secret": hub_payload["sync_access_secret"],
    }

    activation = client.post(
        "/v1/sync/spokes/activate",
        headers=device_headers,
        json={"runtime_profile": "desktop_spoke", "pairing_mode": "qr"},
    )
    assert activation.status_code == 200
    assert activation.json()["runtime_profile"] == "desktop_spoke"
    assert activation.json()["pairing_mode"] == "qr"
    assert activation.json()["hub_device_id"] == hub_payload["id"]
    assert activation.json()["activation_code"]

    unsupported = client.post(
        "/v1/sync/spokes/activate",
        headers=device_headers,
        json={"runtime_profile": "delivery_rider", "pairing_mode": "qr"},
    )
    assert unsupported.status_code == 400
    assert unsupported.json()["detail"] == "Unsupported spoke runtime profile"


def test_non_hub_devices_cannot_issue_spoke_runtime_activation() -> None:
    database_url = sqlite_test_database_url("spoke-runtime-non-hub")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )

    context = _bootstrap_owner_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    spoke = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 2",
            "device_code": "BLR-POS-02",
            "session_surface": "store_desktop",
        },
    )
    assert spoke.status_code == 200
    spoke_payload = spoke.json()

    forbidden = client.post(
        "/v1/sync/spokes/activate",
        headers={
            "x-store-device-id": spoke_payload["id"],
            "x-store-device-secret": "not-a-hub-secret",
        },
        json={"runtime_profile": "desktop_spoke", "pairing_mode": "qr"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "Device is not a branch hub"
