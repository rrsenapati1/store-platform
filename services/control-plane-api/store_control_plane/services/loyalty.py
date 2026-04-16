from __future__ import annotations

from math import floor

from fastapi import HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CustomerProfileRepository
from ..utils import new_id
from .customer_profiles import CustomerProfileService


def _normalize_note(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class LoyaltyService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._profile_service = CustomerProfileService(session)
        self._profile_repo = CustomerProfileRepository(session)

    async def get_loyalty_program(self, *, tenant_id: str) -> dict[str, object]:
        record = await self._profile_repo.get_loyalty_program(tenant_id=tenant_id)
        if record is None:
            return self._serialize_program(program=None)
        return self._serialize_program(program=record)

    async def update_loyalty_program(
        self,
        *,
        tenant_id: str,
        status: str,
        earn_points_per_currency_unit: float,
        redeem_step_points: int,
        redeem_value_per_step: float,
        minimum_redeem_points: int,
    ) -> dict[str, object]:
        normalized_status = status.strip().upper()
        if normalized_status not in {"ACTIVE", "DISABLED"}:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid loyalty program status")
        if earn_points_per_currency_unit < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Earn points per currency unit must be non-negative",
            )
        if redeem_step_points <= 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Redeem step points must be greater than zero",
            )
        if redeem_value_per_step < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Redeem value per step must be non-negative",
            )
        if minimum_redeem_points < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Minimum redeem points must be non-negative",
            )

        record = await self._profile_repo.get_loyalty_program(tenant_id=tenant_id)
        if record is None:
            record = await self._profile_repo.create_loyalty_program(
                tenant_id=tenant_id,
                program_id=new_id(),
                status=normalized_status,
                earn_points_per_currency_unit=float(earn_points_per_currency_unit),
                redeem_step_points=int(redeem_step_points),
                redeem_value_per_step=round(float(redeem_value_per_step), 2),
                minimum_redeem_points=int(minimum_redeem_points),
            )
        else:
            record.status = normalized_status
            record.earn_points_per_currency_unit = float(earn_points_per_currency_unit)
            record.redeem_step_points = int(redeem_step_points)
            record.redeem_value_per_step = round(float(redeem_value_per_step), 2)
            record.minimum_redeem_points = int(minimum_redeem_points)
        await self._session.flush()
        return self._serialize_program(program=record)

    async def get_customer_loyalty(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> dict[str, object]:
        await self._profile_service.get_customer_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._profile_repo.get_loyalty_account(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        ledger_entries = []
        if account is not None:
            ledger_entries = await self._profile_repo.list_loyalty_ledger_entries(
                tenant_id=tenant_id,
                customer_profile_id=customer_profile_id,
            )
        return self._serialize_summary(
            customer_profile_id=customer_profile_id,
            account=account,
            ledger_entries=ledger_entries,
        )

    async def adjust_customer_loyalty(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        points_delta: int,
        note: str | None,
        branch_id: str | None = None,
    ) -> dict[str, object]:
        if points_delta == 0:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Loyalty adjustment must be non-zero")
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if points_delta < 0 and abs(points_delta) > account.available_points:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Customer loyalty balance is insufficient for adjustment",
            )
        account.available_points += int(points_delta)
        account.adjusted_total += int(points_delta)
        await self._profile_repo.create_loyalty_ledger_entry(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="ADJUSTED",
            source_type="MANUAL_ADJUSTMENT",
            source_reference_id=None,
            points_delta=int(points_delta),
            balance_after=account.available_points,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def calculate_sale_redemption(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        points_to_redeem: int,
        sale_total: float,
    ) -> dict[str, object]:
        if points_to_redeem <= 0:
            return {"points_to_redeem": 0, "discount_amount": 0.0}
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        program = await self._profile_repo.get_loyalty_program(tenant_id=tenant_id)
        if program is None or program.status != "ACTIVE":
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Loyalty program is not active")
        if points_to_redeem < program.minimum_redeem_points:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Loyalty redemption does not meet the minimum points requirement",
            )
        if points_to_redeem % program.redeem_step_points != 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Loyalty redemption must match the configured redemption step",
            )
        if program.redeem_value_per_step <= 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Loyalty program redemption value is not configured",
            )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if points_to_redeem > account.available_points:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Customer loyalty balance is insufficient",
            )
        discount_amount = round(
            (points_to_redeem / program.redeem_step_points) * program.redeem_value_per_step,
            2,
        )
        if discount_amount > round(float(sale_total), 2):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Loyalty redemption cannot exceed sale total",
            )
        return {
            "points_to_redeem": int(points_to_redeem),
            "discount_amount": discount_amount,
        }

    async def redeem_customer_loyalty(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        points_to_redeem: int,
        branch_id: str | None,
        source_reference_id: str,
        note: str | None = None,
    ) -> dict[str, object]:
        if points_to_redeem <= 0:
            return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if points_to_redeem > account.available_points:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Customer loyalty balance is insufficient",
            )
        account.available_points -= int(points_to_redeem)
        account.redeemed_total += int(points_to_redeem)
        await self._profile_repo.create_loyalty_ledger_entry(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="REDEEMED",
            source_type="SALE_REDEMPTION",
            source_reference_id=source_reference_id,
            points_delta=-int(points_to_redeem),
            balance_after=account.available_points,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def earn_customer_loyalty(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        eligible_sale_amount: float,
        branch_id: str | None,
        source_reference_id: str,
        note: str | None = None,
    ) -> dict[str, object]:
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        points_to_earn = await self.calculate_sale_earn_points(
            tenant_id=tenant_id,
            eligible_sale_amount=eligible_sale_amount,
        )
        if points_to_earn <= 0:
            return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        account.available_points += int(points_to_earn)
        account.earned_total += int(points_to_earn)
        await self._profile_repo.create_loyalty_ledger_entry(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="EARNED",
            source_type="SALE_EARN",
            source_reference_id=source_reference_id,
            points_delta=int(points_to_earn),
            balance_after=account.available_points,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def reverse_sale_loyalty(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
        points_delta: int,
        branch_id: str | None,
        source_reference_id: str,
        note: str | None,
    ) -> dict[str, object]:
        if points_delta == 0:
            return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        await self._profile_service.require_active_profile(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        account = await self._get_or_create_account(tenant_id=tenant_id, customer_profile_id=customer_profile_id)
        if points_delta < 0 and abs(points_delta) > account.available_points:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Customer loyalty balance is insufficient for reversal",
            )
        account.available_points += int(points_delta)
        await self._profile_repo.create_loyalty_ledger_entry(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=account.id,
            entry_id=new_id(),
            branch_id=branch_id,
            entry_type="REVERSED",
            source_type="RETURN_REVERSAL",
            source_reference_id=source_reference_id,
            points_delta=int(points_delta),
            balance_after=account.available_points,
            note=_normalize_note(note),
        )
        await self._session.flush()
        return await self.get_customer_loyalty(tenant_id=tenant_id, customer_profile_id=customer_profile_id)

    async def calculate_sale_earn_points(
        self,
        *,
        tenant_id: str,
        eligible_sale_amount: float,
    ) -> int:
        program = await self._profile_repo.get_loyalty_program(tenant_id=tenant_id)
        if program is None or program.status != "ACTIVE":
            return 0
        if eligible_sale_amount <= 0 or program.earn_points_per_currency_unit <= 0:
            return 0
        return int(floor(round(float(eligible_sale_amount), 2) * program.earn_points_per_currency_unit))

    async def _get_or_create_account(self, *, tenant_id: str, customer_profile_id: str):
        account = await self._profile_repo.get_loyalty_account(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
        )
        if account is not None:
            return account
        return await self._profile_repo.create_loyalty_account(
            tenant_id=tenant_id,
            customer_profile_id=customer_profile_id,
            account_id=new_id(),
        )

    @staticmethod
    def _serialize_program(*, program) -> dict[str, object]:
        if program is None:
            return {
                "status": "DISABLED",
                "earn_points_per_currency_unit": 0.0,
                "redeem_step_points": 100,
                "redeem_value_per_step": 0.0,
                "minimum_redeem_points": 0,
            }
        return {
            "status": program.status,
            "earn_points_per_currency_unit": program.earn_points_per_currency_unit,
            "redeem_step_points": program.redeem_step_points,
            "redeem_value_per_step": program.redeem_value_per_step,
            "minimum_redeem_points": program.minimum_redeem_points,
        }

    @staticmethod
    def _serialize_summary(*, customer_profile_id: str, account, ledger_entries) -> dict[str, object]:
        return {
            "customer_profile_id": customer_profile_id,
            "available_points": 0 if account is None else account.available_points,
            "earned_total": 0 if account is None else account.earned_total,
            "redeemed_total": 0 if account is None else account.redeemed_total,
            "adjusted_total": 0 if account is None else account.adjusted_total,
            "ledger_entries": [
                {
                    "id": record.id,
                    "entry_type": record.entry_type,
                    "source_type": record.source_type,
                    "source_reference_id": record.source_reference_id,
                    "points_delta": record.points_delta,
                    "balance_after": record.balance_after,
                    "note": record.note,
                    "branch_id": record.branch_id,
                    "created_at": record.created_at,
                }
                for record in ledger_entries
            ],
        }
