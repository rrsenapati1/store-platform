from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session, get_settings
from ..schemas import AttachIrnRequest, BranchIrpProfileResponse, BranchIrpProfileUpsertRequest, GstExportCreateRequest, GstExportJobListResponse, GstExportJobResponse
from ..services import ActorContext, ComplianceService, assert_branch_capability
from ..config import Settings

router = APIRouter(prefix="/v1/tenants", tags=["compliance"])


@router.post("/{tenant_id}/branches/{branch_id}/compliance/gst-exports", response_model=GstExportJobResponse)
async def create_gst_export(
    tenant_id: str,
    branch_id: str,
    payload: GstExportCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> GstExportJobResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session, settings)
    job = await service.create_gst_export_job(
        tenant_id=tenant_id,
        branch_id=branch_id,
        sale_id=payload.sale_id,
        actor_user_id=actor.user_id,
    )
    return GstExportJobResponse(**job)


@router.get("/{tenant_id}/branches/{branch_id}/compliance/gst-exports", response_model=GstExportJobListResponse)
async def list_gst_exports(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> GstExportJobListResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session, settings)
    report = await service.list_gst_export_jobs(tenant_id=tenant_id, branch_id=branch_id)
    return GstExportJobListResponse(**report)


@router.get("/{tenant_id}/branches/{branch_id}/compliance/provider-profile", response_model=BranchIrpProfileResponse)
async def get_branch_irp_profile(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BranchIrpProfileResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session, settings)
    profile = await service.get_branch_irp_profile(tenant_id=tenant_id, branch_id=branch_id)
    return BranchIrpProfileResponse(**profile)


@router.put("/{tenant_id}/branches/{branch_id}/compliance/provider-profile", response_model=BranchIrpProfileResponse)
async def upsert_branch_irp_profile(
    tenant_id: str,
    branch_id: str,
    payload: BranchIrpProfileUpsertRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BranchIrpProfileResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session, settings)
    profile = await service.upsert_branch_irp_profile(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        provider_name=payload.provider_name,
        api_username=payload.api_username,
        api_password=payload.api_password,
    )
    return BranchIrpProfileResponse(**profile)


@router.post(
    "/{tenant_id}/branches/{branch_id}/compliance/gst-exports/{job_id}/attach-irn",
    response_model=GstExportJobResponse,
)
async def attach_irn(
    tenant_id: str,
    branch_id: str,
    job_id: str,
    payload: AttachIrnRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> GstExportJobResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session, settings)
    job = await service.attach_irn(
        tenant_id=tenant_id,
        branch_id=branch_id,
        job_id=job_id,
        actor_user_id=actor.user_id,
        irn=payload.irn,
        ack_no=payload.ack_no,
        signed_qr_payload=payload.signed_qr_payload,
    )
    return GstExportJobResponse(**job)


@router.post(
    "/{tenant_id}/branches/{branch_id}/compliance/gst-exports/{job_id}/retry-submission",
    response_model=GstExportJobResponse,
)
async def retry_gst_export_submission(
    tenant_id: str,
    branch_id: str,
    job_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> GstExportJobResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session, settings)
    job = await service.retry_gst_export_submission(
        tenant_id=tenant_id,
        branch_id=branch_id,
        job_id=job_id,
        actor_user_id=actor.user_id,
    )
    return GstExportJobResponse(**job)
