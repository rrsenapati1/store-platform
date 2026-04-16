from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CustomerProfileRepository
from ..utils import new_id
from .customer_profiles import CustomerProfileService


def _normalize_note(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class StoreCreditService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._profile_service = CustomerProfileService(session)
        self._profile_repo = CustomerProfileRepository(session)

    async def get_customer_store_credit(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> dict[str, object]:
        await self._profile_service.get_customer_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._profile_repo.get_credit_account(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        if account is None:
            return self._serialize_summary(
                customer_profile_id=customer_profile_id,
                account=None,
                lots=[],
                ledger_entries=[],
            )
        lots = await self._profile_repo.list_active_credit_lots(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        ledger_entries = await self._profile_repo.list_credit_ledger_entries(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        return self._serialize_summary(
            customer_profile_id=customer_profile_id,
            account=account,
            lots=lots,
            ledger_entries=ledger_entries,
        )

    async def issue_customer_store_credit(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        amount: float,
        note: str | None,
        branch_id: str | None = None,
        source_type: str = "MANUAL_ISSUE",
        source_reference_id: str | None = None,
    ) -> dict[str, object]:
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store credit amount must be positive")
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        lot = await self._profile_repo.create_credit_lot(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            lot_id=new_id(),
            branch_id=branch_id,
            source_type=source_type,
            source_reference_id=source_reference_id,
            original_amount=amount,
            remaining_amount=amount,
        )
        account.available_balance += amount
        account.issued_total += amount
        await self._profile_repo.create_credit_ledger_entry(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            entry_id=new_id(),
            lot_id=lot.id,
            branch_id=branch_id,
            entry_type="ISSUED",
            source_type=source_type,
            source_reference_id=source_reference_id,
            amount=amount,
            running_balance=account.available_balance,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_customer_store_credit(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def redeem_customer_store_credit(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        amount: float,
        branch_id: str | None,
        source_reference_id: str,
        note: str | None = None,
    ) -> dict[str, object]:
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store credit redemption must be positive")
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if amount > account.available_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer store credit balance is insufficient",
            )
        remaining_to_redeem = amount
        for lot in await self._profile_repo.list_active_credit_lots(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        ):
            if remaining_to_redeem <= 0:
                break
            if lot.remaining_amount <= 0:
                continue
            redeemed_from_lot = min(lot.remaining_amount, remaining_to_redeem)
            lot.remaining_amount -= redeemed_from_lot
            remaining_to_redeem = round(remaining_to_redeem - redeemed_from_lot, 2)
            if lot.remaining_amount <= 0:
                lot.remaining_amount = 0.0
                lot.status = "DEPLETED"
            account.available_balance = round(account.available_balance - redeemed_from_lot, 2)
            account.redeemed_total = round(account.redeemed_total + redeemed_from_lot, 2)
            await self._profile_repo.create_credit_ledger_entry(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                account_id=account.id,
                entry_id=new_id(),
                lot_id=lot.id,
                branch_id=branch_id,
                entry_type="REDEEMED",
                source_type="SALE_REDEMPTION",
                source_reference_id=source_reference_id,
                amount=-redeemed_from_lot,
                running_balance=account.available_balance,
                note=_normalize_note(note),
            )
        if remaining_to_redeem > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer store credit balance is insufficient",
            )
        await self._session.flush()
        return await self.get_customer_store_credit(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def adjust_customer_store_credit(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        amount_delta: float,
        note: str | None,
        branch_id: str | None = None,
    ) -> dict[str, object]:
        if amount_delta == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store credit adjustment must be non-zero")
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        normalized_note = _normalize_note(note)
        lot_id: str | None = None
        if amount_delta > 0:
            lot = await self._profile_repo.create_credit_lot(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
                account_id=account.id,
                lot_id=new_id(),
                branch_id=branch_id,
                source_type="MANUAL_ADJUSTMENT",
                source_reference_id=None,
                original_amount=amount_delta,
                remaining_amount=amount_delta,
            )
            lot_id = lot.id
        else:
            remaining_to_remove = abs(amount_delta)
            if remaining_to_remove > account.available_balance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer store credit balance is insufficient for adjustment",
                )
            lots = await self._profile_repo.list_active_credit_lots(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
            )
            for lot in lots:
                if remaining_to_remove <= 0:
                    break
                if lot.remaining_amount <= 0:
                    continue
                consumed = min(lot.remaining_amount, remaining_to_remove)
                lot.remaining_amount -= consumed
                remaining_to_remove -= consumed
                if lot.remaining_amount <= 0:
                    lot.remaining_amount = 0.0
                    lot.status = "DEPLETED"

        account.available_balance += amount_delta
        account.adjusted_total += amount_delta
        await self._profile_repo.create_credit_ledger_entry(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            entry_id=new_id(),
            lot_id=lot_id,
            branch_id=branch_id,
            entry_type="ADJUSTED",
            source_type="MANUAL_ADJUSTMENT",
            source_reference_id=None,
            amount=amount_delta,
            running_balance=account.available_balance,
            note=normalized_note,
        )
        await self._session.flush()
        return await self.get_customer_store_credit(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def _get_or_create_account(self, *, tenant_id: str, customer_profile_id: str):
        account = await self._profile_repo.get_credit_account(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        if account is not None:
            return account
        return await self._profile_repo.create_credit_account(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=new_id(),
        )

    @staticmethod
    def _serialize_summary(
        *,
        customer_profile_id: str,
        account,
        lots,
        ledger_entries,
    ) -> dict[str, object]:
        return {
            "customer_profile_id": customer_profile_id,
            "available_balance": 0.0 if account is None else account.available_balance,
            "issued_total": 0.0 if account is None else account.issued_total,
            "redeemed_total": 0.0 if account is None else account.redeemed_total,
            "adjusted_total": 0.0 if account is None else account.adjusted_total,
            "lots": [
                {
                    "id": record.id,
                    "source_type": record.source_type,
                    "source_reference_id": record.source_reference_id,
                    "original_amount": record.original_amount,
                    "remaining_amount": record.remaining_amount,
                    "status": record.status,
                    "issued_at": record.issued_at,
                    "branch_id": record.branch_id,
                }
                for record in lots
            ],
            "ledger_entries": [
                {
                    "id": record.id,
                    "entry_type": record.entry_type,
                    "source_type": record.source_type,
                    "source_reference_id": record.source_reference_id,
                    "amount": record.amount,
                    "running_balance": record.running_balance,
                    "note": record.note,
                    "lot_id": record.lot_id,
                    "branch_id": record.branch_id,
                    "created_at": record.created_at,
                }
                for record in ledger_entries
            ],
        }
