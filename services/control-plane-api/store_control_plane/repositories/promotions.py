from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PromotionCampaign, PromotionCode


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
        discount_type: str,
        discount_value: float,
        minimum_order_amount: float | None,
        maximum_discount_amount: float | None,
        redemption_limit_total: int | None,
    ) -> PromotionCampaign:
        record = PromotionCampaign(
            id=campaign_id,
            tenant_id=tenant_id,
            name=name,
            status=status,
            discount_type=discount_type,
            discount_value=discount_value,
            minimum_order_amount=minimum_order_amount,
            maximum_discount_amount=maximum_discount_amount,
            redemption_limit_total=redemption_limit_total,
            redemption_count=0,
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
