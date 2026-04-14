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
        json={"name": "Acme Retail", "slug": "acme-retail-sync-runtime"},
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


def test_branch_hub_sync_transport_and_monitoring_routes() -> None:
    database_url = sqlite_test_database_url("sync-runtime")
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

    device = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
        json={
            "device_name": "Branch Hub",
            "device_code": "BLR-HUB-01",
            "session_surface": "store_desktop",
            "is_branch_hub": True,
        },
    )
    assert device.status_code == 200
    device_payload = device.json()
    assert device_payload["is_branch_hub"] is True
    assert device_payload["sync_access_secret"]

    device_headers = {
        "x-store-device-id": device_payload["id"],
        "x-store-device-secret": device_payload["sync_access_secret"],
    }

    heartbeat = client.get(
        "/v1/sync/heartbeat",
        headers=device_headers,
        params={
            "connected_spoke_count": 4,
            "last_local_spoke_sync_at": "2026-04-14T10:00:00",
            "oldest_unsynced_mutation_age_seconds": 180,
            "local_outbox_depth": 3,
            "runtime_state": "DEGRADED",
        },
    )
    assert heartbeat.status_code == 200
    assert heartbeat.json()["status"] == "current"
    assert heartbeat.json()["runtime_state"] == "DEGRADED"
    assert heartbeat.json()["connected_spoke_count"] == 4
    assert heartbeat.json()["local_outbox_depth"] == 3

    accepted_push = client.post(
        "/v1/sync/push",
        headers=device_headers,
        json={
            "idempotency_key": "push-1",
            "mutations": [
                {
                    "table_name": "sales",
                    "record_id": "sale-1",
                    "operation": "UPSERT",
                    "payload": {"grand_total": "102.50", "status": "PAID"},
                    "client_version": 1,
                    "expected_server_version": 0,
                }
            ],
        },
    )
    assert accepted_push.status_code == 200
    assert accepted_push.json()["duplicate"] is False
    assert accepted_push.json()["accepted_mutations"] == 1
    assert accepted_push.json()["conflict_count"] == 0
    assert accepted_push.json()["server_cursor"] == 1

    duplicate_push = client.post(
        "/v1/sync/push",
        headers=device_headers,
        json={
            "idempotency_key": "push-1",
            "mutations": [
                {
                    "table_name": "sales",
                    "record_id": "sale-1",
                    "operation": "UPSERT",
                    "payload": {"grand_total": "102.50", "status": "PAID"},
                    "client_version": 1,
                    "expected_server_version": 0,
                }
            ],
        },
    )
    assert duplicate_push.status_code == 200
    assert duplicate_push.json()["duplicate"] is True
    assert duplicate_push.json()["accepted_mutations"] == 0
    assert duplicate_push.json()["server_cursor"] == 1

    conflict_push = client.post(
        "/v1/sync/push",
        headers=device_headers,
        json={
            "idempotency_key": "push-2",
            "mutations": [
                {
                    "table_name": "sales",
                    "record_id": "sale-1",
                    "operation": "UPSERT",
                    "payload": {"grand_total": "110.00", "status": "PAID"},
                    "client_version": 2,
                    "expected_server_version": 0,
                }
            ],
        },
    )
    assert conflict_push.status_code == 200
    assert conflict_push.json()["duplicate"] is False
    assert conflict_push.json()["accepted_mutations"] == 0
    assert conflict_push.json()["conflict_count"] == 1
    assert conflict_push.json()["conflicts"][0]["table_name"] == "sales"
    assert conflict_push.json()["conflicts"][0]["record_id"] == "sale-1"
    assert conflict_push.json()["conflicts"][0]["reason"] == "VERSION_MISMATCH"
    assert conflict_push.json()["conflicts"][0]["retry_strategy"] == "PULL_LATEST_THEN_RETRY"

    pulled = client.get(
        "/v1/sync/pull",
        headers=device_headers,
        params={"cursor": 0, "limit": 50},
    )
    assert pulled.status_code == 200
    assert pulled.json()["cursor"] == 1
    assert pulled.json()["records"][0]["table_name"] == "sales"
    assert pulled.json()["records"][0]["record_id"] == "sale-1"
    assert pulled.json()["records"][0]["operation"] == "UPSERT"
    assert pulled.json()["records"][0]["server_version"] == 1

    sync_status = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/runtime/sync-status",
        headers=owner_headers,
    )
    assert sync_status.status_code == 200
    assert sync_status.json()["hub_device_id"] == device_payload["id"]
    assert sync_status.json()["branch_cursor"] == 1
    assert sync_status.json()["last_pull_cursor"] == 1
    assert sync_status.json()["open_conflict_count"] == 1
    assert sync_status.json()["connected_spoke_count"] == 4
    assert sync_status.json()["local_outbox_depth"] == 3
    assert sync_status.json()["pending_mutation_count"] == 3
    assert sync_status.json()["runtime_state"] == "DEGRADED"

    sync_conflicts = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/runtime/sync-conflicts",
        headers=owner_headers,
    )
    assert sync_conflicts.status_code == 200
    assert len(sync_conflicts.json()["records"]) == 1
    assert sync_conflicts.json()["records"][0]["record_id"] == "sale-1"

    sync_envelopes = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/runtime/sync-envelopes",
        headers=owner_headers,
    )
    assert sync_envelopes.status_code == 200
    assert len(sync_envelopes.json()["records"]) >= 4
    assert any(record["entity_type"] == "sync_push" for record in sync_envelopes.json()["records"])
    assert any(record["entity_type"] == "sync_pull" for record in sync_envelopes.json()["records"])
    assert any(record["entity_type"] == "sync_heartbeat" for record in sync_envelopes.json()["records"])


def test_non_hub_device_cannot_use_cloud_sync_runtime() -> None:
    database_url = sqlite_test_database_url("sync-runtime-non-hub")
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

    device = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/devices",
        headers=owner_headers,
        json={
            "device_name": "Counter Desktop 1",
            "device_code": "BLR-POS-01",
            "session_surface": "store_desktop",
        },
    )
    assert device.status_code == 200
    assert device.json()["is_branch_hub"] is False
    assert device.json()["sync_access_secret"] is None

    sync_attempt = client.get(
        "/v1/sync/heartbeat",
        headers={
            "x-store-device-id": device.json()["id"],
            "x-store-device-secret": "invalid-secret",
        },
    )
    assert sync_attempt.status_code == 403
    assert sync_attempt.json()["detail"] == "Device is not a branch hub"
