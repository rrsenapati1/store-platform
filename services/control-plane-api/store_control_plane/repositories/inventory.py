from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import GoodsReceipt, GoodsReceiptLine, InventoryLedgerEntry, RestockTaskSession, SerializedInventoryUnit, StockAdjustment, StockCountReviewSession, StockCountSession, TransferOrder
from ..utils import new_id


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def next_branch_goods_receipt_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(GoodsReceipt.id)).where(
            GoodsReceipt.tenant_id == tenant_id,
            GoodsReceipt.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def get_goods_receipt_for_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
    ) -> GoodsReceipt | None:
        statement = select(GoodsReceipt).where(
            GoodsReceipt.tenant_id == tenant_id,
            GoodsReceipt.branch_id == branch_id,
            GoodsReceipt.purchase_order_id == purchase_order_id,
        )
        return await self._session.scalar(statement)

    async def get_goods_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        goods_receipt_id: str,
    ) -> GoodsReceipt | None:
        statement = select(GoodsReceipt).where(
            GoodsReceipt.tenant_id == tenant_id,
            GoodsReceipt.branch_id == branch_id,
            GoodsReceipt.id == goods_receipt_id,
        )
        return await self._session.scalar(statement)

    async def create_goods_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
        supplier_id: str,
        goods_receipt_number: str,
        received_on,
        note: str | None,
        lines: list[dict[str, float | str]],
    ) -> GoodsReceipt:
        goods_receipt = GoodsReceipt(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            goods_receipt_number=goods_receipt_number,
            received_on=received_on,
            note=note,
        )
        self._session.add(goods_receipt)
        await self._session.flush()
        for line in lines:
            self._session.add(
                GoodsReceiptLine(
                    id=new_id(),
                    goods_receipt_id=goods_receipt.id,
                    product_id=str(line["product_id"]),
                    ordered_quantity=float(line["ordered_quantity"]),
                    quantity=float(line["quantity"]),
                    unit_cost=float(line["unit_cost"]),
                    line_total=float(line["line_total"]),
                    discrepancy_note=str(line["discrepancy_note"]) if line.get("discrepancy_note") is not None else None,
                    serial_numbers=list(line.get("serial_numbers") or []),
                )
            )
        await self._session.flush()
        return goods_receipt

    async def create_serialized_inventory_units(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        goods_receipt_id: str,
        goods_receipt_line_id: str,
        serial_numbers: list[str],
    ) -> list[SerializedInventoryUnit]:
        created: list[SerializedInventoryUnit] = []
        for serial_number in serial_numbers:
            record = SerializedInventoryUnit(
                id=new_id(),
                tenant_id=tenant_id,
                branch_id=branch_id,
                product_id=product_id,
                goods_receipt_id=goods_receipt_id,
                goods_receipt_line_id=goods_receipt_line_id,
                serial_number=serial_number,
                status="AVAILABLE",
            )
            self._session.add(record)
            created.append(record)
        await self._session.flush()
        return created

    async def list_available_serialized_units(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        serial_numbers: list[str],
    ) -> list[SerializedInventoryUnit]:
        if not serial_numbers:
            return []
        statement = (
            select(SerializedInventoryUnit)
            .where(
                SerializedInventoryUnit.tenant_id == tenant_id,
                SerializedInventoryUnit.branch_id == branch_id,
                SerializedInventoryUnit.product_id == product_id,
                SerializedInventoryUnit.status == "AVAILABLE",
                SerializedInventoryUnit.serial_number.in_(serial_numbers),
            )
            .order_by(SerializedInventoryUnit.created_at.asc(), SerializedInventoryUnit.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_serialized_units(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        serial_numbers: list[str],
    ) -> list[SerializedInventoryUnit]:
        if not serial_numbers:
            return []
        statement = (
            select(SerializedInventoryUnit)
            .where(
                SerializedInventoryUnit.tenant_id == tenant_id,
                SerializedInventoryUnit.branch_id == branch_id,
                SerializedInventoryUnit.product_id == product_id,
                SerializedInventoryUnit.serial_number.in_(serial_numbers),
            )
            .order_by(SerializedInventoryUnit.created_at.asc(), SerializedInventoryUnit.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def mark_serialized_units_sold(
        self,
        *,
        unit_ids: list[str],
        sale_id: str,
        sale_line_id: str,
    ) -> None:
        if not unit_ids:
            return
        statement = select(SerializedInventoryUnit).where(SerializedInventoryUnit.id.in_(unit_ids))
        records = list((await self._session.scalars(statement)).all())
        for record in records:
            record.status = "SOLD"
            record.sale_id = sale_id
            record.sale_line_id = sale_line_id
        await self._session.flush()

    async def list_branch_goods_receipts(self, *, tenant_id: str, branch_id: str) -> list[GoodsReceipt]:
        statement = (
            select(GoodsReceipt)
            .where(
                GoodsReceipt.tenant_id == tenant_id,
                GoodsReceipt.branch_id == branch_id,
            )
            .order_by(GoodsReceipt.created_at.asc(), GoodsReceipt.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_goods_receipt_lines_for_receipts(self, *, goods_receipt_ids: list[str]) -> dict[str, list[GoodsReceiptLine]]:
        if not goods_receipt_ids:
            return {}
        statement = (
            select(GoodsReceiptLine)
            .where(GoodsReceiptLine.goods_receipt_id.in_(goods_receipt_ids))
            .order_by(GoodsReceiptLine.created_at.asc(), GoodsReceiptLine.id.asc())
        )
        records = list((await self._session.scalars(statement)).all())
        grouped: dict[str, list[GoodsReceiptLine]] = defaultdict(list)
        for record in records:
            grouped[record.goods_receipt_id].append(record)
        return dict(grouped)

    async def create_inventory_ledger_entries(self, *, entries: list[dict[str, float | str]]) -> list[InventoryLedgerEntry]:
        created: list[InventoryLedgerEntry] = []
        for entry in entries:
            record = InventoryLedgerEntry(
                id=new_id(),
                tenant_id=str(entry["tenant_id"]),
                branch_id=str(entry["branch_id"]),
                product_id=str(entry["product_id"]),
                entry_type=str(entry["entry_type"]),
                quantity=float(entry["quantity"]),
                reference_type=str(entry["reference_type"]),
                reference_id=str(entry["reference_id"]),
            )
            self._session.add(record)
            created.append(record)
        await self._session.flush()
        return created

    async def list_branch_inventory_ledger(self, *, tenant_id: str, branch_id: str) -> list[InventoryLedgerEntry]:
        statement = (
            select(InventoryLedgerEntry)
            .where(
                InventoryLedgerEntry.tenant_id == tenant_id,
                InventoryLedgerEntry.branch_id == branch_id,
            )
            .order_by(InventoryLedgerEntry.created_at.asc(), InventoryLedgerEntry.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def stock_on_hand(self, *, tenant_id: str, branch_id: str, product_id: str) -> float:
        statement = select(func.coalesce(func.sum(InventoryLedgerEntry.quantity), 0.0)).where(
            InventoryLedgerEntry.tenant_id == tenant_id,
            InventoryLedgerEntry.branch_id == branch_id,
            InventoryLedgerEntry.product_id == product_id,
        )
        quantity = await self._session.scalar(statement)
        return float(quantity or 0.0)

    async def create_stock_adjustment(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        quantity_delta: float,
        reason: str,
        note: str | None,
    ) -> StockAdjustment:
        record = StockAdjustment(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            quantity_delta=quantity_delta,
            reason=reason,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_stock_count_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        counted_quantity: float,
        expected_quantity: float,
        variance_quantity: float,
        note: str | None,
    ) -> StockCountSession:
        record = StockCountSession(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            counted_quantity=counted_quantity,
            expected_quantity=expected_quantity,
            variance_quantity=variance_quantity,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def next_branch_stock_count_review_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(StockCountReviewSession.id)).where(
            StockCountReviewSession.tenant_id == tenant_id,
            StockCountReviewSession.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def create_stock_count_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        session_number: str,
        expected_quantity: float,
        note: str | None,
    ) -> StockCountReviewSession:
        record = StockCountReviewSession(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            session_number=session_number,
            status="OPEN",
            expected_quantity=expected_quantity,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_stock_count_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        stock_count_session_id: str,
    ) -> StockCountReviewSession | None:
        statement = select(StockCountReviewSession).where(
            StockCountReviewSession.tenant_id == tenant_id,
            StockCountReviewSession.branch_id == branch_id,
            StockCountReviewSession.id == stock_count_session_id,
        )
        return await self._session.scalar(statement)

    async def list_branch_stock_count_review_sessions(self, *, tenant_id: str, branch_id: str) -> list[StockCountReviewSession]:
        statement = (
            select(StockCountReviewSession)
            .where(
                StockCountReviewSession.tenant_id == tenant_id,
                StockCountReviewSession.branch_id == branch_id,
            )
            .order_by(StockCountReviewSession.created_at.desc(), StockCountReviewSession.id.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def next_branch_restock_task_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(RestockTaskSession.id)).where(
            RestockTaskSession.tenant_id == tenant_id,
            RestockTaskSession.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def create_restock_task_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
        task_number: str,
        stock_on_hand_snapshot: float,
        reorder_point_snapshot: float,
        target_stock_snapshot: float,
        suggested_quantity_snapshot: float,
        requested_quantity: float,
        source_posture: str,
        note: str | None,
    ) -> RestockTaskSession:
        record = RestockTaskSession(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            task_number=task_number,
            status="OPEN",
            stock_on_hand_snapshot=stock_on_hand_snapshot,
            reorder_point_snapshot=reorder_point_snapshot,
            target_stock_snapshot=target_stock_snapshot,
            suggested_quantity_snapshot=suggested_quantity_snapshot,
            requested_quantity=requested_quantity,
            source_posture=source_posture,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_restock_task_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        restock_task_id: str,
    ) -> RestockTaskSession | None:
        statement = select(RestockTaskSession).where(
            RestockTaskSession.tenant_id == tenant_id,
            RestockTaskSession.branch_id == branch_id,
            RestockTaskSession.id == restock_task_id,
        )
        return await self._session.scalar(statement)

    async def list_branch_restock_task_sessions(self, *, tenant_id: str, branch_id: str) -> list[RestockTaskSession]:
        statement = (
            select(RestockTaskSession)
            .where(
                RestockTaskSession.tenant_id == tenant_id,
                RestockTaskSession.branch_id == branch_id,
            )
            .order_by(RestockTaskSession.created_at.desc(), RestockTaskSession.id.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_active_restock_task_for_product(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        product_id: str,
    ) -> RestockTaskSession | None:
        statement = (
            select(RestockTaskSession)
            .where(
                RestockTaskSession.tenant_id == tenant_id,
                RestockTaskSession.branch_id == branch_id,
                RestockTaskSession.product_id == product_id,
                RestockTaskSession.status.in_(("OPEN", "PICKED")),
            )
            .order_by(RestockTaskSession.created_at.desc(), RestockTaskSession.id.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def next_branch_transfer_sequence(self, *, tenant_id: str, source_branch_id: str) -> int:
        statement = select(func.count(TransferOrder.id)).where(
            TransferOrder.tenant_id == tenant_id,
            TransferOrder.source_branch_id == source_branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def create_transfer_order(
        self,
        *,
        tenant_id: str,
        source_branch_id: str,
        destination_branch_id: str,
        product_id: str,
        transfer_number: str,
        quantity: float,
        note: str | None,
    ) -> TransferOrder:
        record = TransferOrder(
            id=new_id(),
            tenant_id=tenant_id,
            source_branch_id=source_branch_id,
            destination_branch_id=destination_branch_id,
            product_id=product_id,
            transfer_number=transfer_number,
            quantity=quantity,
            status="COMPLETED",
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_branch_transfers(self, *, tenant_id: str, branch_id: str) -> list[TransferOrder]:
        statement = (
            select(TransferOrder)
            .where(
                TransferOrder.tenant_id == tenant_id,
                or_(
                    TransferOrder.source_branch_id == branch_id,
                    TransferOrder.destination_branch_id == branch_id,
                ),
            )
            .order_by(TransferOrder.created_at.asc(), TransferOrder.id.asc())
        )
        return list((await self._session.scalars(statement)).all())
