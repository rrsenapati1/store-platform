from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, ComplianceRepository


class GstExportJobService:
    def __init__(self, session: AsyncSession):
        self._compliance_repo = ComplianceRepository(session)
        self._audit_repo = AuditRepository(session)

    async def handle_prepare(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        gst_export_job_id: str,
    ) -> dict[str, object]:
        bundle = await self._compliance_repo.get_export_bundle(
            tenant_id=tenant_id,
            branch_id=branch_id,
            job_id=gst_export_job_id,
        )
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GST export job not found")

        if bundle.job.status == "IRN_ATTACHED":
            return {
                "gst_export_job_id": bundle.job.id,
                "status": bundle.job.status,
                "sale_id": bundle.job.sale_id,
            }

        if bundle.job.status != "IRN_PENDING":
            await self._compliance_repo.set_export_status(bundle.job, status="IRN_PENDING")
            await self._compliance_repo.set_sale_irn_status(
                tenant_id=tenant_id,
                branch_id=branch_id,
                sale_id=bundle.job.sale_id,
                irn_status="IRN_PENDING",
            )
            await self._audit_repo.record(
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_user_id=None,
                action="gst_export.prepared",
                entity_type="gst_export_job",
                entity_id=bundle.job.id,
                payload={"sale_id": bundle.job.sale_id, "invoice_number": bundle.job.invoice_number},
            )

        return {
            "gst_export_job_id": bundle.job.id,
            "status": bundle.job.status,
            "sale_id": bundle.job.sale_id,
        }
