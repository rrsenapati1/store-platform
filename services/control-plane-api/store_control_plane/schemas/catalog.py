from __future__ import annotations

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
