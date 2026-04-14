from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..repositories import AuditRepository, BillingRepository, CatalogRepository, ComplianceRepository, TenantRepository
from ..utils import utc_now
from .compliance_secrets import ComplianceSecretsService
from .irp_payloads import build_irp_invoice_payload
from .irp_provider import IrpActionRequiredError, IrpBranchCredentials, IrpTransientError, build_irp_provider


class GstExportJobService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self._settings = settings
        self._compliance_repo = ComplianceRepository(session)
        self._audit_repo = AuditRepository(session)
        self._billing_repo = BillingRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._tenant_repo = TenantRepository(session)
        self._provider = build_irp_provider(settings)

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
        profile = await self._compliance_repo.get_branch_irp_profile(tenant_id=tenant_id, branch_id=branch_id)
        if profile is None:
            await self._compliance_repo.set_export_status(bundle.job, status="ACTION_REQUIRED")
            await self._compliance_repo.update_export_job_submission(
                bundle.job,
                provider_status="MISSING_PROFILE",
                last_error_code="MISSING_PROFILE",
                last_error_message="Branch IRP provider profile is not configured",
            )
            return {
                "gst_export_job_id": bundle.job.id,
                "status": bundle.job.status,
                "sale_id": bundle.job.sale_id,
            }

        secrets = ComplianceSecretsService(secret_key=self._settings.compliance_secret_key)
        credentials = IrpBranchCredentials(
            branch_gstin=bundle.job.seller_gstin,
            api_username=profile.api_username,
            api_password=secrets.decrypt_password(profile.encrypted_api_password),
        )
        payload = bundle.job.prepared_payload
        if payload is None:
            sale_bundle = await self._billing_repo.get_sale_bundle(
                tenant_id=tenant_id,
                branch_id=branch_id,
                sale_id=bundle.job.sale_id,
            )
            branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
            if sale_bundle is None or branch is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GST export job dependencies not found")
            products_by_id = {product.id: product for product in await self._catalog_repo.list_products(tenant_id=tenant_id)}
            try:
                seller_profile = await self._provider.lookup_taxpayer(credentials, gstin=bundle.job.seller_gstin)
                buyer_profile = await self._provider.lookup_taxpayer(credentials, gstin=bundle.job.buyer_gstin or "")
                payload = build_irp_invoice_payload(
                    sale_bundle=sale_bundle,
                    branch=branch,
                    products_by_id=products_by_id,
                    seller_profile=seller_profile,
                    buyer_profile=buyer_profile,
                )
            except IrpActionRequiredError as error:
                await self._compliance_repo.set_export_status(bundle.job, status="ACTION_REQUIRED")
                await self._compliance_repo.update_export_job_submission(
                    bundle.job,
                    provider_name=profile.provider_name,
                    provider_status=error.provider_status,
                    last_error_code=error.code,
                    last_error_message=error.message,
                )
                return {
                    "gst_export_job_id": bundle.job.id,
                    "status": bundle.job.status,
                    "sale_id": bundle.job.sale_id,
                }
            except ValueError as error:
                await self._compliance_repo.set_export_status(bundle.job, status="ACTION_REQUIRED")
                await self._compliance_repo.update_export_job_submission(
                    bundle.job,
                    provider_name=profile.provider_name,
                    provider_status="INVALID_PAYLOAD",
                    last_error_code="INVALID_PAYLOAD",
                    last_error_message=str(error),
                )
                return {
                    "gst_export_job_id": bundle.job.id,
                    "status": bundle.job.status,
                    "sale_id": bundle.job.sale_id,
                }
            await self._compliance_repo.update_export_job_submission(
                bundle.job,
                provider_name=profile.provider_name,
                provider_status="READY",
                prepared_payload=payload,
                last_error_code=None,
                last_error_message=None,
            )
            await self._compliance_repo.set_export_status(bundle.job, status="READY")

        try:
            result = await self._provider.submit_irn(credentials, payload=payload)
        except IrpActionRequiredError as error:
            if error.provider_status == "DUPLICATE":
                result = await self._provider.get_irn_by_document(
                    credentials,
                    document_number=bundle.job.invoice_number,
                    document_type="INV",
                    document_date=payload["DocDtls"]["Dt"],
                )
            else:
                await self._compliance_repo.set_export_status(bundle.job, status="ACTION_REQUIRED")
                await self._compliance_repo.update_export_job_submission(
                    bundle.job,
                    provider_name=profile.provider_name,
                    provider_status=error.provider_status,
                    submission_attempt_count=bundle.job.submission_attempt_count + 1,
                    last_submitted_at=utc_now(),
                    last_error_code=error.code,
                    last_error_message=error.message,
                )
                await self._audit_repo.record(
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    actor_user_id=None,
                    action="gst_export.action_required",
                    entity_type="gst_export_job",
                    entity_id=bundle.job.id,
                    payload={"reason": error.provider_status, "code": error.code},
                )
                return {
                    "gst_export_job_id": bundle.job.id,
                    "status": bundle.job.status,
                    "sale_id": bundle.job.sale_id,
                }
        except IrpTransientError as error:
            raise RuntimeError(str(error)) from error

        attachment = await self._compliance_repo.attach_irn(
            tenant_id=tenant_id,
            branch_id=branch_id,
            gst_export_job_id=bundle.job.id,
            sales_invoice_id=bundle.job.sales_invoice_id,
            irn=result.irn or "",
            ack_no=result.ack_no or "",
            signed_qr_payload=result.signed_qr_payload or "",
        )
        await self._compliance_repo.set_export_status(bundle.job, status="IRN_ATTACHED")
        await self._compliance_repo.set_sale_irn_status(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=bundle.job.sale_id,
            irn_status="IRN_ATTACHED",
        )
        await self._compliance_repo.update_export_job_submission(
            bundle.job,
            provider_name=profile.provider_name,
            provider_status=result.provider_status,
            submission_attempt_count=bundle.job.submission_attempt_count + 1,
            last_submitted_at=utc_now(),
            last_error_code=None,
            last_error_message=None,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=None,
            action="gst_export.submitted",
            entity_type="gst_export_job",
            entity_id=bundle.job.id,
            payload={"sale_id": bundle.job.sale_id, "irn": attachment.irn},
        )
        return {
            "gst_export_job_id": bundle.job.id,
            "status": bundle.job.status,
            "sale_id": bundle.job.sale_id,
        }
