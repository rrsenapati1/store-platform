from __future__ import annotations

from pydantic import BaseModel


class StaffProfileCreateRequest(BaseModel):
    email: str
    full_name: str
    phone_number: str | None = None
    primary_branch_id: str | None = None


class StaffProfileResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str | None = None
    email: str
    full_name: str
    phone_number: str | None = None
    primary_branch_id: str | None = None
    status: str


class StaffProfileRecord(BaseModel):
    id: str
    tenant_id: str
    user_id: str | None = None
    email: str
    full_name: str
    phone_number: str | None = None
    primary_branch_id: str | None = None
    status: str
    role_names: list[str]
    branch_ids: list[str]


class StaffProfileListResponse(BaseModel):
    records: list[StaffProfileRecord]


class DeviceRegistrationCreateRequest(BaseModel):
    device_name: str
    device_code: str
    session_surface: str
    assigned_staff_profile_id: str | None = None
    is_branch_hub: bool = False


class DeviceRegistrationResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    device_name: str
    device_code: str
    session_surface: str
    is_branch_hub: bool = False
    status: str
    assigned_staff_profile_id: str | None = None
    installation_id: str | None = None
    sync_access_secret: str | None = None


class DeviceRegistrationRecord(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    device_name: str
    device_code: str
    session_surface: str
    is_branch_hub: bool = False
    status: str
    assigned_staff_profile_id: str | None = None
    assigned_staff_full_name: str | None = None
    installation_id: str | None = None


class DeviceRegistrationListResponse(BaseModel):
    records: list[DeviceRegistrationRecord]


class RuntimeDeviceClaimResolveRequest(BaseModel):
    installation_id: str
    runtime_kind: str
    hostname: str | None = None
    operating_system: str | None = None
    architecture: str | None = None
    app_version: str | None = None


class RuntimeDeviceClaimResolveResponse(BaseModel):
    claim_id: str
    claim_code: str
    status: str
    bound_device_id: str | None = None
    bound_device_name: str | None = None
    bound_device_code: str | None = None


class RuntimeHubBootstrapRequest(BaseModel):
    installation_id: str


class RuntimeHubBootstrapResponse(BaseModel):
    device_id: str
    device_code: str
    installation_id: str
    sync_access_secret: str
    issued_at: str


class DeviceClaimRecord(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    installation_id: str
    claim_code: str
    runtime_kind: str
    hostname: str | None = None
    operating_system: str | None = None
    architecture: str | None = None
    app_version: str | None = None
    status: str
    approved_device_id: str | None = None
    approved_device_code: str | None = None
    created_at: str
    last_seen_at: str | None = None
    approved_at: str | None = None


class DeviceClaimListResponse(BaseModel):
    records: list[DeviceClaimRecord]


class DeviceClaimApproveRequest(BaseModel):
    device_name: str
    device_code: str
    session_surface: str
    assigned_staff_profile_id: str | None = None
    is_branch_hub: bool = False


class DeviceClaimApprovalResponse(BaseModel):
    claim: DeviceClaimRecord
    device: DeviceRegistrationResponse


class StoreDesktopActivationIssueResponse(BaseModel):
    device_id: str
    staff_profile_id: str
    activation_code: str
    status: str
    expires_at: str


class StoreDesktopActivationRedeemRequest(BaseModel):
    installation_id: str
    activation_code: str


class StoreDesktopActivationRedeemResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: str
    device_id: str
    staff_profile_id: str
    local_auth_token: str
    offline_valid_until: str
    activation_version: int


class StoreDesktopUnlockRequest(BaseModel):
    installation_id: str
    local_auth_token: str


class StoreDesktopUnlockResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: str
    device_id: str
    staff_profile_id: str
    local_auth_token: str
    offline_valid_until: str
    activation_version: int
