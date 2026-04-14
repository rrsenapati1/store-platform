from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from .supplier_reporting import SupplierReportingService


class SupplierReportJobService:
    def __init__(self, session: AsyncSession):
        self._reporting_service = SupplierReportingService(session)

    async def handle_refresh(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        report_type: str,
        report_date: str | None,
    ) -> dict[str, object]:
        snapshot = await self._reporting_service.refresh_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type=report_type,
            report_date=None if report_date is None else date.fromisoformat(report_date),
        )
        return {
            "report_type": snapshot.report_type,
            "report_date": snapshot.report_date.isoformat() if snapshot.report_date is not None else None,
            "snapshot_id": snapshot.id,
            "snapshot_status": "CURRENT",
        }
