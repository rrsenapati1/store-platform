from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..repositories import AuditRepository, BillingRepository, CatalogRepository, ComplianceRepository, TenantRepository
from .operations_queue import OperationsQueueService
from .compliance_policy import build_hsn_sac_summary, ensure_gst_export_allowed, ensure_irn_attachment_allowed
from .compliance_secrets import ComplianceSecretsService


class ComplianceService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self._session = session
        self._settings = settings
        self._tenant_repo = TenantRepository(session)
        self._billing_repo = BillingRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._compliance_repo = ComplianceRepository(session)
        self._audit_repo = AuditRepository(session)
        self._operations_queue = OperationsQueueService(session)

    async def create_gst_export_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        sale_bundle = await self._billing_repo.get_sale_bundle(tenant_id=tenant_id, branch_id=branch_id, sale_id=sale_id)
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        try:
            ensure_gst_export_allowed(
                invoice_kind=sale_bundle.sale.invoice_kind,
                irn_status=sale_bundle.sale.irn_status,
                seller_gstin=branch.gstin,
                buyer_gstin=sale_bundle.sale.customer_gstin,
            )
            products_by_id = {
                product.id: product
                for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
            }
            hsn_sac_summary = build_hsn_sac_summary(
                [products_by_id[line.product_id].hsn_sac_code for line in sale_bundle.lines if line.product_id in products_by_id]
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        existing_job = await self._compliance_repo.get_export_job_by_sale(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_id,
        )
        if existing_job is not None:
            existing_bundle = await self._compliance_repo.get_export_bundle(
                tenant_id=tenant_id,
                branch_id=branch_id,
                job_id=existing_job.id,
            )
            return self._serialize_job(
                job=existing_job if existing_bundle is None else existing_bundle.job,
                attachment=None if existing_bundle is None else existing_bundle.attachment,
            )

        job = await self._compliance_repo.create_export_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_bundle.sale.id,
            sales_invoice_id=sale_bundle.invoice.id,
            invoice_number=sale_bundle.invoice.invoice_number,
            customer_name=sale_bundle.sale.customer_name,
            seller_gstin=branch.gstin or "",
            buyer_gstin=sale_bundle.sale.customer_gstin,
            hsn_sac_summary=hsn_sac_summary,
            grand_total=sale_bundle.sale.grand_total,
            status="QUEUED",
        )
        await self._operations_queue.enqueue_branch_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            created_by_user_id=actor_user_id,
            job_type="GST_EXPORT_PREPARE",
            queue_key=f"gst-export:{tenant_id}:{branch_id}:{sale_bundle.sale.id}",
            payload={
                "gst_export_job_id": job.id,
                "sale_id": sale_bundle.sale.id,
                "sales_invoice_id": sale_bundle.invoice.id,
            },
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="gst_export.queued",
            entity_type="gst_export_job",
            entity_id=job.id,
            payload={"sale_id": sale_bundle.sale.id, "invoice_number": sale_bundle.invoice.invoice_number},
        )
        await self._session.commit()
        return self._serialize_job(job=job, attachment=None)

    async def list_gst_export_jobs(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        bundles = await self._compliance_repo.list_export_bundles(tenant_id=tenant_id, branch_id=branch_id)
        records = [self._serialize_job(job=bundle.job, attachment=bundle.attachment) for bundle in bundles]
        return {
            "branch_id": branch_id,
            "pending_count": sum(
                1
                for record in records
                if record["status"] in {"QUEUED", "IRN_PENDING", "PREPARING", "READY", "SUBMITTING", "RETRY_QUEUED"}
            ),
            "attached_count": sum(1 for record in records if record["status"] == "IRN_ATTACHED"),
            "records": records,
        }

    async def get_branch_irp_profile(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        profile = await self._compliance_repo.get_branch_irp_profile(tenant_id=tenant_id, branch_id=branch_id)
        if profile is None:
            return {
                "provider_name": None,
                "api_username": None,
                "has_password": False,
                "status": "NOT_CONFIGURED",
                "last_error_message": None,
            }
        return {
            "provider_name": profile.provider_name,
            "api_username": profile.api_username,
            "has_password": bool(profile.encrypted_api_password),
            "status": profile.status,
            "last_error_message": profile.last_error_message,
        }

    async def upsert_branch_irp_profile(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        provider_name: str,
        api_username: str,
        api_password: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        if not branch.gstin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch GSTIN is required")
        secrets = ComplianceSecretsService(secret_key=self._settings.compliance_secret_key)
        existing = await self._compliance_repo.get_branch_irp_profile(tenant_id=tenant_id, branch_id=branch_id)
        if existing is None and not api_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API password is required")
        encrypted_api_password = (
            secrets.encrypt_password(api_password)
            if api_password
            else (existing.encrypted_api_password if existing is not None else "")
        )
        profile = await self._compliance_repo.upsert_branch_irp_profile(
            tenant_id=tenant_id,
            branch_id=branch_id,
            provider_name=provider_name,
            api_username=api_username,
            encrypted_api_password=encrypted_api_password,
            status="CONFIGURED",
            last_error_message=None,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="compliance.irp_profile_upserted",
            entity_type="branch_irp_profile",
            entity_id=profile.id,
            payload={"provider_name": provider_name, "api_username": api_username},
        )
        await self._session.commit()
        return {
            "provider_name": profile.provider_name,
            "api_username": profile.api_username,
            "has_password": True,
            "status": profile.status,
            "last_error_message": profile.last_error_message,
        }

    async def attach_irn(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        job_id: str,
        actor_user_id: str,
        irn: str,
        ack_no: str,
        signed_qr_payload: str,
    ) -> dict[str, object]:
        bundle = await self._compliance_repo.get_export_bundle(tenant_id=tenant_id, branch_id=branch_id, job_id=job_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GST export job not found")

        try:
            ensure_irn_attachment_allowed(
                current_status=bundle.job.status,
                has_attachment=bundle.attachment is not None,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        attachment = await self._compliance_repo.attach_irn(
            tenant_id=tenant_id,
            branch_id=branch_id,
            gst_export_job_id=bundle.job.id,
            sales_invoice_id=bundle.job.sales_invoice_id,
            irn=irn,
            ack_no=ack_no,
            signed_qr_payload=signed_qr_payload,
        )
        await self._compliance_repo.set_export_status(bundle.job, status="IRN_ATTACHED")
        await self._compliance_repo.set_sale_irn_status(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=bundle.job.sale_id,
            irn_status="IRN_ATTACHED",
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="irn.attached",
            entity_type="gst_export_job",
            entity_id=bundle.job.id,
            payload={"sales_invoice_id": bundle.job.sales_invoice_id, "irn": irn},
        )
        await self._session.commit()
        return self._serialize_job(job=bundle.job, attachment=attachment)

    async def retry_gst_export_submission(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        job_id: str,
        actor_user_id: str,
    ) -> dict[str, object]:
        bundle = await self._compliance_repo.get_export_bundle(tenant_id=tenant_id, branch_id=branch_id, job_id=job_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GST export job not found")
        if bundle.job.status == "IRN_ATTACHED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GST export job is already attached")
        await self._compliance_repo.set_export_status(bundle.job, status="RETRY_QUEUED")
        await self._compliance_repo.update_export_job_submission(
            bundle.job,
            provider_status="RETRY_QUEUED",
            last_error_code=None,
            last_error_message=None,
        )
        await self._operations_queue.enqueue_branch_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            created_by_user_id=actor_user_id,
            job_type="GST_EXPORT_PREPARE",
            queue_key=f"gst-export:{tenant_id}:{branch_id}:{bundle.job.sale_id}",
            payload={
                "gst_export_job_id": bundle.job.id,
                "sale_id": bundle.job.sale_id,
                "sales_invoice_id": bundle.job.sales_invoice_id,
            },
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="gst_export.retry_queued",
            entity_type="gst_export_job",
            entity_id=bundle.job.id,
            payload={"sale_id": bundle.job.sale_id, "invoice_number": bundle.job.invoice_number},
        )
        await self._session.commit()
        return self._serialize_job(job=bundle.job, attachment=bundle.attachment)

    @staticmethod
    def _serialize_job(*, job, attachment) -> dict[str, object]:
        return {
            "id": job.id,
            "sale_id": job.sale_id,
            "invoice_id": job.sales_invoice_id,
            "invoice_number": job.invoice_number,
            "customer_name": job.customer_name,
            "seller_gstin": job.seller_gstin,
            "buyer_gstin": job.buyer_gstin,
            "hsn_sac_summary": job.hsn_sac_summary,
            "grand_total": job.grand_total,
            "status": job.status,
            "provider_name": job.provider_name,
            "provider_status": job.provider_status,
            "last_error_code": job.last_error_code,
            "last_error_message": job.last_error_message,
            "irn": attachment.irn if attachment is not None else None,
            "ack_no": attachment.ack_no if attachment is not None else None,
            "signed_qr_payload": attachment.signed_qr_payload if attachment is not None else None,
            "created_at": job.created_at,
        }
