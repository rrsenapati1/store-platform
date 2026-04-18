from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..ops.postgres_backup import resolve_alembic_head
from ..schemas import (
    OperationsWorkerStatusResponse,
    SystemComponentStatusResponse,
    SystemEnvironmentContractResponse,
    SystemHealthResponse,
    SystemSecurityControlsResponse,
    SystemSecurityRateLimitsResponse,
)


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
        alembic_head=resolve_alembic_head(),
        database=database_status,
        operations_worker=OperationsWorkerStatusResponse(
            configured=True,
            poll_seconds=settings.operations_worker_poll_seconds,
            batch_size=settings.operations_worker_batch_size,
            lease_seconds=settings.operations_worker_lease_seconds,
        ),
    )


def build_system_environment_contract(*, settings: Settings) -> SystemEnvironmentContractResponse:
    return SystemEnvironmentContractResponse(
        deployment_environment=settings.deployment_environment,
        public_base_url=settings.public_base_url,
        release_version=settings.release_version,
        log_format=settings.log_format,
        sentry_configured=bool(settings.sentry_dsn),
        sentry_environment=settings.sentry_environment or settings.deployment_environment,
        object_storage_configured=bool(settings.object_storage_bucket),
        object_storage_bucket=settings.object_storage_bucket,
        object_storage_prefix=settings.object_storage_prefix,
        operations_worker=OperationsWorkerStatusResponse(
            configured=True,
            poll_seconds=settings.operations_worker_poll_seconds,
            batch_size=settings.operations_worker_batch_size,
            lease_seconds=settings.operations_worker_lease_seconds,
        ),
        security_controls=SystemSecurityControlsResponse(
            secure_headers_enabled=settings.secure_headers_enabled,
            secure_headers_hsts_enabled=settings.secure_headers_hsts_enabled,
            secure_headers_csp=settings.secure_headers_csp,
            rate_limits=SystemSecurityRateLimitsResponse(
                window_seconds=settings.rate_limit_window_seconds,
                auth_requests=settings.rate_limit_auth_requests,
                activation_requests=settings.rate_limit_activation_requests,
                webhook_requests=settings.rate_limit_webhook_requests,
            ),
        ),
    )
