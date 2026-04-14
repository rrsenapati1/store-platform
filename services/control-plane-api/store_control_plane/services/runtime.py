from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, BarcodeRepository, BillingRepository, CatalogRepository, RuntimeRepository, TenantRepository, WorkforceRepository
from .barcode_policy import build_barcode_label_preview, normalize_barcode
from ..utils import utc_now


def _money(value: float) -> str:
    return f"{value:.2f}"


def _invoice_receipt_lines(*, sale_bundle, products_by_id: dict[str, object]) -> list[str]:
    lines = [
        "STORE TAX INVOICE",
        f"Invoice: {sale_bundle.invoice.invoice_number}",
        f"Customer: {sale_bundle.sale.customer_name}",
    ]
    if sale_bundle.sale.customer_gstin:
        lines.append(f"GSTIN: {sale_bundle.sale.customer_gstin}")
    for line in sale_bundle.lines:
        product = products_by_id.get(line.product_id)
        product_name = product.name if product is not None else line.product_id
        lines.append(f"{product_name} x{line.quantity:g} @ {_money(line.unit_price)} = {_money(line.line_total)}")
    lines.extend(
        [
            f"Subtotal: {_money(sale_bundle.invoice.subtotal)}",
            f"CGST: {_money(sale_bundle.invoice.cgst_total)}",
            f"SGST: {_money(sale_bundle.invoice.sgst_total)}",
            f"IGST: {_money(sale_bundle.invoice.igst_total)}",
            f"Grand Total: {_money(sale_bundle.invoice.grand_total)}",
            f"IRN Status: {sale_bundle.sale.irn_status}",
        ]
    )
    return lines


def _credit_note_receipt_lines(*, sale_bundle, sale_return, credit_note, return_lines, products_by_id: dict[str, object]) -> list[str]:
    lines = [
        "STORE CREDIT NOTE",
        f"Credit Note: {credit_note.credit_note_number}",
        f"Customer: {sale_bundle.sale.customer_name}",
    ]
    if sale_bundle.sale.customer_gstin:
        lines.append(f"GSTIN: {sale_bundle.sale.customer_gstin}")
    for line in return_lines:
        product = products_by_id.get(line.product_id)
        product_name = product.name if product is not None else line.product_id
        lines.append(f"{product_name} x{line.quantity:g} @ {_money(line.unit_price)} = {_money(line.line_total)}")
    lines.extend(
        [
            f"Subtotal: {_money(credit_note.subtotal)}",
            f"CGST: {_money(credit_note.cgst_total)}",
            f"SGST: {_money(credit_note.sgst_total)}",
            f"IGST: {_money(credit_note.igst_total)}",
            f"Grand Total: {_money(credit_note.grand_total)}",
            f"Refund: {sale_return.refund_method} {_money(sale_return.refund_amount)}",
        ]
    )
    return lines


