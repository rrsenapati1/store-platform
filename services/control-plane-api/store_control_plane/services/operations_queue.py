from __future__ import annotations

from datetime import datetime

from ..repositories import OperationsRepository


def serialize_operations_job(job) -> dict[str, object]:
    return {
        "id": job.id,
        "tenant_id": job.tenant_id,
        "branch_id": job.branch_id,
        "created_by_user_id": job.created_by_user_id,
        "job_type": job.job_type,
        "status": job.status,
        "queue_key": job.queue_key,
        "payload": job.payload,
        "result_payload": job.result_payload,
        "attempt_count": job.attempt_count,
        "max_attempts": job.max_attempts,
        "run_after": job.run_after,
        "leased_until": job.leased_until,
        "lease_token": job.lease_token,
        "last_error": job.last_error,
        "dead_lettered_at": job.dead_lettered_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


class OperationsQueueService:
    def __init__(self, session):
        self._session = session
        self._repo = OperationsRepository(session)

    async def enqueue_branch_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        created_by_user_id: str | None,
        job_type: str,
        queue_key: str,
        payload: dict[str, object],
        max_attempts: int = 3,
    ) -> dict[str, object]:
        active_job = await self._repo.get_active_job_by_queue_key(queue_key=queue_key)
        if active_job is not None:
            return serialize_operations_job(active_job)
        job = await self._repo.create_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            created_by_user_id=created_by_user_id,
            job_type=job_type,
            queue_key=queue_key,
            payload=payload,
            max_attempts=max_attempts,
        )
        return serialize_operations_job(job)

    async def list_branch_jobs(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, object]:
        jobs = await self._repo.list_branch_jobs(
            tenant_id=tenant_id,
            branch_id=branch_id,
            status=status,
            limit=limit,
        )
        return {
            "branch_id": branch_id,
            "records": [serialize_operations_job(job) for job in jobs],
        }

    async def retry_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        job_id: str,
        now: datetime,
    ) -> dict[str, object] | None:
        job = await self._repo.retry_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            job_id=job_id,
            now=now,
        )
        if job is None:
            return None
        await self._session.commit()
        return serialize_operations_job(job)
