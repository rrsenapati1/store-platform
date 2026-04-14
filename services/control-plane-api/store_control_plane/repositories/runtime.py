from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PrintJob
from ..utils import new_id


class RuntimeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_print_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        reference_type: str,
        reference_id: str,
        job_type: str,
        copies: int,
        payload: dict[str, object],
    ) -> PrintJob:
        record = PrintJob(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            reference_type=reference_type,
            reference_id=reference_id,
            job_type=job_type,
            copies=copies,
            status="QUEUED",
            payload=payload,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_device_print_jobs(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        status: str | None = None,
    ) -> list[PrintJob]:
        statement = select(PrintJob).where(
            PrintJob.tenant_id == tenant_id,
            PrintJob.branch_id == branch_id,
            PrintJob.device_id == device_id,
        )
        if status is not None:
            statement = statement.where(PrintJob.status == status)
        statement = statement.order_by(PrintJob.created_at.asc(), PrintJob.id.asc())
        return list((await self._session.scalars(statement)).all())

    async def count_device_print_jobs(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        status: str,
    ) -> int:
        statement = select(func.count(PrintJob.id)).where(
            PrintJob.tenant_id == tenant_id,
            PrintJob.branch_id == branch_id,
            PrintJob.device_id == device_id,
            PrintJob.status == status,
        )
        count = await self._session.scalar(statement)
        return int(count or 0)

    async def get_print_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        print_job_id: str,
    ) -> PrintJob | None:
        statement = select(PrintJob).where(
            PrintJob.tenant_id == tenant_id,
            PrintJob.branch_id == branch_id,
            PrintJob.device_id == device_id,
            PrintJob.id == print_job_id,
        )
        return await self._session.scalar(statement)

    async def complete_print_job(
        self,
        *,
        print_job: PrintJob,
        status: str,
        failure_reason: str | None,
    ) -> PrintJob:
        print_job.status = status
        print_job.failure_reason = failure_reason
        await self._session.flush()
        return print_job
