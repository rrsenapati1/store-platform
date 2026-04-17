from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import GiftCard, GiftCardLedgerEntry


class GiftCardRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_gift_cards(
        self,
        *,
        tenant_id: str,
        query: str | None,
    ) -> list[GiftCard]:
        statement = select(GiftCard).where(GiftCard.tenant_id == tenant_id)
        if query:
            pattern = f"%{query.lower()}%"
            statement = statement.where(
                or_(
                    GiftCard.gift_card_code.ilike(pattern),
                    GiftCard.display_name.ilike(pattern),
                )
            )
        statement = statement.order_by(GiftCard.created_at.asc(), GiftCard.id.asc())
        return list((await self._session.scalars(statement)).all())

    async def get_gift_card(self, *, tenant_id: str, gift_card_id: str) -> GiftCard | None:
        statement = select(GiftCard).where(
            GiftCard.tenant_id == tenant_id,
            GiftCard.id == gift_card_id,
        )
        return await self._session.scalar(statement)

    async def get_gift_card_by_code(self, *, tenant_id: str, gift_card_code: str) -> GiftCard | None:
        statement = select(GiftCard).where(
            GiftCard.tenant_id == tenant_id,
            GiftCard.gift_card_code == gift_card_code,
        )
        return await self._session.scalar(statement)

    async def create_gift_card(
        self,
        *,
        tenant_id: str,
        gift_card_id: str,
        gift_card_code: str,
        display_name: str,
    ) -> GiftCard:
        record = GiftCard(
            id=gift_card_id,
            tenant_id=tenant_id,
            gift_card_code=gift_card_code,
            display_name=display_name,
            available_balance=0.0,
            issued_total=0.0,
            redeemed_total=0.0,
            adjusted_total=0.0,
            status="ACTIVE",
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_gift_card_ledger_entries(
        self,
        *,
        tenant_id: str,
        gift_card_id: str,
    ) -> list[GiftCardLedgerEntry]:
        statement = (
            select(GiftCardLedgerEntry)
            .where(
                GiftCardLedgerEntry.tenant_id == tenant_id,
                GiftCardLedgerEntry.gift_card_id == gift_card_id,
            )
            .order_by(GiftCardLedgerEntry.created_at.asc(), GiftCardLedgerEntry.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def create_gift_card_ledger_entry(
        self,
        *,
        tenant_id: str,
        gift_card_id: str,
        entry_id: str,
        branch_id: str | None,
        entry_type: str,
        source_type: str,
        source_reference_id: str | None,
        amount: float,
        balance_after: float,
        note: str | None,
    ) -> GiftCardLedgerEntry:
        record = GiftCardLedgerEntry(
            id=entry_id,
            tenant_id=tenant_id,
            gift_card_id=gift_card_id,
            branch_id=branch_id,
            entry_type=entry_type,
            source_type=source_type,
            source_reference_id=source_reference_id,
            amount=amount,
            balance_after=balance_after,
            note=note,
        )
        self._session.add(record)
        await self._session.flush()
        return record
