from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .system import SystemHealthResponse


class PlatformObservabilityJobRecord(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    job_type: str
    status: str
    attempt_count: int
    max_attempts: int
    last_error: str | None = None
    dead_lettered_at: datetime | None = None
    updated_at: datetime


class PlatformObservabilityOperationsResponse(BaseModel):
    queued_count: int
    running_count: int
    retryable_count: int
    dead_letter_count: int
    recent_failure_records: list[PlatformObservabilityJobRecord]


class PlatformObservabilityRuntimeBranchRecord(BaseModel):
    tenant_id: str
    branch_id: str
    hub_device_id: str
    runtime_state: str
    connected_spoke_count: int
    local_outbox_depth: int
    open_conflict_count: int
    last_heartbeat_at: datetime | None = None
    last_local_spoke_sync_at: datetime | None = None


class PlatformObservabilityRuntimeResponse(BaseModel):
    tracked_branch_count: int
    degraded_branch_count: int
    connected_spoke_count: int
    open_conflict_count: int
    max_local_outbox_depth: int
    branches: list[PlatformObservabilityRuntimeBranchRecord]


class PlatformObservabilityBackupResponse(BaseModel):
    configured: bool
    status: str
    last_successful_backup_at: datetime | None = None
    metadata_key: str | None = None
    release_version: str | None = None
    age_hours: float | None = None
    detail: str | None = None


class PlatformObservabilitySummaryResponse(BaseModel):
    environment: str
    release_version: str
    system_health: SystemHealthResponse
    operations: PlatformObservabilityOperationsResponse
    runtime: PlatformObservabilityRuntimeResponse
    backup: PlatformObservabilityBackupResponse
