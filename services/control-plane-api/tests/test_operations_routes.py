import asyncio

from fastapi.testclient import TestClient

from conftest import sqlite_test_database_url
from store_control_plane.main import create_app
from store_control_plane.services.operations_queue import OperationsQueueService
from store_control_plane.services.operations_worker import OperationsWorkerService
from store_control_plane.utils import utc_now
from test_compliance_async_jobs import _seed_sale_context


async def _enqueue_unknown_job(client: TestClient, *, tenant_id: str, branch_id: str) -> dict[str, object]:
    async with client.app.state.session_factory() as session:
        service = OperationsQueueService(session)
        job = await service.enqueue_branch_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            created_by_user_id=None,
            job_type="UNKNOWN_JOB",
            queue_key=f"unknown-job:{tenant_id}:{branch_id}",
            payload={"reason": "exercise retry route"},
            max_attempts=1,
        )
        await session.commit()
        return job


async def _run_worker_once(client: TestClient) -> dict[str, int]:
    async with client.app.state.session_factory() as session:
        worker_service = OperationsWorkerService(session)
        return await worker_service.process_due_jobs(limit=10, now=utc_now())


def test_operations_route_lists_branch_jobs() -> None:
    database_url = sqlite_test_database_url("operations-routes-list")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )
    context = _seed_sale_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    export_job = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/compliance/gst-exports",
        headers=owner_headers,
        json={"sale_id": context["sale_id"]},
    )
    assert export_job.status_code == 200

    operations_jobs = client.get(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/operations/jobs",
        headers=owner_headers,
    )
    assert operations_jobs.status_code == 200
    assert operations_jobs.json()["records"][0]["job_type"] == "GST_EXPORT_PREPARE"
    assert operations_jobs.json()["records"][0]["status"] == "QUEUED"


def test_operations_route_retries_dead_lettered_job() -> None:
    database_url = sqlite_test_database_url("operations-routes-retry")
    client = TestClient(
        create_app(
            database_url=database_url,
            bootstrap_database=True,
            korsenex_idp_mode="stub",
            platform_admin_emails=["admin@store.local"],
        )
    )
    context = _seed_sale_context(client)
    owner_headers = {"authorization": f"Bearer {context['owner_access_token']}"}

    job = asyncio.run(_enqueue_unknown_job(client, tenant_id=context["tenant_id"], branch_id=context["branch_id"]))
    processed = asyncio.run(_run_worker_once(client))
    assert processed["dead_lettered"] == 1

    retried = client.post(
        f"/v1/tenants/{context['tenant_id']}/branches/{context['branch_id']}/operations/jobs/{job['id']}/retry",
        headers=owner_headers,
    )
    assert retried.status_code == 200
    assert retried.json()["status"] == "QUEUED"
    assert retried.json()["attempt_count"] == 0
    assert retried.json()["last_error"] is None
