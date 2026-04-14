from __future__ import annotations

from pydantic import BaseModel


class OIDCExchangeRequest(BaseModel):
    token: str


class SessionTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: str


class RuntimeActivationRedeemRequest(BaseModel):
    installation_id: str
    activation_code: str


class RuntimeActivationRedeemResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: str
    device_id: str
    staff_profile_id: str
    runtime_profile: str
    session_surface: str


class SignOutResponse(BaseModel):
    status: str


class ActorTenantMembership(BaseModel):
    tenant_id: str
    role_name: str
    status: str


class ActorBranchMembership(BaseModel):
    tenant_id: str
    branch_id: str
    role_name: str
    status: str


class ActorResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    is_platform_admin: bool
    tenant_memberships: list[ActorTenantMembership]
    branch_memberships: list[ActorBranchMembership]
