from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SupplierReportSnapshot, VendorDispute
from ..utils import new_id, utc_now


class SupplierReportingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_vendor_disputes(self, *, tenant_id: str, branch_id: str) -> list[VendorDispute]:
        statement = (
            select(VendorDispute)
            .where(
                VendorDispute.tenant_id == tenant_id,
                VendorDispute.branch_id == branch_id,
            )
            .order_by(VendorDispute.opened_on.asc(), VendorDispute.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_vendor_dispute(self, *, tenant_id: str, branch_id: str, dispute_id: str) -> VendorDispute | None:
        statement = select(VendorDispute).where(
            VendorDispute.tenant_id == tenant_id,
            VendorDispute.branch_id == branch_id,
            VendorDispute.id == dispute_id,
        )
        return await self._session.scalar(statement)

    async def create_vendor_dispute(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        supplier_id: str,
        goods_receipt_id: str | None,
        purchase_invoice_id: str | None,
        dispute_type: str,
        note: str | None,
        opened_on: date,
    ) -> VendorDispute:
        dispute = VendorDispute(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            goods_receipt_id=goods_receipt_id,
            purchase_invoice_id=purchase_invoice_id,
            dispute_type=dispute_type,
            status="OPEN",
            opened_on=opened_on,
            note=note,
        )
        self._session.add(dispute)
        await self._session.flush()
        return dispute

    async def resolve_vendor_dispute(
        self,
        *,
        dispute: VendorDispute,
        resolved_on: date,
        resolution_note: str | None,
    ) -> VendorDispute:
        dispute.status = "RESOLVED"
        dispute.resolved_on = resolved_on
        dispute.resolution_note = resolution_note
        await self._session.flush()
        return dispute

    async def get_snapshot(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        report_type: str,
        report_date: date | None,
        supplier_id: str | None = None,
    ) -> SupplierReportSnapshot | None:
        conditions = [
            SupplierReportSnapshot.tenant_id == tenant_id,
            SupplierReportSnapshot.branch_id == branch_id,
            SupplierReportSnapshot.report_type == report_type,
            SupplierReportSnapshot.supplier_id.is_(None) if supplier_id is None else SupplierReportSnapshot.supplier_id == supplier_id,
            SupplierReportSnapshot.report_date.is_(None) if report_date is None else SupplierReportSnapshot.report_date == report_date,
        ]
        statement = select(SupplierReportSnapshot).where(*conditions)
        return await self._session.scalar(statement)

    async def upsert_snapshot(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        report_type: str,
        report_date: date | None,
        payload: dict[str, object],
        source_watermark: str,
        supplier_id: str | None = None,
    ) -> SupplierReportSnapshot:
        snapshot = await self.get_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type=report_type,
            report_date=report_date,
            supplier_id=supplier_id,
        )
        if snapshot is None:
            snapshot = SupplierReportSnapshot(
                id=new_id(),
                tenant_id=tenant_id,
                branch_id=branch_id,
                supplier_id=supplier_id,
                report_type=report_type,
                report_date=report_date,
            )
            self._session.add(snapshot)
        snapshot.payload = payload
        snapshot.source_watermark = source_watermark
        snapshot.refreshed_at = utc_now()
        snapshot.is_dirty = False
        await self._session.flush()
        return snapshot

    async def mark_branch_snapshots_dirty(self, *, tenant_id: str, branch_id: str) -> None:
        statement = select(SupplierReportSnapshot).where(
            SupplierReportSnapshot.tenant_id == tenant_id,
            SupplierReportSnapshot.branch_id == branch_id,
        )
        for snapshot in (await self._session.scalars(statement)).all():
            snapshot.is_dirty = True
        await self._session.flush()
