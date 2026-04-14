from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OperationsJobResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    created_by_user_id: str | None = None
    job_type: str
    status: str
    queue_key: str
    payload: dict[str, object]
    result_payload: dict[str, object] | None = None
    attempt_count: int
    max_attempts: int
    run_after: datetime
    leased_until: datetime | None = None
    lease_token: str | None = None
    last_error: str | None = None
    dead_lettered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OperationsJobListResponse(BaseModel):
    branch_id: str
    records: list[OperationsJobResponse]
