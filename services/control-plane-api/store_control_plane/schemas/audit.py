from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditRecord(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: str
    tenant_id: str | None
    branch_id: str | None
    created_at: datetime
    payload: dict


class AuditListResponse(BaseModel):
    records: list[AuditRecord]
