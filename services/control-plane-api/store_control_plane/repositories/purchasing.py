from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PurchaseOrder, PurchaseOrderLine, Supplier
from ..utils import new_id


class PurchasingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_supplier(
        self,
        *,
        tenant_id: str,
        name: str,
        gstin: str | None,
        payment_terms_days: int,
    ) -> Supplier:
        supplier = Supplier(
            id=new_id(),
            tenant_id=tenant_id,
            name=name,
            gstin=gstin,
            payment_terms_days=payment_terms_days,
            status="ACTIVE",
        )
        self._session.add(supplier)
        await self._session.flush()
        return supplier

    async def list_suppliers(self, *, tenant_id: str) -> list[Supplier]:
        statement = (
            select(Supplier)
            .where(Supplier.tenant_id == tenant_id)
            .order_by(Supplier.created_at.asc(), Supplier.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_supplier(self, *, tenant_id: str, supplier_id: str) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.tenant_id == tenant_id,
            Supplier.id == supplier_id,
        )
        return await self._session.scalar(statement)

    async def next_branch_purchase_order_sequence(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.branch_id == branch_id,
        )
        count = await self._session.scalar(statement)
        return int(count or 0) + 1

    async def create_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        supplier_id: str,
        purchase_order_number: str,
        subtotal: float,
        tax_total: float,
        grand_total: float,
        lines: list[dict[str, float | str]],
    ) -> PurchaseOrder:
        purchase_order = PurchaseOrder(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            purchase_order_number=purchase_order_number,
            approval_status="NOT_REQUESTED",
            subtotal=subtotal,
            tax_total=tax_total,
            grand_total=grand_total,
        )
        self._session.add(purchase_order)
        await self._session.flush()
        for line in lines:
            self._session.add(
                PurchaseOrderLine(
                    id=new_id(),
                    purchase_order_id=purchase_order.id,
                    product_id=str(line["product_id"]),
                    quantity=float(line["quantity"]),
                    unit_cost=float(line["unit_cost"]),
                    gst_rate=float(line["gst_rate"]),
                    line_total=float(line["line_total"]),
                    tax_total=float(line["tax_total"]),
                )
            )
        await self._session.flush()
        return purchase_order

    async def list_branch_purchase_orders(self, *, tenant_id: str, branch_id: str) -> list[PurchaseOrder]:
        statement = (
            select(PurchaseOrder)
            .where(
                PurchaseOrder.tenant_id == tenant_id,
                PurchaseOrder.branch_id == branch_id,
            )
            .order_by(PurchaseOrder.created_at.asc(), PurchaseOrder.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_purchase_order(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
    ) -> PurchaseOrder | None:
        statement = select(PurchaseOrder).where(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.branch_id == branch_id,
            PurchaseOrder.id == purchase_order_id,
        )
        return await self._session.scalar(statement)

    async def list_purchase_order_lines_for_orders(
        self,
        *,
        purchase_order_ids: list[str],
    ) -> dict[str, list[PurchaseOrderLine]]:
        if not purchase_order_ids:
            return {}
        statement = (
            select(PurchaseOrderLine)
            .where(PurchaseOrderLine.purchase_order_id.in_(purchase_order_ids))
            .order_by(PurchaseOrderLine.created_at.asc(), PurchaseOrderLine.id.asc())
        )
        records = list((await self._session.scalars(statement)).all())
        lines_by_order_id: dict[str, list[PurchaseOrderLine]] = {}
        for record in records:
            lines_by_order_id.setdefault(record.purchase_order_id, []).append(record)
        return lines_by_order_id