class RuntimeService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._barcode_repo = BarcodeRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._billing_repo = BillingRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._runtime_repo = RuntimeRepository(session)
        self._audit_repo = AuditRepository(session)

    async def list_runtime_devices(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        devices = await self._workforce_repo.list_branch_devices(tenant_id=tenant_id, branch_id=branch_id)
        profiles = {
            profile.id: profile
            for profile in await self._workforce_repo.list_staff_profiles(tenant_id=tenant_id)
        }
        return [
            {
                "id": device.id,
                "tenant_id": device.tenant_id,
                "branch_id": device.branch_id,
                "device_name": device.device_name,
                "device_code": device.device_code,
                "session_surface": device.session_surface,
                "status": device.status,
                "assigned_staff_profile_id": device.assigned_staff_profile_id,
                "assigned_staff_full_name": profiles.get(device.assigned_staff_profile_id).full_name
                if device.assigned_staff_profile_id and profiles.get(device.assigned_staff_profile_id)
                else None,
                "last_seen_at": device.last_seen_at,
            }
            for device in devices
            if device.status == "ACTIVE"
        ]

    async def record_device_heartbeat(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_id: str,
    ) -> dict[str, object]:
        device = await self._get_active_device(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        touched = await self._workforce_repo.touch_device_registration(device=device, seen_at=utc_now())
        queued_job_count = await self._runtime_repo.count_device_print_jobs(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            status="QUEUED",
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="runtime_device.heartbeat",
            entity_type="device_registration",
            entity_id=device_id,
            payload={"queued_job_count": queued_job_count},
        )
        await self._session.commit()
        return {
            "device_id": touched.id,
            "status": touched.status,
            "last_seen_at": touched.last_seen_at,
            "queued_job_count": queued_job_count,
        }

    async def queue_sale_invoice_print_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_id: str,
        sale_id: str,
        copies: int,
    ) -> dict[str, object]:
        if copies < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Copies must be at least 1")
        await self._get_active_device(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        sale_bundle = await self._billing_repo.get_sale_bundle(tenant_id=tenant_id, branch_id=branch_id, sale_id=sale_id)
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        payload = {
            "document_number": sale_bundle.invoice.invoice_number,
            "customer_name": sale_bundle.sale.customer_name,
            "receipt_lines": _invoice_receipt_lines(
                sale_bundle=sale_bundle,
                products_by_id=await self._products_by_id(tenant_id=tenant_id),
            ),
        }
        job = await self._runtime_repo.create_print_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            reference_type="sale",
            reference_id=sale_id,
            job_type="SALES_INVOICE",
            copies=copies,
            payload=payload,
        )
        await self._record_print_job_queue_audit(actor_user_id=actor_user_id, job=job)
        await self._session.commit()
        return self._serialize_print_job(job)

    async def queue_sale_return_print_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_id: str,
        sale_return_id: str,
        copies: int,
    ) -> dict[str, object]:
        if copies < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Copies must be at least 1")
        await self._get_active_device(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        sale_return = await self._billing_repo.get_sale_return(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_return_id=sale_return_id,
        )
        if sale_return is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale return not found")
        credit_note = await self._billing_repo.get_credit_note_for_sale_return(sale_return_id=sale_return_id)
        if credit_note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit note not found")
        sale_bundle = await self._billing_repo.get_sale_bundle(
            tenant_id=tenant_id,
            branch_id=branch_id,
            sale_id=sale_return.sale_id,
        )
        if sale_bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original sale not found")
        return_lines = (
            await self._billing_repo.list_sale_return_lines_for_returns(sale_return_ids=[sale_return.id])
        ).get(sale_return.id, [])
        payload = {
            "document_number": credit_note.credit_note_number,
            "customer_name": sale_bundle.sale.customer_name,
            "receipt_lines": _credit_note_receipt_lines(
                sale_bundle=sale_bundle,
                sale_return=sale_return,
                credit_note=credit_note,
                return_lines=return_lines,
                products_by_id=await self._products_by_id(tenant_id=tenant_id),
            ),
        }
        job = await self._runtime_repo.create_print_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            reference_type="sale_return",
            reference_id=sale_return_id,
            job_type="CREDIT_NOTE",
            copies=copies,
            payload=payload,
        )
        await self._record_print_job_queue_audit(actor_user_id=actor_user_id, job=job)
        await self._session.commit()
        return self._serialize_print_job(job)

    async def queue_barcode_label_print_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_id: str,
        product_id: str,
        copies: int,
    ) -> dict[str, object]:
        if copies < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Copies must be at least 1")
        await self._get_active_device(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)

        product = await self._barcode_repo.get_product(tenant_id=tenant_id, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")
        branch_item = await self._barcode_repo.get_branch_catalog_item(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
        )
        if branch_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch catalog item not found")

        barcode = normalize_barcode(product.barcode or "")
        if not barcode:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog product barcode is not allocated")

        effective_selling_price = (
            branch_item.selling_price_override
            if branch_item.selling_price_override is not None
            else product.selling_price
        )
        label = build_barcode_label_preview(
            sku_value=product.sku_code,
            product_name=product.name,
            barcode=barcode,
            selling_price=effective_selling_price,
        )
        payload = {
            "product_id": product.id,
            "labels": [dict(label) for _ in range(copies)],
        }
        job = await self._runtime_repo.create_print_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            reference_type="catalog_product",
            reference_id=product_id,
            job_type="BARCODE_LABEL",
            copies=copies,
            payload=payload,
        )
        await self._record_print_job_queue_audit(actor_user_id=actor_user_id, job=job)
        await self._session.commit()
        return self._serialize_print_job(job)

    async def list_device_print_jobs(self, *, tenant_id: str, branch_id: str, device_id: str) -> list[dict[str, object]]:
        await self._get_active_device(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        jobs = await self._runtime_repo.list_device_print_jobs(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            status="QUEUED",
        )
        return [self._serialize_print_job(job) for job in jobs]

    async def complete_print_job(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        device_id: str,
        print_job_id: str,
        completion_status: str,
        failure_reason: str | None,
    ) -> dict[str, object]:
        await self._get_active_device(tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        if completion_status not in {"COMPLETED", "FAILED"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported print job status")
        if completion_status == "FAILED" and not failure_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failure reason is required for failed jobs")
        job = await self._runtime_repo.get_print_job(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            print_job_id=print_job_id,
        )
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print job not found")
        updated = await self._runtime_repo.complete_print_job(
            print_job=job,
            status=completion_status,
            failure_reason=failure_reason,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="print_job.completed",
            entity_type="print_job",
            entity_id=updated.id,
            payload={"status": updated.status, "failure_reason": updated.failure_reason},
        )
        await self._session.commit()
        return self._serialize_print_job(updated)

    async def _record_print_job_queue_audit(self, *, actor_user_id: str, job) -> None:
        await self._audit_repo.record(
            tenant_id=job.tenant_id,
            branch_id=job.branch_id,
            actor_user_id=actor_user_id,
            action="print_job.queued",
            entity_type="print_job",
            entity_id=job.id,
            payload={"job_type": job.job_type, "reference_type": job.reference_type, "reference_id": job.reference_id},
        )

    async def _assert_branch_exists(self, *, tenant_id: str, branch_id: str) -> None:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    async def _get_active_device(self, *, tenant_id: str, branch_id: str, device_id: str):
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        device = await self._workforce_repo.get_device_registration(
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
        )
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device is not active")
        return device

    async def _products_by_id(self, *, tenant_id: str) -> dict[str, object]:
        return {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }

    @staticmethod
    def _serialize_print_job(job) -> dict[str, object]:
        return {
            "id": job.id,
            "tenant_id": job.tenant_id,
            "branch_id": job.branch_id,
            "device_id": job.device_id,
            "reference_type": job.reference_type,
            "reference_id": job.reference_id,
            "job_type": job.job_type,
            "copies": job.copies,
            "status": job.status,
            "failure_reason": job.failure_reason,
            "payload": job.payload,
        }
