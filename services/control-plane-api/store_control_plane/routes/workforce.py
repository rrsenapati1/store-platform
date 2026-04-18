from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import AttendanceSessionCloseRequest, AttendanceSessionCreateRequest, AttendanceSessionForceCloseRequest, AttendanceSessionListResponse, AttendanceSessionResponse, AuditListResponse, AuditRecord, BranchRuntimePolicyResponse, BranchRuntimePolicyUpsertRequest, CashierSessionCloseRequest, CashierSessionCreateRequest, CashierSessionForceCloseRequest, CashierSessionListResponse, CashierSessionResponse, DeviceClaimApprovalResponse, DeviceClaimApproveRequest, DeviceClaimListResponse, DeviceClaimRecord, DeviceRegistrationCreateRequest, DeviceRegistrationListResponse, DeviceRegistrationRecord, DeviceRegistrationResponse, RuntimeActivationIssueResponse, ShiftSessionCloseRequest, ShiftSessionCreateRequest, ShiftSessionForceCloseRequest, ShiftSessionListResponse, ShiftSessionResponse, StaffProfileCreateRequest, StaffProfileListResponse, StaffProfileRecord, StaffProfileResponse, StoreDesktopActivationIssueResponse, WorkforceAuditExportResponse
from ..services import ActorContext, WorkforceService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["workforce"])


@router.post("/{tenant_id}/staff-profiles", response_model=StaffProfileResponse)
async def create_staff_profile(
    tenant_id: str,
    payload: StaffProfileCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StaffProfileResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="staff.manage")
    service = WorkforceService(session)
    profile = await service.create_staff_profile(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        primary_branch_id=payload.primary_branch_id,
    )
    return StaffProfileResponse.model_validate(profile, from_attributes=True)


