from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CustomerVoucherAssignment, PromotionCampaign, PromotionCode


class PromotionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_campaigns(self, *, tenant_id: str) -> list[PromotionCampaign]:
        statement = (
            select(PromotionCampaign)
            .where(PromotionCampaign.tenant_id == tenant_id)
            .order_by(PromotionCampaign.created_at.asc(), PromotionCampaign.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_campaign(self, *, tenant_id: str, campaign_id: str) -> PromotionCampaign | None:
        statement = select(PromotionCampaign).where(
            PromotionCampaign.tenant_id == tenant_id,
            PromotionCampaign.id == campaign_id,
        )
        return await self._session.scalar(statement)

    async def create_campaign(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        name: str,
        status: str,
        trigger_mode: str,
        scope: str,
        discount_type: str,
        discount_value: float,
        priority: int,
        stacking_rule: str,
        minimum_order_amount: float | None,
        maximum_discount_amount: float | None,
        redemption_limit_total: int | None,
        target_product_ids: list[str] | None,
        target_category_codes: list[str] | None,
    ) -> PromotionCampaign:
        record = PromotionCampaign(
            id=campaign_id,
            tenant_id=tenant_id,
            name=name,
            status=status,
            trigger_mode=trigger_mode,
            scope=scope,
            discount_type=discount_type,
            discount_value=discount_value,
            priority=priority,
            stacking_rule=stacking_rule,
            minimum_order_amount=minimum_order_amount,
            maximum_discount_amount=maximum_discount_amount,
            redemption_limit_total=redemption_limit_total,
            redemption_count=0,
            target_product_ids=target_product_ids,
            target_category_codes=target_category_codes,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_codes_for_campaign(self, *, tenant_id: str, campaign_id: str) -> list[PromotionCode]:
        statement = (
            select(PromotionCode)
            .where(
                PromotionCode.tenant_id == tenant_id,
                PromotionCode.campaign_id == campaign_id,
            )
            .order_by(PromotionCode.created_at.asc(), PromotionCode.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_code_by_value(self, *, tenant_id: str, code: str) -> PromotionCode | None:
        statement = select(PromotionCode).where(
            PromotionCode.tenant_id == tenant_id,
            PromotionCode.code == code,
        )
        return await self._session.scalar(statement)

    async def get_code_by_id(self, *, tenant_id: str, promotion_code_id: str) -> PromotionCode | None:
        statement = select(PromotionCode).where(
            PromotionCode.tenant_id == tenant_id,
            PromotionCode.id == promotion_code_id,
        )
        return await self._session.scalar(statement)

    async def create_code(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        promotion_code_id: str,
        code: str,
        status: str,
        redemption_limit_per_code: int | None,
    ) -> PromotionCode:
        record = PromotionCode(
            id=promotion_code_id,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            code=code,
            status=status,
            redemption_limit_per_code=redemption_limit_per_code,
            redemption_count=0,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_customer_vouchers(
        self,
        *,
        tenant_id: str,
        customer_profile_id: str,
    ) -> list[CustomerVoucherAssignment]:
        statement = (
            select(CustomerVoucherAssignment)
            .where(
                CustomerVoucherAssignment.tenant_id == tenant_id,
                CustomerVoucherAssignment.customer_profile_id == customer_profile_id,
            )
            .order_by(CustomerVoucherAssignment.created_at.asc(), CustomerVoucherAssignment.id.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_customer_voucher(
        self,
        *,
        tenant_id: str,
        voucher_id: str,
        customer_profile_id: str | None = None,
    ) -> CustomerVoucherAssignment | None:
        statement = select(CustomerVoucherAssignment).where(
            CustomerVoucherAssignment.tenant_id == tenant_id,
            CustomerVoucherAssignment.id == voucher_id,
        )
        if customer_profile_id is not None:
            statement = statement.where(CustomerVoucherAssignment.customer_profile_id == customer_profile_id)
        return await self._session.scalar(statement)

    async def get_customer_voucher_by_code(
        self,
        *,
        tenant_id: str,
        voucher_code: str,
    ) -> CustomerVoucherAssignment | None:
        statement = select(CustomerVoucherAssignment).where(
            CustomerVoucherAssignment.tenant_id == tenant_id,
            CustomerVoucherAssignment.voucher_code == voucher_code,
        )
        return await self._session.scalar(statement)

    async def create_customer_voucher(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        customer_profile_id: str,
        voucher_id: str,
        voucher_code: str,
        voucher_name_snapshot: str,
        voucher_amount: float,
        status: str,
        issued_note: str | None,
    ) -> CustomerVoucherAssignment:
        record = CustomerVoucherAssignment(
            id=voucher_id,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            customer_profile_id=customer_profile_id,
            voucher_code=voucher_code,
            voucher_name_snapshot=voucher_name_snapshot,
            voucher_amount=voucher_amount,
            status=status,
            issued_note=issued_note,
        )
        self._session.add(record)
        await self._session.flush()
        return record
