from __future__ import annotations

from pydantic import BaseModel


class TenantMembershipCreateRequest(BaseModel):
    email: str
    full_name: str
    role_name: str


class BranchMembershipCreateRequest(BaseModel):
    email: str
    full_name: str
    role_name: str


class MembershipResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str | None = None
    email: str
    full_name: str
    role_name: str
    status: str
