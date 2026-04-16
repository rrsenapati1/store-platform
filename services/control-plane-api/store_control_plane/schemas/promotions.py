from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromotionCampaignCreateRequest(BaseModel):
    name: str
    status: str
    trigger_mode: str = "CODE"
    scope: str = "CART"
    discount_type: str
    discount_value: float = Field(ge=0)
    minimum_order_amount: float | None = Field(default=None, ge=0)
    maximum_discount_amount: float | None = Field(default=None, ge=0)
    redemption_limit_total: int | None = Field(default=None, ge=0)
    target_product_ids: list[str] | None = None
    target_category_codes: list[str] | None = None


class PromotionCampaignUpdateRequest(BaseModel):
    name: str | None = None
    status: str | None = None
    trigger_mode: str | None = None
    scope: str | None = None
    discount_type: str | None = None
    discount_value: float | None = Field(default=None, ge=0)
    minimum_order_amount: float | None = Field(default=None, ge=0)
    maximum_discount_amount: float | None = Field(default=None, ge=0)
    redemption_limit_total: int | None = Field(default=None, ge=0)
    target_product_ids: list[str] | None = None
    target_category_codes: list[str] | None = None


class PromotionCodeCreateRequest(BaseModel):
    code: str
    status: str
    redemption_limit_per_code: int | None = Field(default=None, ge=0)


class PromotionCodeResponse(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    code: str
    status: str
    redemption_limit_per_code: int | None = None
    redemption_count: int
    created_at: datetime
    updated_at: datetime


class PromotionCampaignResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    status: str
    trigger_mode: str
    scope: str
    discount_type: str
    discount_value: float
    minimum_order_amount: float | None = None
    maximum_discount_amount: float | None = None
    redemption_limit_total: int | None = None
    redemption_count: int
    target_product_ids: list[str] = []
    target_category_codes: list[str] = []
    created_at: datetime
    updated_at: datetime
    codes: list[PromotionCodeResponse] = []


class PromotionCampaignListResponse(BaseModel):
    records: list[PromotionCampaignResponse]
