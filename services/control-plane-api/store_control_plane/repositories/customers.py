from __future__ import annotations

from collections import defaultdict

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CreditNote, CustomerExchangeSnapshot, CustomerProfile, CustomerSaleReturnSnapshot, CustomerSaleSnapshot, ExchangeOrder, Payment, Sale, SaleReturn, SalesInvoice


class CustomerProfileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_profiles(
        self,
        *,
        tenant_id: str,
        query: str | None = None,
        status: str | None = None,
    ) -> list[CustomerProfile]:
        statement = select(CustomerProfile).where(CustomerProfile.tenant_id == tenant_id)
        if status is not None:
            statement = statement.where(CustomerProfile.status == status)
        if query:
            pattern = f"%{query.lower()}%"
            statement = statement.where(
                or_(
                    CustomerProfile.full_name.ilike(pattern),
                    CustomerProfile.phone.ilike(pattern),
                    CustomerProfile.email.ilike(pattern),
                    CustomerProfile.gstin.ilike(pattern),
                )
            )
        statement = statement.order_by(CustomerProfile.full_name.asc(), CustomerProfile.id.asc())
        return list((await self._session.scalars(statement)).all())

    async def get_profile(self, *, tenant_id: str, customer_profile_id: str) -> CustomerProfile | None:
        statement = select(CustomerProfile).where(
            CustomerProfile.tenant_id == tenant_id,
            CustomerProfile.id == customer_profile_id,
        )
        return await self._session.scalar(statement)

    async def get_profile_by_gstin(self, *, tenant_id: str, gstin: str) -> CustomerProfile | None:
        statement = select(CustomerProfile).where(
            CustomerProfile.tenant_id == tenant_id,
            CustomerProfile.gstin == gstin,
        )
        return await self._session.scalar(statement)

    async def create_profile(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        full_name: str,
        phone: str | None,
        email: str | None,
        gstin: str | None,
        default_note: str | None,
        tags: list[str],
        status: str = "ACTIVE",
    ) -> CustomerProfile:
        record = CustomerProfile(
            id=customer_profile_id,
            tenant_id=tenant_id,
            full_name=full_name,
            phone=phone,
            email=email,
            gstin=gstin,
            default_note=default_note,
            tags=tags,
            status=status,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_profiles_by_ids(
        self,
        *,
        tenant_id: str,
        customer_profile_ids: list[str],
    ) -> dict[str, CustomerProfile]:
        if not customer_profile_ids:
            return {}
        statement = select(CustomerProfile).where(
            CustomerProfile.tenant_id == tenant_id,
            CustomerProfile.id.in_(customer_profile_ids),
        )
        records = list((await self._session.scalars(statement)).all())
        return {record.id: record for record in records}


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
