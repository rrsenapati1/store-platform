from __future__ import annotations

from fastapi import HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import PromotionRepository, TenantRepository
from ..utils import new_id


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_status(value: str | None, *, allowed: set[str], field_name: str) -> str:
    normalized = _normalize_optional(value)
    if normalized is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"{field_name} is required")
    upper = normalized.upper()
    if upper not in allowed:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Unsupported {field_name.lower()}")
    return upper


class PromotionService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._promotion_repo = PromotionRepository(session)

    async def list_campaigns(self, *, tenant_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        campaigns = await self._promotion_repo.list_campaigns(tenant_id=tenant_id)
        return {"records": [await self._serialize_campaign(record) for record in campaigns]}

    async def list_active_automatic_campaigns(self, *, tenant_id: str) -> list:
        await self._require_tenant(tenant_id)
        campaigns = await self._promotion_repo.list_campaigns(tenant_id=tenant_id)
        return [
            record
            for record in campaigns
            if record.status == "ACTIVE" and record.trigger_mode == "AUTOMATIC"
        ]

    async def get_campaign(self, *, tenant_id: str, campaign_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        campaign = await self._require_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
        return await self._serialize_campaign(campaign)

    async def create_campaign(
        self,
        *,
        tenant_id: str,
        name: str,
        status: str,
        trigger_mode: str,
        scope: str,
        discount_type: str,
        discount_value: float,
        minimum_order_amount: float | None,
        maximum_discount_amount: float | None,
        redemption_limit_total: int | None,
        target_product_ids: list[str] | None,
        target_category_codes: list[str] | None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_trigger_mode = _normalize_status(
            trigger_mode,
            allowed={"CODE", "AUTOMATIC"},
            field_name="Trigger mode",
        )
        normalized_scope = _normalize_status(
            scope,
            allowed={"CART", "ITEM_CATEGORY"},
            field_name="Scope",
        )
        normalized_targets = self._normalize_targets(
            trigger_mode=normalized_trigger_mode,
            scope=normalized_scope,
            target_product_ids=target_product_ids,
            target_category_codes=target_category_codes,
        )
        record = await self._promotion_repo.create_campaign(
            tenant_id=tenant_id,
            campaign_id=new_id(),
            name=self._normalize_name(name),
            status=_normalize_status(status, allowed={"ACTIVE", "DISABLED", "ARCHIVED"}, field_name="Status"),
            trigger_mode=normalized_trigger_mode,
            scope=normalized_scope,
            discount_type=_normalize_status(discount_type, allowed={"FLAT_AMOUNT", "PERCENTAGE"}, field_name="Discount type"),
            discount_value=self._normalize_discount_value(discount_value),
            minimum_order_amount=self._normalize_amount(minimum_order_amount, field_name="Minimum order amount"),
            maximum_discount_amount=self._normalize_amount(maximum_discount_amount, field_name="Maximum discount amount"),
            redemption_limit_total=self._normalize_limit(redemption_limit_total, field_name="Redemption limit total"),
            target_product_ids=normalized_targets["target_product_ids"],
            target_category_codes=normalized_targets["target_category_codes"],
        )
        return await self._serialize_campaign(record)

    async def update_campaign(self, *, tenant_id: str, campaign_id: str, updates: dict[str, object]) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
        next_trigger_mode = record.trigger_mode
        next_scope = record.scope
        next_target_product_ids = list(record.target_product_ids or [])
        next_target_category_codes = list(record.target_category_codes or [])
        if "name" in updates:
            record.name = self._normalize_name(updates.get("name"))
        if "status" in updates:
            record.status = _normalize_status(updates.get("status"), allowed={"ACTIVE", "DISABLED", "ARCHIVED"}, field_name="Status")
        if "trigger_mode" in updates:
            next_trigger_mode = _normalize_status(updates.get("trigger_mode"), allowed={"CODE", "AUTOMATIC"}, field_name="Trigger mode")
        if "scope" in updates:
            next_scope = _normalize_status(updates.get("scope"), allowed={"CART", "ITEM_CATEGORY"}, field_name="Scope")
        if "discount_type" in updates:
            record.discount_type = _normalize_status(updates.get("discount_type"), allowed={"FLAT_AMOUNT", "PERCENTAGE"}, field_name="Discount type")
        if "discount_value" in updates:
            record.discount_value = self._normalize_discount_value(updates.get("discount_value"))
        if "minimum_order_amount" in updates:
            record.minimum_order_amount = self._normalize_amount(updates.get("minimum_order_amount"), field_name="Minimum order amount")
        if "maximum_discount_amount" in updates:
            record.maximum_discount_amount = self._normalize_amount(updates.get("maximum_discount_amount"), field_name="Maximum discount amount")
        if "redemption_limit_total" in updates:
            record.redemption_limit_total = self._normalize_limit(updates.get("redemption_limit_total"), field_name="Redemption limit total")
        if "target_product_ids" in updates:
            next_target_product_ids = self._normalize_id_list(updates.get("target_product_ids"))
        if "target_category_codes" in updates:
            next_target_category_codes = self._normalize_code_list(updates.get("target_category_codes"))
        normalized_targets = self._normalize_targets(
            trigger_mode=next_trigger_mode,
            scope=next_scope,
            target_product_ids=next_target_product_ids,
            target_category_codes=next_target_category_codes,
        )
        record.trigger_mode = next_trigger_mode
        record.scope = next_scope
        record.target_product_ids = normalized_targets["target_product_ids"]
        record.target_category_codes = normalized_targets["target_category_codes"]
        await self._session.flush()
        return await self._serialize_campaign(record)

    async def disable_campaign(self, *, tenant_id: str, campaign_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
        record.status = "DISABLED"
        await self._session.flush()
        return await self._serialize_campaign(record)

    async def reactivate_campaign(self, *, tenant_id: str, campaign_id: str) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        record = await self._require_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
        record.status = "ACTIVE"
        await self._session.flush()
        return await self._serialize_campaign(record)

    async def create_code(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        code: str,
        status: str,
        redemption_limit_per_code: int | None,
    ) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        campaign = await self._require_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
        if campaign.trigger_mode != "CODE":
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Automatic campaigns do not support shared promotion codes",
            )
        normalized_code = self._normalize_code(code)
        existing = await self._promotion_repo.get_code_by_value(tenant_id=tenant_id, code=normalized_code)
        if existing is not None:
            raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Promotion code already exists")
        record = await self._promotion_repo.create_code(
            tenant_id=tenant_id,
            campaign_id=campaign.id,
            promotion_code_id=new_id(),
            code=normalized_code,
            status=_normalize_status(status, allowed={"ACTIVE", "DISABLED"}, field_name="Status"),
            redemption_limit_per_code=self._normalize_limit(redemption_limit_per_code, field_name="Redemption limit per code"),
        )
        return self._serialize_code(record)

    async def validate_promotion_code(self, *, tenant_id: str, promotion_code: str, sale_total: float) -> dict[str, object]:
        await self._require_tenant(tenant_id)
        normalized_code = self._normalize_code(promotion_code)
        code = await self._promotion_repo.get_code_by_value(tenant_id=tenant_id, code=normalized_code)
        if code is None or code.status != "ACTIVE":
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion code is invalid")
        campaign = await self._require_campaign(tenant_id=tenant_id, campaign_id=code.campaign_id)
        if campaign.status != "ACTIVE" or campaign.trigger_mode != "CODE":
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion code is invalid")
        if campaign.minimum_order_amount is not None and float(sale_total) < float(campaign.minimum_order_amount):
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion code is invalid")
        if campaign.redemption_limit_total is not None and campaign.redemption_count >= campaign.redemption_limit_total:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion code is invalid")
        if code.redemption_limit_per_code is not None and code.redemption_count >= code.redemption_limit_per_code:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion code is invalid")
        if campaign.discount_type == "FLAT_AMOUNT":
            discount_amount = float(campaign.discount_value)
        else:
            discount_amount = round(float(sale_total) * float(campaign.discount_value) / 100.0, 2)
            if campaign.maximum_discount_amount is not None:
                discount_amount = min(discount_amount, float(campaign.maximum_discount_amount))
        discount_amount = min(round(discount_amount, 2), round(float(sale_total), 2))
        return {"campaign": campaign, "code": code, "discount_amount": discount_amount}

    async def mark_code_redeemed(self, *, tenant_id: str, promotion_code_id: str) -> None:
        code = await self._require_code_by_id(tenant_id=tenant_id, promotion_code_id=promotion_code_id)
        campaign = await self._require_campaign(tenant_id=tenant_id, campaign_id=code.campaign_id)
        campaign.redemption_count += 1
        code.redemption_count += 1
        await self._session.flush()

    async def _require_code_by_id(self, *, tenant_id: str, promotion_code_id: str):
        record = await self._promotion_repo.get_code_by_id(tenant_id=tenant_id, promotion_code_id=promotion_code_id)
        if record is None:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Promotion code not found")
        return record

    async def _require_tenant(self, tenant_id: str) -> None:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    async def _require_campaign(self, *, tenant_id: str, campaign_id: str):
        record = await self._promotion_repo.get_campaign(tenant_id=tenant_id, campaign_id=campaign_id)
        if record is None:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Promotion campaign not found")
        return record

    async def _serialize_campaign(self, record) -> dict[str, object]:
        codes = await self._promotion_repo.list_codes_for_campaign(tenant_id=record.tenant_id, campaign_id=record.id)
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "name": record.name,
            "status": record.status,
            "trigger_mode": record.trigger_mode,
            "scope": record.scope,
            "discount_type": record.discount_type,
            "discount_value": record.discount_value,
            "minimum_order_amount": record.minimum_order_amount,
            "maximum_discount_amount": record.maximum_discount_amount,
            "redemption_limit_total": record.redemption_limit_total,
            "redemption_count": record.redemption_count,
            "target_product_ids": list(record.target_product_ids or []),
            "target_category_codes": list(record.target_category_codes or []),
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "codes": [self._serialize_code(code) for code in codes],
        }

    @staticmethod
    def serialize_campaign_snapshot(record) -> dict[str, object]:
        return {
            "id": record.id,
            "name": record.name,
            "trigger_mode": record.trigger_mode,
            "scope": record.scope,
            "discount_type": record.discount_type,
            "discount_value": float(record.discount_value),
        }

    @staticmethod
    def _serialize_code(record) -> dict[str, object]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "campaign_id": record.campaign_id,
            "code": record.code,
            "status": record.status,
            "redemption_limit_per_code": record.redemption_limit_per_code,
            "redemption_count": record.redemption_count,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    @staticmethod
    def _normalize_name(value: str | None) -> str:
        normalized = _normalize_optional(value)
        if normalized is None:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Campaign name is required")
        return normalized

    @staticmethod
    def _normalize_code(value: str | None) -> str:
        normalized = _normalize_optional(value)
        if normalized is None:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion code is required")
        return normalized.upper()

    @staticmethod
    def _normalize_discount_value(value: object) -> float:
        if value is None:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Discount value is required")
        normalized = round(float(value), 2)
        if normalized < 0:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Discount value must be non-negative")
        return normalized

    @staticmethod
    def _normalize_amount(value: object, *, field_name: str) -> float | None:
        if value is None:
            return None
        normalized = round(float(value), 2)
        if normalized < 0:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"{field_name} must be non-negative")
        return normalized

    @staticmethod
    def _normalize_limit(value: object, *, field_name: str) -> int | None:
        if value is None:
            return None
        normalized = int(value)
        if normalized < 0:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"{field_name} must be non-negative")
        return normalized

    @staticmethod
    def _normalize_id_list(value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion targets must be a list")
        normalized: list[str] = []
        for entry in value:
            text = _normalize_optional(str(entry) if entry is not None else None)
            if text is not None and text not in normalized:
                normalized.append(text)
        return normalized

    @staticmethod
    def _normalize_code_list(value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Promotion targets must be a list")
        normalized: list[str] = []
        for entry in value:
            text = _normalize_optional(str(entry) if entry is not None else None)
            if text is not None:
                upper = text.upper()
                if upper not in normalized:
                    normalized.append(upper)
        return normalized

    def _normalize_targets(
        self,
        *,
        trigger_mode: str,
        scope: str,
        target_product_ids: list[str] | None,
        target_category_codes: list[str] | None,
    ) -> dict[str, list[str] | None]:
        normalized_product_ids = self._normalize_id_list(target_product_ids)
        normalized_category_codes = self._normalize_code_list(target_category_codes)
        if trigger_mode == "CODE":
            return {
                "target_product_ids": [],
                "target_category_codes": [],
            }
        if scope == "ITEM_CATEGORY" and not normalized_product_ids and not normalized_category_codes:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Automatic item or category campaigns require at least one target",
            )
        if scope == "CART":
            return {
                "target_product_ids": [],
                "target_category_codes": [],
            }
        return {
            "target_product_ids": normalized_product_ids,
            "target_category_codes": normalized_category_codes,
        }
