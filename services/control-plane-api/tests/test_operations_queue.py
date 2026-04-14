import asyncio
from datetime import timedelta

from conftest import sqlite_test_database_url
from store_control_plane.db.session import bootstrap_database, create_session_factory
from store_control_plane.models import OperationsJob
from store_control_plane.services.operations_queue import OperationsQueueService
from store_control_plane.services.operations_worker import OperationsWorkerService
from store_control_plane.utils import utc_now


async def _exercise_queue_contract() -> None:
    database_url = sqlite_test_database_url("operations-queue")
    engine, session_factory = create_session_factory(database_url)
    try:
        await bootstrap_database(session_factory, engine=engine)

        async with session_factory() as session:
            queue_service = OperationsQueueService(session)
            first_job = await queue_service.enqueue_branch_job(
                tenant_id="tenant-1",
                branch_id="branch-1",
                created_by_user_id="user-1",
                job_type="SUPPLIER_REPORT_REFRESH",
                queue_key="supplier-report:tenant-1:branch-1:supplier-payables-report:none:none",
                payload={"report_type": "supplier-payables-report"},
                max_attempts=2,
            )
            second_job = await queue_service.enqueue_branch_job(
                tenant_id="tenant-1",
                branch_id="branch-1",
                created_by_user_id="user-1",
                job_type="SUPPLIER_REPORT_REFRESH",
                queue_key="supplier-report:tenant-1:branch-1:supplier-payables-report:none:none",
                payload={"report_type": "supplier-payables-report"},
                max_attempts=2,
            )
            assert first_job["id"] == second_job["id"]
            await session.commit()

        async with session_factory() as session:
            worker_service = OperationsWorkerService(session)
            leased = await worker_service.lease_due_jobs(limit=10, now=utc_now())
            assert len(leased) == 1
            assert leased[0]["status"] == "RUNNING"
            await worker_service.mark_job_retryable(
                job_id=leased[0]["id"],
                lease_token=leased[0]["lease_token"],
                error_message="temporary failure",
                now=utc_now(),
            )
            await session.commit()

        async with session_factory() as session:
            worker_service = OperationsWorkerService(session)
            leased = await worker_service.lease_due_jobs(limit=10, now=utc_now() + timedelta(minutes=5))
            assert len(leased) == 1
            retried = leased[0]
            assert retried["attempt_count"] == 1
            assert retried["status"] == "RUNNING"
            dead_lettered = await worker_service.mark_job_retryable(
                job_id=retried["id"],
                lease_token=retried["lease_token"],
                error_message="permanent failure",
                now=utc_now() + timedelta(minutes=5),
            )
            assert dead_lettered["status"] == "DEAD_LETTER"
            await session.commit()
    finally:
        await engine.dispose()


def test_operations_queue_dedupes_leases_retries_and_dead_letters() -> None:
    asyncio.run(_exercise_queue_contract())


async def _exercise_maintenance_sweep() -> None:
    database_url = sqlite_test_database_url("operations-maintenance")
    engine, session_factory = create_session_factory(database_url)
    try:
        await bootstrap_database(session_factory, engine=engine)

        async with session_factory() as session:
            queue_service = OperationsQueueService(session)
            job = await queue_service.enqueue_branch_job(
                tenant_id="tenant-1",
                branch_id="branch-1",
                created_by_user_id="user-1",
                job_type="GST_EXPORT_PREPARE",
                queue_key="gst-export:tenant-1:branch-1:sale-1",
                payload={"gst_export_job_id": "gst-export-1"},
            )
            await session.commit()

        async with session_factory() as session:
            worker_service = OperationsWorkerService(session)
            leased = await worker_service.lease_due_jobs(limit=10, now=utc_now())
            await worker_service.mark_job_succeeded(
                job_id=leased[0]["id"],
                lease_token=leased[0]["lease_token"],
                result_payload={"status": "IRN_PENDING"},
            )
            succeeded_job = await session.get(OperationsJob, job["id"])
            assert succeeded_job is not None
            succeeded_job.updated_at = utc_now() - timedelta(days=10)
            await session.commit()

        async with session_factory() as session:
            worker_service = OperationsWorkerService(session)
            swept = await worker_service.run_maintenance_sweep(now=utc_now(), retention_hours=24)
            assert swept["deleted_completed_jobs"] == 1
    finally:
        await engine.dispose()


def test_operations_worker_maintenance_sweep_deletes_old_succeeded_jobs() -> None:
    asyncio.run(_exercise_maintenance_sweep())
