from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CatalogProductCreateRequest(BaseModel):
    name: str
    sku_code: str
    barcode: str
    hsn_sac_code: str
    gst_rate: float = Field(ge=0)
    mrp: float | None = Field(default=None, gt=0)
    category_code: str | None = None
    selling_price: float = Field(gt=0)


class CatalogProductResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    sku_code: str
    barcode: str
    hsn_sac_code: str
    gst_rate: float
    mrp: float
    category_code: str | None = None
    selling_price: float
    status: str


class CatalogProductRecord(BaseModel):
    product_id: str
    tenant_id: str
    name: str
    sku_code: str
    barcode: str
    hsn_sac_code: str
    gst_rate: float
    mrp: float
    category_code: str | None = None
    selling_price: float
    status: str


class CatalogProductListResponse(BaseModel):
    records: list[CatalogProductRecord]


class BranchCatalogItemUpsertRequest(BaseModel):
    product_id: str
    selling_price_override: float | None = Field(default=None, gt=0)
    availability_status: str = "ACTIVE"
    reorder_point: float | None = Field(default=None, ge=0)
    target_stock: float | None = Field(default=None, gt=0)


class BranchCatalogItemResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    product_id: str
    product_name: str
    sku_code: str
    barcode: str
    hsn_sac_code: str
    gst_rate: float
    mrp: float
    category_code: str | None = None
    base_selling_price: float
    selling_price_override: float | None
    effective_selling_price: float
    availability_status: str
    reorder_point: float | None = None
    target_stock: float | None = None


class BranchCatalogItemRecord(BranchCatalogItemResponse):
    pass


class BranchCatalogItemListResponse(BaseModel):
    records: list[BranchCatalogItemRecord]


class PriceTierCreateRequest(BaseModel):
    code: str
    display_name: str
    status: str = "ACTIVE"


class PriceTierUpdateRequest(BaseModel):
    display_name: str | None = None
    status: str | None = None


class PriceTierResponse(BaseModel):
    id: str
    tenant_id: str
    code: str
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class PriceTierRecord(PriceTierResponse):
    pass


class PriceTierListResponse(BaseModel):
    records: list[PriceTierRecord]


class BranchPriceTierPriceUpsertRequest(BaseModel):
    product_id: str
    price_tier_id: str
    selling_price: float = Field(gt=0)


class BranchPriceTierPriceResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    product_id: str
    product_name: str
    sku_code: str
    price_tier_id: str
    price_tier_code: str
    price_tier_display_name: str
    base_selling_price: float
    effective_base_selling_price: float
    selling_price: float
    created_at: datetime
    updated_at: datetime


class BranchPriceTierPriceRecord(BranchPriceTierPriceResponse):
    pass


class BranchPriceTierPriceListResponse(BaseModel):
    records: list[BranchPriceTierPriceRecord]
