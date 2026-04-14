from fastapi.testclient import TestClient

from store_api.main import create_app


def test_staff_assignment_device_registration_and_sync_routes():
    client = TestClient(create_app())

    tenant = client.post(
        "/v1/platform/tenants",
        headers={"x-actor-role": "platform_super_admin"},
        json={"name": "Acme Retail"},
    ).json()

    branch = client.post(
        f"/v1/tenants/{tenant['id']}/branches",
        headers={"x-actor-role": "tenant_owner"},
        json={"name": "Bengaluru Flagship", "gstin": "29ABCDE1234F1Z5"},
    ).json()

    assignment = client.post(
        f"/v1/tenants/{tenant['id']}/staff-assignments",
        headers={"x-actor-role": "tenant_owner"},
        json={
            "branch_id": branch["id"],
            "staff_name": "Cash Counter One",
            "role": "cashier",
        },
    ).json()

    assert assignment["role"] == "cashier"

    device = client.post(
        f"/v1/tenants/{tenant['id']}/branches/{branch['id']}/devices",
        headers={"x-actor-role": "store_manager"},
        json={
            "device_name": "Counter Desktop 1",
            "session_surface": "store_desktop",
        },
    ).json()

    assert device["session_surface"] == "store_desktop"

    accepted = client.post(
        "/v1/sync/push",
        headers={"x-actor-role": "store_manager"},
        json={"record_id": "sale-1", "client_version": 1, "server_version": 1},
    ).json()

    conflict = client.post(
        "/v1/sync/push",
        headers={"x-actor-role": "store_manager"},
        json={"record_id": "sale-1", "client_version": 1, "server_version": 2},
    ).json()

    pulled = client.get("/v1/sync/pull").json()
    heartbeat = client.get("/v1/sync/heartbeat").json()

    assert accepted["accepted"] is True
    assert conflict["conflict"] is True
    assert pulled["cursor"] >= 1
    assert heartbeat["status"] in {"current", "reconnecting", "stale"}
