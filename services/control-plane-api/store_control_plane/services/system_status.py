from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..schemas import OperationsWorkerStatusResponse, SystemComponentStatusResponse, SystemHealthResponse


async def build_system_health(*, settings: Settings, session: AsyncSession) -> SystemHealthResponse:
    database_status = SystemComponentStatusResponse(status="ok", detail=None)
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised via integration behavior
        database_status = SystemComponentStatusResponse(status="error", detail=str(exc))

    overall_status = "ok" if database_status.status == "ok" else "degraded"
    return SystemHealthResponse(
        status=overall_status,
        environment=settings.deployment_environment,
        public_base_url=settings.public_base_url,
        release_version=settings.release_version,
        database=database_status,
        operations_worker=OperationsWorkerStatusResponse(
            configured=True,
            poll_seconds=settings.operations_worker_poll_seconds,
            batch_size=settings.operations_worker_batch_size,
            lease_seconds=settings.operations_worker_lease_seconds,
        ),
    )
