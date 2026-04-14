from __future__ import annotations

from pydantic import BaseModel


class TenantCreateRequest(BaseModel):
    name: str
    slug: str


class TenantCreatedResponse(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    onboarding_status: str


class PlatformTenantRecord(BaseModel):
    tenant_id: str
    name: str
    slug: str
    status: str
    onboarding_status: str


class PlatformTenantListResponse(BaseModel):
    records: list[PlatformTenantRecord]


class OwnerInviteCreateRequest(BaseModel):
    email: str
    full_name: str


class OwnerInviteResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    status: str
