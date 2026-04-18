from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import (
    CatalogRepository,
    InventoryRepository,
    OperationsRepository,
    ProcurementFinanceRepository,
    PurchasingRepository,
    TenantRepository,
    WorkforceRepository,
)
from ..repositories.operations import ACTIVE_JOB_STATUSES
from ..utils import utc_now
from .batches import BatchService
from .billing import BillingService
from .inventory import InventoryService
from .procurement_finance import ProcurementFinanceService
from .purchasing import PurchasingService
from .supplier_reporting import SupplierReportingService


class ReportingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._purchasing_repo = PurchasingRepository(session)
        self._finance_repo = ProcurementFinanceRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._operations_repo = OperationsRepository(session)
        self._inventory_service = InventoryService(session)
        self._batch_service = BatchService(session)
        self._billing_service = BillingService(session)
        self._purchasing_service = PurchasingService(session)
        self._finance_service = ProcurementFinanceService(session)
        self._supplier_reporting_service = SupplierReportingService(session)

    async def branch_management_dashboard(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        as_of_date = utc_now().date()
        [
            sales,
            sale_returns,
            replenishment_board,
            restock_board,
            receiving_board,
            stock_count_board,
            batch_expiry_report,
            purchase_approval_report,
            supplier_payables_report,
            supplier_settlement_blockers,
            cashier_sessions,
            attendance_sessions,
            shift_sessions,
            operations_jobs,
            purchase_orders,
            goods_receipts,
            purchase_invoices,
            supplier_returns,
            supplier_payments,
            branch_catalog_items,
        ] = await asyncio.gather(
            self._billing_service.list_sales(tenant_id=tenant_id, branch_id=branch_id),
            self._billing_service.list_sale_returns(tenant_id=tenant_id, branch_id=branch_id),
            self._inventory_service.replenishment_board(tenant_id=tenant_id, branch_id=branch_id),
            self._inventory_service.restock_board(tenant_id=tenant_id, branch_id=branch_id),
            self._inventory_service.receiving_board(tenant_id=tenant_id, branch_id=branch_id),
            self._inventory_service.stock_count_board(tenant_id=tenant_id, branch_id=branch_id),
            self._batch_service.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id),
            self._purchasing_service.purchase_approval_report(tenant_id=tenant_id, branch_id=branch_id),
            self._finance_service.supplier_payables_report(tenant_id=tenant_id, branch_id=branch_id),
            self._supplier_reporting_service.supplier_settlement_blockers(
                tenant_id=tenant_id,
                branch_id=branch_id,
                as_of_date=as_of_date,
            ),
            self._workforce_repo.list_branch_cashier_sessions(tenant_id=tenant_id, branch_id=branch_id),
            self._workforce_repo.list_branch_attendance_sessions(tenant_id=tenant_id, branch_id=branch_id),
            self._workforce_repo.list_branch_shift_sessions(tenant_id=tenant_id, branch_id=branch_id),
            self._operations_repo.list_branch_jobs(tenant_id=tenant_id, branch_id=branch_id),
            self._purchasing_repo.list_branch_purchase_orders(tenant_id=tenant_id, branch_id=branch_id),
            self._inventory_repo.list_branch_goods_receipts(tenant_id=tenant_id, branch_id=branch_id),
            self._finance_repo.list_branch_purchase_invoices(tenant_id=tenant_id, branch_id=branch_id),
            self._finance_repo.list_branch_supplier_returns(tenant_id=tenant_id, branch_id=branch_id),
            self._finance_repo.list_branch_supplier_payments(tenant_id=tenant_id, branch_id=branch_id),
            self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id),
        )

        purchase_order_lines_by_order_id = await self._purchasing_repo.list_purchase_order_lines_for_orders(
            purchase_order_ids=[purchase_order.id for purchase_order in purchase_orders]
        )
        goods_receipts_by_purchase_order_id = {
            goods_receipt.purchase_order_id: goods_receipt for goods_receipt in goods_receipts
        }
        outstanding_by_purchase_invoice_id = self._build_outstanding_by_purchase_invoice_id(
            purchase_invoices=purchase_invoices,
            supplier_returns=supplier_returns,
            supplier_payments=supplier_payments,
        )
        approved_pending_receipt_orders = [
            purchase_order
            for purchase_order in purchase_orders
            if purchase_order.approval_status == "APPROVED"
            and purchase_order.id not in goods_receipts_by_purchase_order_id
        ]
        recommended_records = self._build_recommendations(
            replenishment_board=replenishment_board,
            restock_board=restock_board,
            purchase_orders=approved_pending_receipt_orders,
            purchase_order_lines_by_order_id=purchase_order_lines_by_order_id,
            branch_catalog_items=branch_catalog_items,
        )
        sales_7d = self._records_in_window(records=sales, date_key="issued_on", as_of_date=as_of_date)
        returns_7d = self._records_in_window(records=sale_returns, date_key="issued_on", as_of_date=as_of_date)
        sales_today = [record for record in sales if str(record["issued_on"]) == as_of_date.isoformat()]
        overdue_supplier_invoice_count = sum(
            1
            for purchase_invoice in purchase_invoices
            if purchase_invoice.due_date < as_of_date
            and outstanding_by_purchase_invoice_id.get(purchase_invoice.id, 0.0) > 0
        )
        queued_operations_job_count = sum(
            1 for job in operations_jobs if job.status in ACTIVE_JOB_STATUSES
        )

        sales_7d_total = round(sum(float(record["grand_total"]) for record in sales_7d), 2)
        returns_7d_total = round(sum(float(record["refund_amount"]) for record in returns_7d), 2)
        sales_today_total = round(sum(float(record["grand_total"]) for record in sales_today), 2)
        average_basket_value_7d = round(
            sales_7d_total / len(sales_7d),
            2,
        ) if sales_7d else 0.0

        return {
            "branch_id": branch.id,
            "branch_name": branch.name,
            "as_of_date": as_of_date.isoformat(),
            "trade": {
                "sales_today_total": sales_today_total,
                "sales_today_count": len(sales_today),
                "sales_7d_total": sales_7d_total,
                "sales_7d_count": len(sales_7d),
                "returns_7d_total": returns_7d_total,
                "returns_7d_count": len(returns_7d),
                "average_basket_value_7d": average_basket_value_7d,
            },
            "workforce": {
                "open_shift_count": sum(1 for record in shift_sessions if record.status == "OPEN"),
                "open_attendance_count": sum(1 for record in attendance_sessions if record.status == "OPEN"),
                "open_cashier_count": sum(1 for record in cashier_sessions if record.status == "OPEN"),
            },
            "operations": {
                "low_stock_count": int(replenishment_board["low_stock_count"]),
                "restock_open_count": int(restock_board["open_count"]),
                "receiving_ready_count": int(receiving_board["ready_count"]),
                "receiving_variance_count": int(receiving_board.get("received_with_variance_count") or 0),
                "stock_count_open_count": int(stock_count_board["open_count"]),
                "expiring_soon_count": int(batch_expiry_report["expiring_soon_count"]),
                "supplier_blocker_count": int(supplier_settlement_blockers["hard_hold_count"]),
                "overdue_supplier_invoice_count": overdue_supplier_invoice_count,
                "queued_operations_job_count": queued_operations_job_count,
            },
            "procurement": {
                "approval_pending_count": int(purchase_approval_report["pending_approval_count"]),
                "approved_pending_receipt_count": len(approved_pending_receipt_orders),
                "approved_pending_receipt_total": round(
                    sum(float(purchase_order.grand_total) for purchase_order in approved_pending_receipt_orders),
                    2,
                ),
                "outstanding_payables_total": round(float(supplier_payables_report["outstanding_total"]), 2),
                "blocked_release_total": round(
                    float(supplier_settlement_blockers["blocked_release_now_total"]),
                    2,
                ),
            },
            "recommendations": recommended_records,
        }

    @staticmethod
    def _records_in_window(
        *,
        records: list[dict[str, object]],
        date_key: str,
        as_of_date,
    ) -> list[dict[str, object]]:
        window_start = as_of_date - timedelta(days=6)
        results: list[dict[str, object]] = []
        for record in records:
            issued_on = record.get(date_key)
            if issued_on is None:
                continue
            if isinstance(issued_on, datetime):
                candidate = issued_on.date()
            elif isinstance(issued_on, date):
                candidate = issued_on
            else:
                candidate = date.fromisoformat(str(issued_on))
            if window_start <= candidate <= as_of_date:
                results.append(record)
        return results

    @staticmethod
    def _build_outstanding_by_purchase_invoice_id(
        *,
        purchase_invoices,
        supplier_returns,
        supplier_payments,
    ) -> dict[str, float]:
        outstanding_by_invoice_id = {
            purchase_invoice.id: round(float(purchase_invoice.grand_total), 2)
            for purchase_invoice in purchase_invoices
        }
        for supplier_return in supplier_returns:
            purchase_invoice_id = supplier_return.purchase_invoice_id
            outstanding_by_invoice_id[purchase_invoice_id] = round(
                outstanding_by_invoice_id.get(purchase_invoice_id, 0.0) - float(supplier_return.grand_total),
                2,
            )
        for supplier_payment in supplier_payments:
            purchase_invoice_id = supplier_payment.purchase_invoice_id
            outstanding_by_invoice_id[purchase_invoice_id] = round(
                outstanding_by_invoice_id.get(purchase_invoice_id, 0.0) - float(supplier_payment.amount),
                2,
            )
        return outstanding_by_invoice_id

    def _build_recommendations(
        self,
        *,
        replenishment_board: dict[str, object],
        restock_board: dict[str, object],
        purchase_orders,
        purchase_order_lines_by_order_id: dict[str, list[object]],
        branch_catalog_items,
    ) -> list[dict[str, object]]:
        replenishment_records = {
            str(record["product_id"]): record for record in replenishment_board["records"]
        }
        open_restock_quantity_by_product_id: dict[str, float] = {}
        for record in restock_board["records"]:
            if str(record["status"]) not in {"OPEN", "PICKED"}:
                continue
            product_id = str(record["product_id"])
            open_restock_quantity_by_product_id[product_id] = round(
                open_restock_quantity_by_product_id.get(product_id, 0.0) + float(record["requested_quantity"]),
                2,
            )

        open_purchase_order_quantity_by_product_id: dict[str, float] = {}
        latest_purchase_unit_cost_by_product_id: dict[str, float] = {}
        for purchase_order in purchase_orders:
            for line in purchase_order_lines_by_order_id.get(purchase_order.id, []):
                product_id = str(line.product_id)
                open_purchase_order_quantity_by_product_id[product_id] = round(
                    open_purchase_order_quantity_by_product_id.get(product_id, 0.0) + float(line.quantity),
                    2,
                )
                latest_purchase_unit_cost_by_product_id[product_id] = round(float(line.unit_cost), 2)

        branch_catalog_items_by_product_id = {
            item.product_id: item for item in branch_catalog_items
        }
        records: list[dict[str, object]] = []
        for product_id, replenishment_record in replenishment_records.items():
            branch_catalog_item = branch_catalog_items_by_product_id.get(product_id)
            if branch_catalog_item is None:
                continue
            if branch_catalog_item.reorder_point is None or branch_catalog_item.target_stock is None:
                continue

            stock_on_hand = round(float(replenishment_record["stock_on_hand"]), 2)
            reorder_point = round(float(branch_catalog_item.reorder_point), 2)
            target_stock = round(float(branch_catalog_item.target_stock), 2)
            if stock_on_hand >= reorder_point:
                continue

            open_restock_quantity = round(open_restock_quantity_by_product_id.get(product_id, 0.0), 2)
            open_purchase_order_quantity = round(open_purchase_order_quantity_by_product_id.get(product_id, 0.0), 2)
            suggested_reorder_quantity = round(float(replenishment_record["suggested_reorder_quantity"]), 2)
            net_recommended_order_quantity = round(
                max(target_stock - stock_on_hand - open_restock_quantity - open_purchase_order_quantity, 0.0),
                2,
            )
            latest_purchase_unit_cost = round(
                latest_purchase_unit_cost_by_product_id.get(product_id, 0.0),
                2,
            )
            estimated_purchase_cost = round(
                net_recommended_order_quantity * latest_purchase_unit_cost,
                2,
            )
            recommendation_status = (
                "ORDER_NOW" if net_recommended_order_quantity > 0 else "IN_FLIGHT_COVERED"
            )
            records.append(
                {
                    "product_id": product_id,
                    "product_name": str(replenishment_record["product_name"]),
                    "sku_code": str(replenishment_record["sku_code"]),
                    "stock_on_hand": stock_on_hand,
                    "reorder_point": reorder_point,
                    "target_stock": target_stock,
                    "suggested_reorder_quantity": suggested_reorder_quantity,
                    "open_restock_quantity": open_restock_quantity,
                    "open_purchase_order_quantity": open_purchase_order_quantity,
                    "net_recommended_order_quantity": net_recommended_order_quantity,
                    "latest_purchase_unit_cost": latest_purchase_unit_cost,
                    "estimated_purchase_cost": estimated_purchase_cost,
                    "recommendation_status": recommendation_status,
                }
            )
        records.sort(
            key=lambda record: (
                0 if record["recommendation_status"] == "ORDER_NOW" else 1,
                -float(record["estimated_purchase_cost"]),
                str(record["product_name"]),
            )
        )
        return records
