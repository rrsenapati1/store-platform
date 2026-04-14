from __future__ import annotations

from pydantic import BaseModel, model_validator


class VendorDisputeCreateRequest(BaseModel):
    goods_receipt_id: str | None = None
    purchase_invoice_id: str | None = None
    dispute_type: str
    note: str | None = None

    @model_validator(mode="after")
    def validate_reference(self):
        if bool(self.goods_receipt_id) == bool(self.purchase_invoice_id):
            raise ValueError("Exactly one reference is required")
        return self


class VendorDisputeResolveRequest(BaseModel):
    resolution_note: str | None = None