@router.get("/{tenant_id}/staff-profiles", response_model=StaffProfileListResponse)
async def list_staff_profiles(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StaffProfileListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="staff.manage")
    service = WorkforceService(session)
    records = await service.list_staff_profiles(tenant_id)
    return StaffProfileListResponse(records=[StaffProfileRecord(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/devices", response_model=DeviceRegistrationResponse)
async def register_branch_device(
    tenant_id: str,
    branch_id: str,
    payload: DeviceRegistrationCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> DeviceRegistrationResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="branch.manage")
    service = WorkforceService(session)
    device = await service.register_device(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        assigned_staff_profile_id=payload.assigned_staff_profile_id,
        installation_id=None,
        device_name=payload.device_name,
        device_code=payload.device_code,
        session_surface=payload.session_surface,
        runtime_profile=payload.runtime_profile,
        is_branch_hub=payload.is_branch_hub,
    )
    return DeviceRegistrationResponse(**device)


@router.get("/{tenant_id}/branches/{branch_id}/devices", response_model=DeviceRegistrationListResponse)
async def list_branch_devices(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> DeviceRegistrationListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="branch.manage")
    service = WorkforceService(session)
    records = await service.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
    return DeviceRegistrationListResponse(records=[DeviceRegistrationRecord(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/runtime-policy", response_model=BranchRuntimePolicyResponse)
async def get_branch_runtime_policy(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchRuntimePolicyResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    record = await service.get_branch_runtime_policy(tenant_id=tenant_id, branch_id=branch_id)
    return BranchRuntimePolicyResponse(**record)


@router.put("/{tenant_id}/branches/{branch_id}/runtime-policy", response_model=BranchRuntimePolicyResponse)
async def update_branch_runtime_policy(
    tenant_id: str,
    branch_id: str,
    payload: BranchRuntimePolicyUpsertRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchRuntimePolicyResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    record = await service.update_branch_runtime_policy(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        require_shift_for_attendance=payload.require_shift_for_attendance,
        require_attendance_for_cashier=payload.require_attendance_for_cashier,
        require_assigned_staff_for_device=payload.require_assigned_staff_for_device,
        allow_offline_sales=payload.allow_offline_sales,
        max_pending_offline_sales=payload.max_pending_offline_sales,
    )
    return BranchRuntimePolicyResponse(**record)


@router.get("/{tenant_id}/branches/{branch_id}/shift-sessions", response_model=ShiftSessionListResponse)
async def list_branch_shift_sessions(
    tenant_id: str,
    branch_id: str,
    status: str | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ShiftSessionListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    records = await service.list_branch_shift_sessions(tenant_id=tenant_id, branch_id=branch_id, status=status)
    return ShiftSessionListResponse(records=[ShiftSessionResponse(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/shift-sessions", response_model=ShiftSessionResponse)
async def create_branch_shift_session(
    tenant_id: str,
    branch_id: str,
    payload: ShiftSessionCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ShiftSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    shift_session = await service.create_shift_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        shift_name=payload.shift_name,
        opening_note=payload.opening_note,
    )
    return ShiftSessionResponse(**shift_session)


@router.get("/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}", response_model=ShiftSessionResponse)
async def get_branch_shift_session(
    tenant_id: str,
    branch_id: str,
    shift_session_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ShiftSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    shift_session = await service.get_shift_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        shift_session_id=shift_session_id,
    )
    return ShiftSessionResponse(**shift_session)


@router.post("/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}/close", response_model=ShiftSessionResponse)
async def close_branch_shift_session(
    tenant_id: str,
    branch_id: str,
    shift_session_id: str,
    payload: ShiftSessionCloseRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ShiftSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    shift_session = await service.close_shift_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        shift_session_id=shift_session_id,
        actor_user_id=actor.user_id,
        closing_note=payload.closing_note,
    )
    return ShiftSessionResponse(**shift_session)


@router.post("/{tenant_id}/branches/{branch_id}/shift-sessions/{shift_session_id}/force-close", response_model=ShiftSessionResponse)
async def force_close_branch_shift_session(
    tenant_id: str,
    branch_id: str,
    shift_session_id: str,
    payload: ShiftSessionForceCloseRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> ShiftSessionResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    shift_session = await service.force_close_shift_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        shift_session_id=shift_session_id,
        actor_user_id=actor.user_id,
        reason=payload.reason,
    )
    return ShiftSessionResponse(**shift_session)


@router.get("/{tenant_id}/branches/{branch_id}/cashier-sessions", response_model=CashierSessionListResponse)
async def list_branch_cashier_sessions(
    tenant_id: str,
    branch_id: str,
    status: str | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CashierSessionListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    records = await service.list_branch_cashier_sessions(tenant_id=tenant_id, branch_id=branch_id, status=status)
    return CashierSessionListResponse(records=[CashierSessionResponse(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/attendance-sessions", response_model=AttendanceSessionListResponse)
async def list_branch_attendance_sessions(
    tenant_id: str,
    branch_id: str,
    status: str | None = None,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> AttendanceSessionListResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    records = await service.list_branch_attendance_sessions(tenant_id=tenant_id, branch_id=branch_id, status=status)
    return AttendanceSessionListResponse(records=[AttendanceSessionResponse(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/attendance-sessions", response_model=AttendanceSessionResponse)
async def create_branch_attendance_session(
    tenant_id: str,
    branch_id: str,
    payload: AttendanceSessionCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> AttendanceSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    attendance_session = await service.create_attendance_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_registration_id=payload.device_registration_id,
        staff_profile_id=payload.staff_profile_id,
        clock_in_note=payload.clock_in_note,
    )
    return AttendanceSessionResponse(**attendance_session)


@router.post("/{tenant_id}/branches/{branch_id}/cashier-sessions", response_model=CashierSessionResponse)
async def create_branch_cashier_session(
    tenant_id: str,
    branch_id: str,
    payload: CashierSessionCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CashierSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    cashier_session = await service.create_cashier_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_registration_id=payload.device_registration_id,
        staff_profile_id=payload.staff_profile_id,
        opening_float_amount=payload.opening_float_amount,
        opening_note=payload.opening_note,
    )
    return CashierSessionResponse(**cashier_session)


@router.get("/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}", response_model=CashierSessionResponse)
async def get_branch_cashier_session(
    tenant_id: str,
    branch_id: str,
    cashier_session_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CashierSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    cashier_session = await service.get_cashier_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        cashier_session_id=cashier_session_id,
    )
    return CashierSessionResponse(**cashier_session)


@router.post("/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/close", response_model=CashierSessionResponse)
async def close_branch_cashier_session(
    tenant_id: str,
    branch_id: str,
    cashier_session_id: str,
    payload: CashierSessionCloseRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CashierSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    cashier_session = await service.close_cashier_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        cashier_session_id=cashier_session_id,
        actor_user_id=actor.user_id,
        closing_note=payload.closing_note,
    )
    return CashierSessionResponse(**cashier_session)


@router.post("/{tenant_id}/branches/{branch_id}/cashier-sessions/{cashier_session_id}/force-close", response_model=CashierSessionResponse)
async def force_close_branch_cashier_session(
    tenant_id: str,
    branch_id: str,
    cashier_session_id: str,
    payload: CashierSessionForceCloseRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CashierSessionResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    cashier_session = await service.force_close_cashier_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        cashier_session_id=cashier_session_id,
        actor_user_id=actor.user_id,
        reason=payload.reason,
    )
    return CashierSessionResponse(**cashier_session)


@router.post("/{tenant_id}/branches/{branch_id}/attendance-sessions/{attendance_session_id}/close", response_model=AttendanceSessionResponse)
async def close_branch_attendance_session(
    tenant_id: str,
    branch_id: str,
    attendance_session_id: str,
    payload: AttendanceSessionCloseRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> AttendanceSessionResponse:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("branch.manage", "sales.bill", "sales.return"),
    )
    service = WorkforceService(session)
    attendance_session = await service.close_attendance_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        attendance_session_id=attendance_session_id,
        actor_user_id=actor.user_id,
        clock_out_note=payload.clock_out_note,
    )
    return AttendanceSessionResponse(**attendance_session)


@router.post("/{tenant_id}/branches/{branch_id}/attendance-sessions/{attendance_session_id}/force-close", response_model=AttendanceSessionResponse)
async def force_close_branch_attendance_session(
    tenant_id: str,
    branch_id: str,
    attendance_session_id: str,
    payload: AttendanceSessionForceCloseRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> AttendanceSessionResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    attendance_session = await service.force_close_attendance_session(
        tenant_id=tenant_id,
        branch_id=branch_id,
        attendance_session_id=attendance_session_id,
        actor_user_id=actor.user_id,
        reason=payload.reason,
    )
    return AttendanceSessionResponse(**attendance_session)


@router.get("/{tenant_id}/branches/{branch_id}/device-claims", response_model=DeviceClaimListResponse)
async def list_branch_device_claims(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> DeviceClaimListResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    records = await service.list_branch_device_claims(tenant_id=tenant_id, branch_id=branch_id)
    return DeviceClaimListResponse(records=[DeviceClaimRecord(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/workforce-audit-events", response_model=AuditListResponse)
async def list_branch_workforce_audit_events(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> AuditListResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    records = await service.list_workforce_audit_events(tenant_id=tenant_id, branch_id=branch_id)
    return AuditListResponse(records=[AuditRecord(**record) for record in records])


@router.get("/{tenant_id}/branches/{branch_id}/workforce-audit-export", response_model=WorkforceAuditExportResponse)
async def export_branch_workforce_audit_events(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> WorkforceAuditExportResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    payload = await service.export_workforce_audit_events(tenant_id=tenant_id, branch_id=branch_id)
    return WorkforceAuditExportResponse(**payload)


@router.post("/{tenant_id}/branches/{branch_id}/device-claims/{claim_id}/approve", response_model=DeviceClaimApprovalResponse)
async def approve_branch_device_claim(
    tenant_id: str,
    branch_id: str,
    claim_id: str,
    payload: DeviceClaimApproveRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> DeviceClaimApprovalResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    response = await service.approve_device_claim(
        tenant_id=tenant_id,
        branch_id=branch_id,
        claim_id=claim_id,
        actor_user_id=actor.user_id,
        assigned_staff_profile_id=payload.assigned_staff_profile_id,
        device_name=payload.device_name,
        device_code=payload.device_code,
        session_surface=payload.session_surface,
        runtime_profile=payload.runtime_profile,
        is_branch_hub=payload.is_branch_hub,
    )
    return DeviceClaimApprovalResponse(
        claim=DeviceClaimRecord(**response["claim"]),
        device=DeviceRegistrationResponse(**response["device"]),
    )


@router.post("/{tenant_id}/branches/{branch_id}/devices/{device_id}/desktop-activation", response_model=StoreDesktopActivationIssueResponse)
async def issue_store_desktop_activation(
    tenant_id: str,
    branch_id: str,
    device_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> StoreDesktopActivationIssueResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    activation = await service.issue_store_desktop_activation(
        tenant_id=tenant_id,
        branch_id=branch_id,
        device_id=device_id,
        actor_user_id=actor.user_id,
    )
    return StoreDesktopActivationIssueResponse(**activation)


@router.post("/{tenant_id}/branches/{branch_id}/devices/{device_id}/runtime-activation", response_model=RuntimeActivationIssueResponse)
async def issue_runtime_activation(
    tenant_id: str,
    branch_id: str,
    device_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RuntimeActivationIssueResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("branch.manage",))
    service = WorkforceService(session)
    activation = await service.issue_runtime_activation(
        tenant_id=tenant_id,
        branch_id=branch_id,
        device_id=device_id,
        actor_user_id=actor.user_id,
    )
    return RuntimeActivationIssueResponse(**activation)
