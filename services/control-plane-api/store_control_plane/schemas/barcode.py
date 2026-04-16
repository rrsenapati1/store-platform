from __future__ import annotations

from pydantic import BaseModel


class BarcodeAllocationRequest(BaseModel):
    barcode: str | None = None


class BarcodeAllocationResponse(BaseModel):
    product_id: str
    barcode: str
    source: str


class BarcodeScanLookupResponse(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    barcode: str
    selling_price: float
    stock_on_hand: float
    availability_status: str
    reorder_point: float | None = None
    target_stock: float | None = None


class BarcodeLabelPreviewResponse(BaseModel):
    product_id: str
    sku_code: str
    product_name: str
    barcode: str
    price_label: str
