from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import GiftCardRepository, TenantRepository
from ..utils import new_id


def _normalize_note(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_display_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_gift_card_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


class GiftCardService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._gift_card_repo = GiftCardRepository(session)

    async def list_gift_cards(self, *, tenant_id: str, query: str | None) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        records = await self._gift_card_repo.list_gift_cards(
            tenant_id=tenant_id,
            query=_normalize_gift_card_code(query) or _normalize_display_name(query),
        )
        return {"records": [self._serialize_record(record) for record in records]}

    async def issue_gift_card(
        self,
        *,
        tenant_id: str,
        display_name: str,
        gift_card_code: str,
        initial_amount: float,
        note: str | None,
        branch_id: str | None = None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_name = _normalize_display_name(display_name)
        if normalized_name is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card display name is required")
        normalized_code = _normalize_gift_card_code(gift_card_code)
        if normalized_code is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card code is required")
        if initial_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card amount must be positive")
        existing = await self._gift_card_repo.get_gift_card_by_code(tenant_id=tenant_id, gift_card_code=normalized_code)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Gift card code already exists")
        record = await self._gift_card_repo.create_gift_card(
            tenant_id=tenant_id,
            gift_card_id=new_id(),
            gift_card_code=normalized_code,
            display_name=normalized_name,
        )
        record.available_balance = round(float(initial_amount), 2)
        record.issued_total = round(float(initial_amount), 2)
        record.status = "ACTIVE"
        await self._gift_card_repo.create_gift_card_ledger_entry(
            tenant_id=tenant_id,
            gift_card_id=record.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="ISSUED",
            source_type="MANUAL_ISSUE",
            source_reference_id=None,
            amount=record.available_balance,
            balance_after=record.available_balance,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_gift_card(tenant_id=tenant_id, gift_card_id=record.id)

    async def get_gift_card(self, *, tenant_id: str, gift_card_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        ledger_entries = await self._gift_card_repo.list_gift_card_ledger_entries(
            tenant_id=tenant_id,
            gift_card_id=gift_card_id,
        )
        return self._serialize_summary(record=record, ledger_entries=ledger_entries)

    async def get_gift_card_by_code(self, *, tenant_id: str, gift_card_code: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_code = _normalize_gift_card_code(gift_card_code)
        if normalized_code is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card code is required")
        record = await self._gift_card_repo.get_gift_card_by_code(tenant_id=tenant_id, gift_card_code=normalized_code)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift card not found")
        ledger_entries = await self._gift_card_repo.list_gift_card_ledger_entries(
            tenant_id=tenant_id,
            gift_card_id=record.id,
        )
        return self._serialize_summary(record=record, ledger_entries=ledger_entries)

    async def adjust_gift_card(
        self,
        *,
        tenant_id: str,
        gift_card_id: str,
        amount_delta: float,
        note: str | None,
        branch_id: str | None = None,
    ) -> dict[str, object]:
        if amount_delta == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card adjustment must be non-zero")
        record = await self._require_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        if amount_delta < 0 and abs(amount_delta) > record.available_balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card balance is insufficient")
        record.available_balance = round(record.available_balance + float(amount_delta), 2)
        record.adjusted_total = round(record.adjusted_total + float(amount_delta), 2)
        self._sync_balance_status(record)
        await self._gift_card_repo.create_gift_card_ledger_entry(
            tenant_id=tenant_id,
            gift_card_id=record.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="ADJUSTED",
            source_type="MANUAL_ADJUSTMENT",
            source_reference_id=None,
            amount=round(float(amount_delta), 2),
            balance_after=record.available_balance,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_gift_card(tenant_id=tenant_id, gift_card_id=record.id)

    async def disable_gift_card(self, *, tenant_id: str, gift_card_id: str) -> dict[str, object]:
        record = await self._require_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        record.status = "DISABLED"
        await self._session.flush()
        return await self.get_gift_card(tenant_id=tenant_id, gift_card_id=record.id)

    async def reactivate_gift_card(self, *, tenant_id: str, gift_card_id: str) -> dict[str, object]:
        record = await self._require_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        record.status = "ACTIVE" if record.available_balance > 0 else "DEPLETED"
        await self._session.flush()
        return await self.get_gift_card(tenant_id=tenant_id, gift_card_id=record.id)

    async def preview_redemption(
        self,
        *,
        tenant_id: str,
        gift_card_code: str | None,
        requested_amount: float,
        sale_total: float,
    ) -> dict[str, object]:
        normalized_code = _normalize_gift_card_code(gift_card_code)
        if normalized_code is None or requested_amount <= 0:
            return {"gift_card": None, "applied_amount": 0.0}
        record = await self._gift_card_repo.get_gift_card_by_code(tenant_id=tenant_id, gift_card_code=normalized_code)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift card not found")
        if record.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card is not active")
        if requested_amount > record.available_balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card balance is insufficient")
        applied_amount = round(min(float(requested_amount), max(round(float(sale_total), 2), 0.0)), 2)
        return {
            "gift_card": self.serialize_gift_card_snapshot(record),
            "applied_amount": applied_amount,
        }

    async def redeem_gift_card(
        self,
        *,
        tenant_id: str,
        gift_card_id: str,
        amount: float,
        branch_id: str | None,
        source_reference_id: str,
        note: str | None = None,
    ) -> dict[str, object]:
        if amount <= 0:
            return await self.get_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        record = await self._require_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        if record.status != "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card is not active")
        if amount > record.available_balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card balance is insufficient")
        record.available_balance = round(record.available_balance - float(amount), 2)
        record.redeemed_total = round(record.redeemed_total + float(amount), 2)
        self._sync_balance_status(record)
        await self._gift_card_repo.create_gift_card_ledger_entry(
            tenant_id=tenant_id,
            gift_card_id=record.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="REDEEMED",
            source_type="SALE_REDEMPTION",
            source_reference_id=source_reference_id,
            amount=-round(float(amount), 2),
            balance_after=record.available_balance,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_gift_card(tenant_id=tenant_id, gift_card_id=record.id)

    async def _require_tenant(self, tenant_id: str) -> None:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    async def _require_gift_card(self, *, tenant_id: str, gift_card_id: str):
        await self._require_tenant(tenant_id)
        record = await self._gift_card_repo.get_gift_card(tenant_id=tenant_id, gift_card_id=gift_card_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift card not found")
        return record

    @staticmethod
    def serialize_gift_card_snapshot(record) -> dict[str, object]:
        return {
            "id": record.id,
            "gift_card_code": record.gift_card_code,
            "display_name": record.display_name,
            "status": record.status,
            "available_balance": record.available_balance,
        }

    @staticmethod
    def _serialize_record(record) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "gift_card_code": record.gift_card_code,
            "display_name": record.display_name,
            "available_balance": record.available_balance,
            "issued_total": record.issued_total,
            "redeemed_total": record.redeemed_total,
            "adjusted_total": record.adjusted_total,
            "status": record.status,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def _serialize_summary(self, *, record, ledger_entries) -> dict[str, object]:
        return {
            **self._serialize_record(record),
            "ledger_entries": [
                {
                    "id": entry.id,
                    "entry_type": entry.entry_type,
                    "source_type": entry.source_type,
                    "source_reference_id": entry.source_reference_id,
                    "amount": entry.amount,
                    "balance_after": entry.balance_after,
                    "note": entry.note,
                    "branch_id": entry.branch_id,
                    "created_at": entry.created_at,
                }
                for entry in ledger_entries
            ],
        }

    @staticmethod
    def _sync_balance_status(record) -> None:
        if record.status == "DISABLED":
            return
        record.status = "ACTIVE" if record.available_balance > 0 else "DEPLETED"
