from __future__ import annotations

from collections import defaultdict

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    CreditNote,
    CustomerCreditAccount,
    CustomerCreditLedgerEntry,
    CustomerCreditLot,
    CustomerExchangeSnapshot,
    CustomerLoyaltyAccount,
    CustomerLoyaltyLedgerEntry,
    CustomerProfile,
    CustomerSaleReturnSnapshot,
    CustomerSaleSnapshot,
    ExchangeOrder,
    Payment,
    Sale,
    SaleReturn,
    SalesInvoice,
    TenantLoyaltyProgram,
)


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

    async def get_loyalty_program(self, *, tenant_id: str) -> TenantLoyaltyProgram | None:
        statement = select(TenantLoyaltyProgram).where(TenantLoyaltyProgram.tenant_id == tenant_id)
        return await self._session.scalar(statement)

    async def create_loyalty_program(
        self,
        *,
        tenant_id: str,
        program_id: str,
        status: str,
        earn_points_per_currency_unit: float,
        redeem_step_points: int,
        redeem_value_per_step: float,
        minimum_redeem_points: int,
    ) -> TenantLoyaltyProgram:
        record = TenantLoyaltyProgram(
            id=program_id,
            tenant_id=tenant_id,
            status=status,
            earn_points_per_currency_unit=earn_points_per_currency_unit,
            redeem_step_points=redeem_step_points,
            redeem_value_per_step=redeem_value_per_step,
            minimum_redeem_points=minimum_redeem_points,
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

    async def get_credit_account(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> CustomerCreditAccount | None:
        statement = select(CustomerCreditAccount).where(
            CustomerCreditAccount.tenant_id == tenant_id,
            CustomerCreditAccount.customer_profile_id == customer_profile_id,
        )
        return await self._session.scalar(statement)

    async def create_credit_account(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        account_id: str,
    ) -> CustomerCreditAccount:
        record = CustomerCreditAccount(
            id=account_id,
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            available_balance=0.0,
            issued_total=0.0,
            redeemed_total=0.0,
            adjusted_total=0.0,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_loyalty_account(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> CustomerLoyaltyAccount | None:
        statement = select(CustomerLoyaltyAccount).where(
            CustomerLoyaltyAccount.tenant_id == tenant_id,
            CustomerLoyaltyAccount.customer_profile_id == customer_profile_id,
        )
        return await self._session.scalar(statement)

    async def create_loyalty_account(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        account_id: str,
    ) -> CustomerLoyaltyAccount:
        record = CustomerLoyaltyAccount(
            id=account_id,
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            available_points=0,
            earned_total=0,
            redeemed_total=0,
            adjusted_total=0,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_active_credit_lots(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> list[CustomerCreditLot]:
        statement = (
            select(CustomerCreditLot)
            .where(
                CustomerCreditLot.tenant_id == tenant_id,
                CustomerCreditLot.customer_profile_id == customer_profile_id,
                CustomerCreditLot.status == "ACTIVE",
            )
            .order_by(CustomerCreditLot.issued_at.asc(), CustomerCreditLot.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_credit_ledger_entries(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> list[CustomerCreditLedgerEntry]:
        statement = (
            select(CustomerCreditLedgerEntry)
            .where(
                CustomerCreditLedgerEntry.tenant_id == tenant_id,
                CustomerCreditLedgerEntry.customer_profile_id == customer_profile_id,
            )
            .order_by(CustomerCreditLedgerEntry.created_at.asc(), CustomerCreditLedgerEntry.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_loyalty_ledger_entries(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> list[CustomerLoyaltyLedgerEntry]:
        statement = (
            select(CustomerLoyaltyLedgerEntry)
            .where(
                CustomerLoyaltyLedgerEntry.tenant_id == tenant_id,
                CustomerLoyaltyLedgerEntry.customer_profile_id == customer_profile_id,
            )
            .order_by(CustomerLoyaltyLedgerEntry.created_at.asc(), CustomerLoyaltyLedgerEntry.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def create_credit_lot(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        account_id: str,
        lot_id: str,
        branch_id: str | None,
        source_type: str,
        source_reference_id: str | None,
        original_amount: float,
        remaining_amount: float,
        status: str = "ACTIVE",
    ) -> CustomerCreditLot:
        record = CustomerCreditLot(
            id=lot_id,
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account_id,
            branch_id=branch_id,
            source_type=source_type,
            source_reference_id=source_reference_id,
            original_amount=original_amount,
            remaining_amount=remaining_amount,
            status=status,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_credit_ledger_entry(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        account_id: str,
        entry_id: str,
        lot_id: str | None,
        branch_id: str | None,
        entry_type: str,
        source_type: str,
        source_reference_id: str | None,
        amount: float,
        running_balance: float,
        note: str | None,
    ) -> CustomerCreditLedgerEntry:
        record = CustomerCreditLedgerEntry(
            id=entry_id,
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account_id,
            lot_id=lot_id,
            branch_id=branch_id,
            entry_type=entry_type,
            source_type=source_type,
            source_reference_id=source_reference_id,
            amount=amount,
            running_balance=running_balance,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_loyalty_ledger_entry(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        account_id: str,
        entry_id: str,
        branch_id: str | None,
        entry_type: str,
        source_type: str,
        source_reference_id: str | None,
        points_delta: int,
        balance_after: int,
        note: str | None,
    ) -> CustomerLoyaltyLedgerEntry:
        record = CustomerLoyaltyLedgerEntry(
            id=entry_id,
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account_id,
            branch_id=branch_id,
            entry_type=entry_type,
            source_type=source_type,
            source_reference_id=source_reference_id,
            points_delta=points_delta,
            balance_after=balance_after,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record


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
