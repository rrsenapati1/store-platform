from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import OperationsJob
from ..utils import new_id, utc_now


ACTIVE_JOB_STATUSES = ("QUEUED", "RUNNING", "RETRYABLE")


class OperationsRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_branch_jobs(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[OperationsJob]:
        statement = (
            select(OperationsJob)
            .where(
                OperationsJob.tenant_id == tenant_id,
                OperationsJob.branch_id == branch_id,
            )
            .order_by(OperationsJob.created_at.desc(), OperationsJob.id.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(OperationsJob.status == status)
        return list((await self._session.scalars(statement)).all())

    async def get_job(self, *, job_id: str) -> OperationsJob | None:
        return await self._session.get(OperationsJob, job_id)

    async def get_active_job_by_queue_key(self, *, queue_key: str) -> OperationsJob | None:
        statement = (
            select(OperationsJob)
            .where(
                OperationsJob.queue_key == queue_key,
                OperationsJob.status.in_(ACTIVE_JOB_STATUSES),
            )
            .order_by(OperationsJob.created_at.desc(), OperationsJob.id.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def create_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        created_by_user_id: str | None,
        job_type: str,
        queue_key: str,
        payload: dict[str, object],
        max_attempts: int,
        run_after: datetime | None = None,
    ) -> OperationsJob:
        job = OperationsJob(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            created_by_user_id=created_by_user_id,
            job_type=job_type,
            status="QUEUED",
            queue_key=queue_key,
            payload=dict(payload),
            result_payload=None,
            attempt_count=0,
            max_attempts=max_attempts,
            run_after=run_after or utc_now(),
            leased_until=None,
            lease_token=None,
            last_error=None,
            dead_lettered_at=None,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def lease_due_jobs(
        self,
        *,
        now: datetime,
        limit: int,
        lease_seconds: int,
        token_factory,
    ) -> list[OperationsJob]:
        statement = (
            select(OperationsJob)
            .where(
                OperationsJob.status.in_(("QUEUED", "RETRYABLE")),
                OperationsJob.run_after <= now,
                or_(OperationsJob.leased_until.is_(None), OperationsJob.leased_until < now),
            )
            .order_by(OperationsJob.run_after.asc(), OperationsJob.created_at.asc(), OperationsJob.id.asc())
            .limit(limit)
            .with_for_update()
        )
        jobs = list((await self._session.scalars(statement)).all())
        leased_until = now + timedelta(seconds=lease_seconds)
        for job in jobs:
            job.status = "RUNNING"
            job.leased_until = leased_until
            job.lease_token = token_factory()
            job.last_error = None
        await self._session.flush()
        return jobs

    async def mark_job_succeeded(
        self,
        *,
        job_id: str,
        lease_token: str,
        result_payload: dict[str, object] | None = None,
    ) -> OperationsJob | None:
        job = await self.get_job(job_id=job_id)
        if job is None or job.lease_token != lease_token:
            return None
        job.status = "SUCCEEDED"
        job.result_payload = None if result_payload is None else dict(result_payload)
        job.leased_until = None
        job.lease_token = None
        job.last_error = None
        await self._session.flush()
        return job

    async def mark_job_retryable(
        self,
        *,
        job_id: str,
        lease_token: str,
        error_message: str,
        now: datetime,
        retry_delay_seconds: int,
    ) -> OperationsJob | None:
        job = await self.get_job(job_id=job_id)
        if job is None or job.lease_token != lease_token:
            return None
        job.attempt_count += 1
        job.last_error = error_message
        job.leased_until = None
        job.lease_token = None
        if job.attempt_count >= job.max_attempts:
            job.status = "DEAD_LETTER"
            job.dead_lettered_at = now
            job.run_after = now
        else:
            job.status = "RETRYABLE"
            job.run_after = now + timedelta(seconds=retry_delay_seconds)
        await self._session.flush()
        return job

    async def requeue_expired_leases(self, *, now: datetime) -> int:
        statement = select(OperationsJob).where(
            OperationsJob.status == "RUNNING",
            OperationsJob.leased_until.is_not(None),
            OperationsJob.leased_until < now,
        )
        jobs = list((await self._session.scalars(statement)).all())
        for job in jobs:
            job.status = "QUEUED"
            job.leased_until = None
            job.lease_token = None
        await self._session.flush()
        return len(jobs)

    async def delete_completed_jobs_before(self, *, cutoff: datetime) -> int:
        statement = delete(OperationsJob).where(
            OperationsJob.status == "SUCCEEDED",
            OperationsJob.updated_at < cutoff,
        )
        result = await self._session.execute(statement)
        return int(result.rowcount or 0)

    async def retry_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        job_id: str,
        now: datetime,
    ) -> OperationsJob | None:
        job = await self.get_job(job_id=job_id)
        if job is None:
            return None
        if job.tenant_id != tenant_id or job.branch_id != branch_id:
            return None
        if job.status not in {"DEAD_LETTER", "RETRYABLE"}:
            return None
        job.status = "QUEUED"
        job.attempt_count = 0
        job.run_after = now
        job.leased_until = None
        job.lease_token = None
        job.last_error = None
        job.dead_lettered_at = None
        job.result_payload = None
        await self._session.flush()
        return job
