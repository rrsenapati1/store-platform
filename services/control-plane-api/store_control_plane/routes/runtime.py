from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import DeviceRegistrationListResponse, DeviceRegistrationRecord, PrintJobCompletionRequest, PrintJobListResponse, PrintJobQueueRequest, PrintJobResponse, RuntimeDeviceClaimResolveRequest, RuntimeDeviceClaimResolveResponse, RuntimeDeviceHeartbeatResponse, RuntimeHubBootstrapRequest, RuntimeHubBootstrapResponse
from ..services import ActorContext, RuntimeService, WorkforceService, assert_branch_any_capability

router = APIRouter(prefix="/v1/tenants", tags=["runtime"])


def _assert_runtime_access(actor: ActorContext, *, tenant_id: str, branch_id: str) -> None:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("sales.bill", "sales.return", "refund.approve"),
    )


def _assert_barcode_print_access(actor: ActorContext, *, tenant_id: str, branch_id: str) -> None:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("barcode.manage", "catalog.manage", "sales.bill"),
    )


@router.get("/{tenant_id}/branches/{branch_id}/runtime/devices", response_model=DeviceRegistrationListResponse)
async def list_runtime_devices(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> DeviceRegistrationListResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    records = await service.list_runtime_devices(tenant_id=tenant_id, branch_id=branch_id)
    return DeviceRegistrationListResponse(records=[DeviceRegistrationRecord(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/runtime/device-claim", response_model=RuntimeDeviceClaimResolveResponse)
async def resolve_runtime_device_claim(
    tenant_id: str,
    branch_id: str,
    payload: RuntimeDeviceClaimResolveRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RuntimeDeviceClaimResolveResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = WorkforceService(session)
    claim = await service.resolve_runtime_device_claim(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        installation_id=payload.installation_id,
        runtime_kind=payload.runtime_kind,
        hostname=payload.hostname,
        operating_system=payload.operating_system,
        architecture=payload.architecture,
        app_version=payload.app_version,
    )
    return RuntimeDeviceClaimResolveResponse(**claim)


@router.post("/{tenant_id}/branches/{branch_id}/runtime/hub-bootstrap", response_model=RuntimeHubBootstrapResponse)
async def bootstrap_runtime_hub_identity(
    tenant_id: str,
    branch_id: str,
    payload: RuntimeHubBootstrapRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RuntimeHubBootstrapResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    bootstrap = await service.bootstrap_branch_hub_runtime_identity(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor=actor,
        installation_id=payload.installation_id,
    )
    return RuntimeHubBootstrapResponse(**bootstrap)


@router.post("/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/heartbeat", response_model=RuntimeDeviceHeartbeatResponse)
async def record_runtime_device_heartbeat(
    tenant_id: str,
    branch_id: str,
    device_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> RuntimeDeviceHeartbeatResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    heartbeat = await service.record_device_heartbeat(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_id=device_id,
    )
    return RuntimeDeviceHeartbeatResponse(**heartbeat)


@router.get("/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs", response_model=PrintJobListResponse)
async def list_runtime_device_print_jobs(
    tenant_id: str,
    branch_id: str,
    device_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PrintJobListResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    records = await service.list_device_print_jobs(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
    return PrintJobListResponse(records=[PrintJobResponse(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs/{print_job_id}/complete", response_model=PrintJobResponse)
async def complete_runtime_print_job(
    tenant_id: str,
    branch_id: str,
    device_id: str,
    print_job_id: str,
    payload: PrintJobCompletionRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PrintJobResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    record = await service.complete_print_job(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_id=device_id,
        print_job_id=print_job_id,
        completion_status=payload.status,
        failure_reason=payload.failure_reason,
    )
    return PrintJobResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sales/{sale_id}", response_model=PrintJobResponse)
async def queue_sale_invoice_print_job(
    tenant_id: str,
    branch_id: str,
    sale_id: str,
    payload: PrintJobQueueRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PrintJobResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    record = await service.queue_sale_invoice_print_job(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_id=payload.device_id,
        sale_id=sale_id,
        copies=payload.copies,
    )
    return PrintJobResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sale-returns/{sale_return_id}", response_model=PrintJobResponse)
async def queue_sale_return_print_job(
    tenant_id: str,
    branch_id: str,
    sale_return_id: str,
    payload: PrintJobQueueRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PrintJobResponse:
    _assert_runtime_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    record = await service.queue_sale_return_print_job(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_id=payload.device_id,
        sale_return_id=sale_return_id,
        copies=payload.copies,
    )
    return PrintJobResponse(**record)


@router.post("/{tenant_id}/branches/{branch_id}/runtime/print-jobs/barcode-labels/{product_id}", response_model=PrintJobResponse)
async def queue_barcode_label_print_job(
    tenant_id: str,
    branch_id: str,
    product_id: str,
    payload: PrintJobQueueRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PrintJobResponse:
    _assert_barcode_print_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = RuntimeService(session)
    record = await service.queue_barcode_label_print_job(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        device_id=payload.device_id,
        product_id=product_id,
        copies=payload.copies,
    )
    return PrintJobResponse(**record)
