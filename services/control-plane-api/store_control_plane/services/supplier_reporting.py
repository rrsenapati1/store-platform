from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, InventoryRepository, ProcurementFinanceRepository, PurchasingRepository, SupplierReportingRepository, TenantRepository
from ..utils import utc_now
from .supplier_reporting_finance_policy import build_supplier_aging_report, build_supplier_due_schedule, build_supplier_payment_activity_report, build_supplier_payables_report, build_supplier_settlement_report, build_supplier_statement_report
from .supplier_reporting_ops_policy import build_supplier_escalation_report, build_supplier_exception_report, build_supplier_performance_report, build_supplier_settlement_blocker_report, build_vendor_dispute_board


class SupplierReportingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._purchasing_repo = PurchasingRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._finance_repo = ProcurementFinanceRepository(session)
        self._reporting_repo = SupplierReportingRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_vendor_dispute(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        goods_receipt_id: str | None,
        purchase_invoice_id: str | None,
        dispute_type: str,
        note: str | None,
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        if bool(goods_receipt_id) == bool(purchase_invoice_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exactly one reference is required",
            )

        supplier_id: str
        if goods_receipt_id is not None:
            goods_receipt = await self._inventory_repo.get_goods_receipt(
                tenant_id=tenant_id,
                branch_id=branch_id,
                goods_receipt_id=goods_receipt_id,
            )
            if goods_receipt is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found")
            supplier_id = goods_receipt.supplier_id
        else:
            purchase_invoice = await self._finance_repo.get_purchase_invoice(
                tenant_id=tenant_id,
                branch_id=branch_id,
                purchase_invoice_id=purchase_invoice_id or "",
            )
            if purchase_invoice is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found")
            supplier_id = purchase_invoice.supplier_id

        dispute = await self._reporting_repo.create_vendor_dispute(
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            goods_receipt_id=goods_receipt_id,
            purchase_invoice_id=purchase_invoice_id,
            dispute_type=dispute_type,
            note=note,
            opened_on=utc_now().date(),
        )
        await self._reporting_repo.mark_branch_snapshots_dirty(tenant_id=tenant_id, branch_id=branch_id)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="vendor_dispute.created",
            entity_type="vendor_dispute",
            entity_id=dispute.id,
            payload={"dispute_type": dispute.dispute_type},
        )
        await self._session.commit()
        return self._serialize_vendor_dispute(dispute)

    async def resolve_vendor_dispute(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        dispute_id: str,
        actor_user_id: str,
        resolution_note: str | None,
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        dispute = await self._reporting_repo.get_vendor_dispute(
            tenant_id=tenant_id,
            branch_id=branch_id,
            dispute_id=dispute_id,
        )
        if dispute is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor dispute not found")
        if dispute.status == "RESOLVED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor dispute already resolved")

        updated = await self._reporting_repo.resolve_vendor_dispute(
            dispute=dispute,
            resolved_on=utc_now().date(),
            resolution_note=resolution_note,
        )
        await self._reporting_repo.mark_branch_snapshots_dirty(tenant_id=tenant_id, branch_id=branch_id)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="vendor_dispute.resolved",
            entity_type="vendor_dispute",
            entity_id=updated.id,
            payload={"resolution_note": resolution_note},
        )
        await self._session.commit()
        return self._serialize_vendor_dispute(updated)

    async def supplier_payables_report(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-payables-report",
            report_date=None,
            builder=lambda source, _as_of_date: build_supplier_payables_report(
                branch_id=branch_id,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_aging_report(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-aging-report",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_aging_report(
                branch_id=branch_id,
                as_of_date=report_date,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_statements(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-statements",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_statement_report(
                branch_id=branch_id,
                as_of_date=report_date,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_due_schedule(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-due-schedule",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_due_schedule(
                branch_id=branch_id,
                as_of_date=report_date,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_settlement_report(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-settlement-report",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_settlement_report(
                branch_id=branch_id,
                as_of_date=report_date,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_settlement_blockers(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-settlement-blockers",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_settlement_blocker_report(
                branch_id=branch_id,
                as_of_date=report_date,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                vendor_disputes=source["vendor_disputes"],
                goods_receipts=source["goods_receipts"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_exception_report(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-exception-report",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_exception_report(
                branch_id=branch_id,
                as_of_date=report_date,
                vendor_disputes=source["vendor_disputes"],
                goods_receipts=source["goods_receipts"],
                purchase_invoices=source["purchase_invoices"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_escalation_report(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-escalation-report",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_escalation_report(
                branch_id=branch_id,
                as_of_date=report_date,
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                supplier_payments=source["supplier_payments"],
                vendor_disputes=source["vendor_disputes"],
                goods_receipts=source["goods_receipts"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_performance_report(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-performance-report",
            report_date=None,
            builder=lambda source, _as_of_date: build_supplier_performance_report(
                branch_id=branch_id,
                purchase_orders=source["purchase_orders"],
                goods_receipts=source["goods_receipts"],
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                vendor_disputes=source["vendor_disputes"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def supplier_payment_activity(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="supplier-payment-activity",
            report_date=resolved_date,
            builder=lambda source, report_date: build_supplier_payment_activity_report(
                branch_id=branch_id,
                as_of_date=report_date,
                supplier_payments=source["supplier_payments"],
                purchase_invoices=source["purchase_invoices"],
                supplier_returns=source["supplier_returns"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def vendor_dispute_board(self, *, tenant_id: str, branch_id: str, as_of_date: date | None) -> dict[str, object]:
        resolved_date = as_of_date or utc_now().date()
        return await self._branch_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type="vendor-dispute-board",
            report_date=resolved_date,
            builder=lambda source, report_date: build_vendor_dispute_board(
                branch_id=branch_id,
                as_of_date=report_date,
                vendor_disputes=source["vendor_disputes"],
                goods_receipts=source["goods_receipts"],
                purchase_invoices=source["purchase_invoices"],
                suppliers_by_id=source["suppliers_by_id"],
            ),
        )

    async def _branch_snapshot(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        report_type: str,
        report_date: date | None,
        builder,
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        snapshot = await self._reporting_repo.get_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type=report_type,
            report_date=report_date,
        )
        if snapshot is not None and not snapshot.is_dirty:
            return dict(snapshot.payload)

        source = await self._load_source_data(tenant_id=tenant_id, branch_id=branch_id)
        payload = builder(source, report_date)
        await self._reporting_repo.upsert_snapshot(
            tenant_id=tenant_id,
            branch_id=branch_id,
            report_type=report_type,
            report_date=report_date,
            payload=payload,
            source_watermark=self._source_watermark(source),
        )
        await self._session.commit()
        return payload

    async def _load_source_data(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        suppliers = await self._purchasing_repo.list_suppliers(tenant_id=tenant_id)
        purchase_orders = await self._purchasing_repo.list_branch_purchase_orders(tenant_id=tenant_id, branch_id=branch_id)
        goods_receipts = await self._inventory_repo.list_branch_goods_receipts(tenant_id=tenant_id, branch_id=branch_id)
        purchase_invoices = await self._finance_repo.list_branch_purchase_invoices(tenant_id=tenant_id, branch_id=branch_id)
        supplier_returns = await self._finance_repo.list_branch_supplier_returns(tenant_id=tenant_id, branch_id=branch_id)
        supplier_payments = await self._finance_repo.list_branch_supplier_payments(tenant_id=tenant_id, branch_id=branch_id)
        vendor_disputes = await self._reporting_repo.list_vendor_disputes(tenant_id=tenant_id, branch_id=branch_id)

        return {
            "purchase_orders": [self._serialize_purchase_order(purchase_order) for purchase_order in purchase_orders],
            "goods_receipts": [self._serialize_goods_receipt(goods_receipt) for goods_receipt in goods_receipts],
            "purchase_invoices": [self._serialize_purchase_invoice(purchase_invoice) for purchase_invoice in purchase_invoices],
            "supplier_returns": [self._serialize_supplier_return(supplier_return) for supplier_return in supplier_returns],
            "supplier_payments": [self._serialize_supplier_payment(supplier_payment) for supplier_payment in supplier_payments],
            "vendor_disputes": [self._serialize_vendor_dispute(vendor_dispute) for vendor_dispute in vendor_disputes],
            "suppliers_by_id": {supplier.id: self._serialize_supplier(supplier) for supplier in suppliers},
            "_source_entities": {
                "purchase_orders": purchase_orders,
                "goods_receipts": goods_receipts,
                "purchase_invoices": purchase_invoices,
                "supplier_returns": supplier_returns,
                "supplier_payments": supplier_payments,
                "vendor_disputes": vendor_disputes,
            },
        }

    def _source_watermark(self, source: dict[str, object]) -> str:
        source_entities = source["_source_entities"]
        parts: list[str] = []
        for label, records in source_entities.items():
            latest = max((record.updated_at for record in records), default=None)
            parts.append(f"{label}:{len(records)}:{latest.isoformat() if latest else '-'}")
        return "|".join(parts)

    async def _assert_branch_exists(self, *, tenant_id: str, branch_id: str) -> None:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    @staticmethod
    def _serialize_supplier(supplier) -> dict[str, object]:
        return {
            "id": supplier.id,
            "name": supplier.name,
            "gstin": supplier.gstin,
            "payment_terms_days": supplier.payment_terms_days,
        }

    @staticmethod
    def _serialize_purchase_order(purchase_order) -> dict[str, object]:
        return {
            "id": purchase_order.id,
            "branch_id": purchase_order.branch_id,
            "supplier_id": purchase_order.supplier_id,
            "approval_status": purchase_order.approval_status,
            "approved_on": purchase_order.approved_at.date().isoformat() if purchase_order.approved_at else None,
        }

    @staticmethod
    def _serialize_goods_receipt(goods_receipt) -> dict[str, object]:
        return {
            "id": goods_receipt.id,
            "branch_id": goods_receipt.branch_id,
            "purchase_order_id": goods_receipt.purchase_order_id,
            "supplier_id": goods_receipt.supplier_id,
            "goods_receipt_number": goods_receipt.goods_receipt_number,
            "received_on": goods_receipt.received_on.isoformat(),
        }

    @staticmethod
    def _serialize_purchase_invoice(purchase_invoice) -> dict[str, object]:
        return {
            "id": purchase_invoice.id,
            "branch_id": purchase_invoice.branch_id,
            "supplier_id": purchase_invoice.supplier_id,
            "invoice_number": purchase_invoice.invoice_number,
            "invoice_date": purchase_invoice.invoice_date.isoformat(),
            "due_date": purchase_invoice.due_date.isoformat(),
            "payment_terms_days": purchase_invoice.payment_terms_days,
            "grand_total": purchase_invoice.grand_total,
        }

    @staticmethod
    def _serialize_supplier_return(supplier_return) -> dict[str, object]:
        return {
            "id": supplier_return.id,
            "branch_id": supplier_return.branch_id,
            "supplier_id": supplier_return.supplier_id,
            "purchase_invoice_id": supplier_return.purchase_invoice_id,
            "grand_total": supplier_return.grand_total,
        }

    @staticmethod
    def _serialize_supplier_payment(supplier_payment) -> dict[str, object]:
        return {
            "id": supplier_payment.id,
            "branch_id": supplier_payment.branch_id,
            "supplier_id": supplier_payment.supplier_id,
            "purchase_invoice_id": supplier_payment.purchase_invoice_id,
            "payment_number": supplier_payment.payment_number,
            "payment_date": supplier_payment.paid_on.isoformat(),
            "payment_method": supplier_payment.payment_method,
            "amount": supplier_payment.amount,
            "reference": supplier_payment.reference,
        }

    @staticmethod
    def _serialize_vendor_dispute(vendor_dispute) -> dict[str, object]:
        return {
            "id": vendor_dispute.id,
            "tenant_id": vendor_dispute.tenant_id,
            "branch_id": vendor_dispute.branch_id,
            "supplier_id": vendor_dispute.supplier_id,
            "goods_receipt_id": vendor_dispute.goods_receipt_id,
            "purchase_invoice_id": vendor_dispute.purchase_invoice_id,
            "dispute_type": vendor_dispute.dispute_type,
            "status": vendor_dispute.status,
            "opened_on": vendor_dispute.opened_on.isoformat(),
            "resolved_on": vendor_dispute.resolved_on.isoformat() if vendor_dispute.resolved_on else None,
            "note": vendor_dispute.note,
            "resolution_note": vendor_dispute.resolution_note,
        }
