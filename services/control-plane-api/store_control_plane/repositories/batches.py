from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BatchExpiryWriteOff, BatchLot
from ..utils import new_id


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_batch_lots_for_goods_receipt(self, *, goods_receipt_id: str) -> list[BatchLot]:
        statement = (
            select(BatchLot)
            .where(BatchLot.goods_receipt_id == goods_receipt_id)
            .order_by(BatchLot.created_at.asc(), BatchLot.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_branch_batch_lots(self, *, tenant_id: str, branch_id: str) -> list[BatchLot]:
        statement = (
            select(BatchLot)
            .where(BatchLot.tenant_id == tenant_id, BatchLot.branch_id == branch_id)
            .order_by(BatchLot.expiry_date.asc(), BatchLot.batch_number.asc(), BatchLot.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_batch_lot(self, *, tenant_id: str, branch_id: str, batch_lot_id: str) -> BatchLot | None:
        statement = select(BatchLot).where(
            BatchLot.tenant_id == tenant_id,
            BatchLot.branch_id == branch_id,
            BatchLot.id == batch_lot_id,
        )
        return await self._session.scalar(statement)

    async def create_batch_lots(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        goods_receipt_id: str,
        lots: list[dict[str, str | float | date]],
    ) -> list[BatchLot]:
        records: list[BatchLot] = []
        for lot in lots:
            record = BatchLot(
                id=new_id(),
                tenant_id=tenant_id,
                branch_id=branch_id,
                goods_receipt_id=goods_receipt_id,
                product_id=str(lot["product_id"]),
                batch_number=str(lot["batch_number"]),
                quantity=float(lot["quantity"]),
                expiry_date=lot["expiry_date"] if isinstance(lot["expiry_date"], date) else date.fromisoformat(str(lot["expiry_date"])),
            )
            self._session.add(record)
            records.append(record)
        await self._session.flush()
        return records

    async def list_write_offs_for_batch_lots(self, *, batch_lot_ids: list[str]) -> dict[str, list[BatchExpiryWriteOff]]:
        if not batch_lot_ids:
            return {}
        statement = (
            select(BatchExpiryWriteOff)
            .where(BatchExpiryWriteOff.batch_lot_id.in_(batch_lot_ids))
            .order_by(BatchExpiryWriteOff.created_at.asc(), BatchExpiryWriteOff.id.asc())
        )
        records = list((await self._session.scalars(statement)).all())
        grouped: dict[str, list[BatchExpiryWriteOff]] = defaultdict(list)
        for record in records:
            grouped[record.batch_lot_id].append(record)
        return dict(grouped)

    async def create_batch_expiry_write_off(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_lot_id: str,
        product_id: str,
        quantity: float,
        reason: str,
    ) -> BatchExpiryWriteOff:
        record = BatchExpiryWriteOff(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_lot_id=batch_lot_id,
            product_id=product_id,
            quantity=quantity,
            reason=reason,
        )
        self._session.add(record)
        await self._session.flush()
        return record
