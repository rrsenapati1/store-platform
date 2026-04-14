from __future__ import annotations

from pydantic import BaseModel


class TenantSummaryResponse(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    onboarding_status: str


class BranchCreateRequest(BaseModel):
    name: str
    code: str
    gstin: str | None = None
    timezone: str = "Asia/Kolkata"


class BranchResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    gstin: str | None
    timezone: str
    status: str


class BranchRecord(BaseModel):
    branch_id: str
    tenant_id: str
    name: str
    code: str
    status: str


class BranchListResponse(BaseModel):
    records: list[BranchRecord]
