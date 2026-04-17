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
    priority: int = Field(default=100, ge=0)
    stacking_rule: str = "STACKABLE"
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
    priority: int | None = Field(default=None, ge=0)
    stacking_rule: str | None = None
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


class CustomerVoucherIssueRequest(BaseModel):
    campaign_id: str
    note: str | None = None


class CustomerVoucherCancelRequest(BaseModel):
    note: str | None = None


class CustomerVoucherResponse(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    customer_profile_id: str
    voucher_code: str
    voucher_name: str
    voucher_amount: float
    status: str
    issued_note: str | None = None
    redeemed_sale_id: str | None = None
    created_at: datetime
    updated_at: datetime
    redeemed_at: datetime | None = None


class CustomerVoucherListResponse(BaseModel):
    records: list[CustomerVoucherResponse]


class PromotionCampaignResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    status: str
    trigger_mode: str
    scope: str
    discount_type: str
    discount_value: float
    priority: int
    stacking_rule: str
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
