from __future__ import annotations

from datetime import datetime

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
    runtime_profile: str | None = None
    assigned_staff_profile_id: str | None = None
    is_branch_hub: bool = False


class DeviceRegistrationResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    device_name: str
    device_code: str
    session_surface: str
    runtime_profile: str
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
    runtime_profile: str
    is_branch_hub: bool = False
    status: str
    assigned_staff_profile_id: str | None = None
    assigned_staff_full_name: str | None = None
    installation_id: str | None = None


class DeviceRegistrationListResponse(BaseModel):
    records: list[DeviceRegistrationRecord]


class CashierSessionCreateRequest(BaseModel):
    device_registration_id: str
    staff_profile_id: str
    opening_float_amount: float = 0
    opening_note: str | None = None


class CashierSessionCloseRequest(BaseModel):
    closing_note: str | None = None


class CashierSessionForceCloseRequest(BaseModel):
    reason: str


class CashierSessionResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    device_registration_id: str
    device_name: str | None = None
    device_code: str | None = None
    staff_profile_id: str
    staff_full_name: str | None = None
    runtime_user_id: str | None = None
    opened_by_user_id: str | None = None
    closed_by_user_id: str | None = None
    status: str
    session_number: str
    opening_float_amount: float
    opening_note: str | None = None
    closing_note: str | None = None
    force_close_reason: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    last_activity_at: datetime | None = None
    linked_sales_count: int = 0
    linked_returns_count: int = 0
    gross_billed_amount: float = 0


class CashierSessionListResponse(BaseModel):
    records: list[CashierSessionResponse]


class AttendanceSessionCreateRequest(BaseModel):
    device_registration_id: str
    staff_profile_id: str
    clock_in_note: str | None = None


class AttendanceSessionCloseRequest(BaseModel):
    clock_out_note: str | None = None


class AttendanceSessionForceCloseRequest(BaseModel):
    reason: str


class AttendanceSessionResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    shift_session_id: str | None = None
    device_registration_id: str
    device_name: str | None = None
    device_code: str | None = None
    staff_profile_id: str
    staff_full_name: str | None = None
    runtime_user_id: str | None = None
    opened_by_user_id: str | None = None
    closed_by_user_id: str | None = None
    status: str
    attendance_number: str
    clock_in_note: str | None = None
    clock_out_note: str | None = None
    force_close_reason: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    last_activity_at: datetime | None = None
    linked_cashier_sessions_count: int = 0


class AttendanceSessionListResponse(BaseModel):
    records: list[AttendanceSessionResponse]


class ShiftSessionCreateRequest(BaseModel):
    shift_name: str
    opening_note: str | None = None


class ShiftSessionCloseRequest(BaseModel):
    closing_note: str | None = None


class ShiftSessionForceCloseRequest(BaseModel):
    reason: str


class ShiftSessionResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    opened_by_user_id: str | None = None
    closed_by_user_id: str | None = None
    status: str
    shift_number: str
    shift_name: str
    opening_note: str | None = None
    closing_note: str | None = None
    force_close_reason: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    last_activity_at: datetime | None = None
    linked_attendance_sessions_count: int = 0
    linked_cashier_sessions_count: int = 0


class ShiftSessionListResponse(BaseModel):
    records: list[ShiftSessionResponse]


class BranchRuntimePolicyUpsertRequest(BaseModel):
    require_shift_for_attendance: bool
    require_attendance_for_cashier: bool
    require_assigned_staff_for_device: bool
    allow_offline_sales: bool
    max_pending_offline_sales: int


class BranchRuntimePolicyResponse(BaseModel):
    id: str | None = None
    tenant_id: str
    branch_id: str
    require_shift_for_attendance: bool
    require_attendance_for_cashier: bool
    require_assigned_staff_for_device: bool
    allow_offline_sales: bool
    max_pending_offline_sales: int
    updated_by_user_id: str | None = None


class WorkforceAuditExportResponse(BaseModel):
    filename: str
    content_type: str
    content: str


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
    runtime_profile: str | None = None
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


class RuntimeActivationIssueResponse(BaseModel):
    device_id: str
    staff_profile_id: str
    activation_code: str
    status: str
    expires_at: str
    runtime_profile: str
    session_surface: str


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
