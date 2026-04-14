from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.repositories.sync_runtime import SyncRuntimeRepository
from store_control_plane.services.operations_queue import OperationsQueueService
from store_control_plane.services.operations_worker import OperationsWorkerService
from store_control_plane.utils import utc_now
from test_compliance_async_jobs import _exchange, _seed_sale_context


class _FakeObjectStorageClient:
    def __init__(self, *, metadata_key: str, metadata_payload: dict[str, object]) -> None:
        self._metadata_key = metadata_key
        self._metadata_payload = metadata_payload

    def list_keys(self, *, bucket: str, prefix: str, limit: int = 100) -> list[str]:
        return [self._metadata_key]

    def read_text(self, *, bucket: str, key: str) -> str:
        assert key == self._metadata_key
        return json.dumps(self._metadata_payload)


async def _seed_observability_state(client: TestClient, *, tenant_id: str, branch_id: str) -> None:
    async with client.app.state.session_factory() as session:
        queue_service = OperationsQueueService(session)
        await queue_service.enqueue_branch_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            created_by_user_id=None,
            job_type="UNKNOWN_JOB",
            queue_key=f"observability-unknown:{tenant_id}:{branch_id}",
            payload={"reason": "exercise dead letter summary"},
            max_attempts=1,
        )
        worker_service = OperationsWorkerService(session, settings=client.app.state.settings)
        processed = await worker_service.process_due_jobs(limit=10, now=utc_now())
        assert processed["dead_lettered"] == 1

        now = utc_now()
        sync_repo = SyncRuntimeRepository(session)
        await sync_repo.upsert_hub_sync_status(
            tenant_id=tenant_id,
            branch_id=branch_id,
            hub_device_id="hub-device-1",
            source_device_id="HUB-001",
            updates={
                "runtime_state": "DEGRADED",
                "connected_spoke_count": 2,
                "local_outbox_depth": 3,
                "pending_mutation_count": 3,
                "last_heartbeat_at": now,
                "last_local_spoke_sync_at": now,
            },
        )
        await sync_repo.create_sync_conflict(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id="hub-device-1",
            source_idempotency_key="offline-sale-replay-1",
            conflict_index=0,
            request_hash="hash-1",
            table_name="offline_sales",
            record_id="continuity-sale-1",
            reason="STOCK_DIVERGENCE",
            message="Cloud stock no longer matches offline replay",
            client_version=1,
            server_version=4,
            retry_strategy="MANUAL_REVIEW",
        )
        await session.commit()


def test_platform_observability_summary_reports_jobs_runtime_and_backup_posture(monkeypatch) -> None:
    database_url = sqlite_test_database_url("platform-observability-summary")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
            deployment_environment="staging",
            release_version="2026.04.15-observability",
            object_storage_bucket="store-control-plane-artifacts",
            object_storage_prefix="control-plane/staging",
        )
    )
    context = _seed_sale_context(client)
    admin_session = _exchange(client, subject="platform-admin-1", email="admin@store.local", name="Platform Admin")
    admin_headers = {"authorization": f"Bearer {admin_session['access_token']}"}
    asyncio.run(_seed_observability_state(client, tenant_id=context["tenant_id"], branch_id=context["branch_id"]))

    metadata_key = "control-plane/staging/postgres-backups/20260415T020000Z/metadata.json"
    fake_storage = _FakeObjectStorageClient(
        metadata_key=metadata_key,
        metadata_payload={
            "created_at": utc_now().isoformat(),
            "release_version": "2026.04.15-observability",
            "environment": "staging",
        },
    )
    monkeypatch.setattr("store_control_plane.services.platform_observability.build_object_storage_client", lambda settings: fake_storage)

    response = client.get("/v1/platform/observability/summary", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "staging"
    assert payload["release_version"] == "2026.04.15-observability"
    assert payload["operations"]["dead_letter_count"] == 1
    assert payload["operations"]["recent_failure_records"][0]["job_type"] == "UNKNOWN_JOB"
    assert payload["runtime"]["tracked_branch_count"] == 1
    assert payload["runtime"]["degraded_branch_count"] == 1
    assert payload["runtime"]["open_conflict_count"] == 1
    assert payload["runtime"]["branches"][0]["runtime_state"] == "DEGRADED"
    assert payload["backup"]["status"] == "ok"
    assert payload["backup"]["metadata_key"] == metadata_key
    assert payload["backup"]["release_version"] == "2026.04.15-observability"
