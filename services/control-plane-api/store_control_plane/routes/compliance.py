from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import AttachIrnRequest, GstExportCreateRequest, GstExportJobListResponse, GstExportJobResponse
from ..services import ActorContext, ComplianceService, assert_branch_capability

router = APIRouter(prefix="/v1/tenants", tags=["compliance"])


@router.post("/{tenant_id}/branches/{branch_id}/compliance/gst-exports", response_model=GstExportJobResponse)
async def create_gst_export(
    tenant_id: str,
    branch_id: str,
    payload: GstExportCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> GstExportJobResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session)
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
) -> GstExportJobListResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session)
    report = await service.list_gst_export_jobs(tenant_id=tenant_id, branch_id=branch_id)
    return GstExportJobListResponse(**report)


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
) -> GstExportJobResponse:
    assert_branch_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capability="compliance.export")
    service = ComplianceService(session)
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
