from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import GstExportJob, IrnAttachment, Sale
from ..utils import new_id


@dataclass(slots=True)
class GstExportBundle:
    job: GstExportJob
    attachment: IrnAttachment | None


class ComplianceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_export_job_by_sale(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
    ) -> GstExportJob | None:
        statement = select(GstExportJob).where(
            GstExportJob.tenant_id == tenant_id,
            GstExportJob.branch_id == branch_id,
            GstExportJob.sale_id == sale_id,
        )
        return await self._session.scalar(statement)

    async def get_export_bundle(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        job_id: str,
    ) -> GstExportBundle | None:
        statement = (
            select(GstExportJob, IrnAttachment)
            .outerjoin(IrnAttachment, IrnAttachment.gst_export_job_id == GstExportJob.id)
            .where(
                GstExportJob.tenant_id == tenant_id,
                GstExportJob.branch_id == branch_id,
                GstExportJob.id == job_id,
            )
        )
        record = (await self._session.execute(statement)).first()
        if record is None:
            return None
        job, attachment = record
        return GstExportBundle(job=job, attachment=attachment)

    async def list_export_bundles(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> list[GstExportBundle]:
        statement = (
            select(GstExportJob, IrnAttachment)
            .outerjoin(IrnAttachment, IrnAttachment.gst_export_job_id == GstExportJob.id)
            .where(
                GstExportJob.tenant_id == tenant_id,
                GstExportJob.branch_id == branch_id,
            )
            .order_by(GstExportJob.created_at.asc(), GstExportJob.invoice_number.asc(), GstExportJob.id.asc())
        )
        result = await self._session.execute(statement)
        return [GstExportBundle(job=job, attachment=attachment) for job, attachment in result.all()]

    async def create_export_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        sales_invoice_id: str,
        invoice_number: str,
        customer_name: str,
        seller_gstin: str,
        buyer_gstin: str | None,
        hsn_sac_summary: str,
        grand_total: float,
        status: str,
    ) -> GstExportJob:
        job = GstExportJob(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_id,
            sales_invoice_id=sales_invoice_id,
            invoice_number=invoice_number,
            customer_name=customer_name,
            seller_gstin=seller_gstin,
            buyer_gstin=buyer_gstin,
            hsn_sac_summary=hsn_sac_summary,
            grand_total=grand_total,
            status=status,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def attach_irn(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        gst_export_job_id: str,
        sales_invoice_id: str,
        irn: str,
        ack_no: str,
        signed_qr_payload: str,
    ) -> IrnAttachment:
        attachment = IrnAttachment(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            gst_export_job_id=gst_export_job_id,
            sales_invoice_id=sales_invoice_id,
            irn=irn,
            ack_no=ack_no,
            signed_qr_payload=signed_qr_payload,
        )
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def set_export_status(self, job: GstExportJob, *, status: str) -> GstExportJob:
        job.status = status
        await self._session.flush()
        return job

    async def set_sale_irn_status(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        irn_status: str,
    ) -> None:
        sale = await self._session.scalar(
            select(Sale).where(
                Sale.tenant_id == tenant_id,
                Sale.branch_id == branch_id,
                Sale.id == sale_id,
            )
        )
        if sale is not None:
            sale.irn_status = irn_status
            await self._session.flush()
