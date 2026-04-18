from __future__ import annotations

from pydantic import BaseModel


class SystemComponentStatusResponse(BaseModel):
    status: str
    detail: str | None = None


class OperationsWorkerStatusResponse(BaseModel):
    configured: bool
    poll_seconds: int
    batch_size: int
    lease_seconds: int


class SystemHealthResponse(BaseModel):
    status: str
    environment: str
    public_base_url: str
    release_version: str
    alembic_head: str
    database: SystemComponentStatusResponse
    operations_worker: OperationsWorkerStatusResponse


class AuthorityBoundaryResponse(BaseModel):
    control_plane_service: str
    legacy_service: str
    cutover_phase: str
    legacy_write_mode: str
    migrated_domains: list[str]
    legacy_remaining_domains: list[str]
    shutdown_criteria: list[str]
    shutdown_steps: list[str]


class SystemSecurityRateLimitsResponse(BaseModel):
    window_seconds: int
    auth_requests: int
    activation_requests: int
    webhook_requests: int


class SystemSecurityControlsResponse(BaseModel):
    secure_headers_enabled: bool
    secure_headers_hsts_enabled: bool
    secure_headers_csp: str
    rate_limits: SystemSecurityRateLimitsResponse


class SystemEnvironmentContractResponse(BaseModel):
    deployment_environment: str
    public_base_url: str
    release_version: str
    log_format: str
    sentry_configured: bool
    sentry_environment: str
    object_storage_configured: bool
    object_storage_bucket: str | None
    object_storage_prefix: str | None
    operations_worker: OperationsWorkerStatusResponse
    security_controls: SystemSecurityControlsResponse
