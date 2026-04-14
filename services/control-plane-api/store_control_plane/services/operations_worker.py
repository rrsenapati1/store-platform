from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe

from ..repositories import OperationsRepository
from .gst_export_jobs import GstExportJobService
from .operations_queue import serialize_operations_job
from .supplier_report_jobs import SupplierReportJobService


class OperationsWorkerService:
    def __init__(self, session, *, lease_seconds: int = 60, retry_delay_seconds: int = 60):
        self._session = session
        self._repo = OperationsRepository(session)
        self._lease_seconds = lease_seconds
        self._retry_delay_seconds = retry_delay_seconds

    async def lease_due_jobs(self, *, limit: int, now: datetime) -> list[dict[str, object]]:
        jobs = await self._repo.lease_due_jobs(
            now=now,
            limit=limit,
            lease_seconds=self._lease_seconds,
            token_factory=lambda: token_urlsafe(24),
        )
        return [serialize_operations_job(job) for job in jobs]

    async def mark_job_succeeded(
        self,
        *,
        job_id: str,
        lease_token: str,
        result_payload: dict[str, object] | None = None,
    ) -> dict[str, object] | None:
        job = await self._repo.mark_job_succeeded(
            job_id=job_id,
            lease_token=lease_token,
            result_payload=result_payload,
        )
        return None if job is None else serialize_operations_job(job)

    async def process_due_jobs(self, *, limit: int, now: datetime) -> dict[str, int]:
        requeued_expired_leases = await self._repo.requeue_expired_leases(now=now)
        jobs = await self._repo.lease_due_jobs(
            now=now,
            limit=limit,
            lease_seconds=self._lease_seconds,
            token_factory=lambda: token_urlsafe(24),
        )
        await self._session.commit()

        completed = 0
        retried = 0
        dead_lettered = 0
        for job in jobs:
            try:
                result_payload = await self._dispatch_job(job)
                updated = await self._repo.mark_job_succeeded(
                    job_id=job.id,
                    lease_token=job.lease_token or "",
                    result_payload=result_payload,
                )
                await self._session.commit()
                if updated is not None:
                    completed += 1
            except Exception as error:
                await self._session.rollback()
                updated = await self._repo.mark_job_retryable(
                    job_id=job.id,
                    lease_token=job.lease_token or "",
                    error_message=str(error),
                    now=now,
                    retry_delay_seconds=self._retry_delay_seconds,
                )
                await self._session.commit()
                if updated is not None:
                    if updated.status == "DEAD_LETTER":
                        dead_lettered += 1
                    else:
                        retried += 1

        return {
            "leased": len(jobs),
            "completed": completed,
            "retried": retried,
            "dead_lettered": dead_lettered,
            "requeued_expired_leases": requeued_expired_leases,
        }

    async def run_maintenance_sweep(self, *, now: datetime, retention_hours: int) -> dict[str, int]:
        deleted_completed_jobs = await self._repo.delete_completed_jobs_before(
            cutoff=now - timedelta(hours=retention_hours),
        )
        await self._session.commit()
        return {"deleted_completed_jobs": deleted_completed_jobs}

    async def _dispatch_job(self, job) -> dict[str, object]:
        if job.job_type == "GST_EXPORT_PREPARE":
            handler = GstExportJobService(self._session)
            payload = job.payload or {}
            return await handler.handle_prepare(
                tenant_id=job.tenant_id,
                branch_id=job.branch_id,
                gst_export_job_id=str(payload["gst_export_job_id"]),
            )
        if job.job_type == "SUPPLIER_REPORT_REFRESH":
            handler = SupplierReportJobService(self._session)
            payload = job.payload or {}
            return await handler.handle_refresh(
                tenant_id=job.tenant_id,
                branch_id=job.branch_id,
                report_type=str(payload["report_type"]),
                report_date=None if payload.get("report_date") is None else str(payload["report_date"]),
            )
        raise ValueError(f"Unsupported operations job type: {job.job_type}")

    async def mark_job_retryable(
        self,
        *,
        job_id: str,
        lease_token: str,
        error_message: str,
        now: datetime,
    ) -> dict[str, object] | None:
        job = await self._repo.mark_job_retryable(
            job_id=job_id,
            lease_token=lease_token,
            error_message=error_message,
            now=now,
            retry_delay_seconds=self._retry_delay_seconds,
        )
        return None if job is None else serialize_operations_job(job)
