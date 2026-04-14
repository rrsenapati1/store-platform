from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import GoodsReceipt, GoodsReceiptLine, InventoryLedgerEntry, StockAdjustment, StockCountSession, TransferOrder
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
        )
        self._session.add(goods_receipt)
        await self._session.flush()
        for line in lines:
            self._session.add(
                GoodsReceiptLine(
                    id=new_id(),
                    goods_receipt_id=goods_receipt.id,
                    product_id=str(line["product_id"]),
                    quantity=float(line["quantity"]),
                    unit_cost=float(line["unit_cost"]),
                    line_total=float(line["line_total"]),
                )
            )
        await self._session.flush()
        return goods_receipt

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
