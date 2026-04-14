from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CreditNote, CustomerExchangeSnapshot, CustomerSaleReturnSnapshot, CustomerSaleSnapshot, ExchangeOrder, Payment, Sale, SaleReturn, SalesInvoice


class CustomerReportingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_sales(
        self,
        *,
        tenant_id: str,
        branch_id: str | None = None,
    ) -> list[CustomerSaleSnapshot]:
        statement = (
            select(Sale, SalesInvoice)
            .join(SalesInvoice, SalesInvoice.sale_id == Sale.id)
            .where(Sale.tenant_id == tenant_id)
        )
        if branch_id:
            statement = statement.where(Sale.branch_id == branch_id)
        statement = statement.order_by(SalesInvoice.issued_on.asc(), SalesInvoice.invoice_number.asc())
        result = await self._session.execute(statement)
        records = result.all()
        sales = [sale for sale, _ in records]
        payments_by_sale_id = await self._list_payments_for_sales(sale_ids=[sale.id for sale in sales])
        return [
            CustomerSaleSnapshot(
                sale=sale,
                invoice=invoice,
                payments=payments_by_sale_id.get(sale.id, []),
            )
            for sale, invoice in records
        ]

    async def list_sale_returns(
        self,
        *,
        tenant_id: str,
        branch_id: str | None = None,
    ) -> list[CustomerSaleReturnSnapshot]:
        statement = (
            select(SaleReturn, CreditNote)
            .join(CreditNote, CreditNote.sale_return_id == SaleReturn.id)
            .where(SaleReturn.tenant_id == tenant_id)
        )
        if branch_id:
            statement = statement.where(SaleReturn.branch_id == branch_id)
        statement = statement.order_by(CreditNote.issued_on.asc(), CreditNote.credit_note_number.asc())
        result = await self._session.execute(statement)
        return [
            CustomerSaleReturnSnapshot(sale_return=sale_return, credit_note=credit_note)
            for sale_return, credit_note in result.all()
        ]

    async def list_exchange_orders(
        self,
        *,
        tenant_id: str,
        branch_id: str | None = None,
    ) -> list[CustomerExchangeSnapshot]:
        statement = select(ExchangeOrder).where(ExchangeOrder.tenant_id == tenant_id)
        if branch_id:
            statement = statement.where(ExchangeOrder.branch_id == branch_id)
        statement = statement.order_by(ExchangeOrder.created_at.asc(), ExchangeOrder.id.asc())
        exchanges = list((await self._session.scalars(statement)).all())
        return [CustomerExchangeSnapshot(exchange_order=exchange) for exchange in exchanges]

    async def _list_payments_for_sales(self, *, sale_ids: list[str]) -> dict[str, list[Payment]]:
        if not sale_ids:
            return {}
        statement = (
            select(Payment)
            .where(Payment.sale_id.in_(sale_ids))
            .order_by(Payment.created_at.asc(), Payment.id.asc())
        )
        grouped: dict[str, list[Payment]] = defaultdict(list)
        for record in (await self._session.scalars(statement)).all():
            grouped[record.sale_id].append(record)
        return dict(grouped)
