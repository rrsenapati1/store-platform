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
