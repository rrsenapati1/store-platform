from __future__ import annotations

from pydantic import BaseModel, Field

from .billing import SaleLineCreateRequest, SaleReturnResponse, SaleResponse


class ExchangeCreateRequest(BaseModel):
    settlement_method: str
    return_lines: list[SaleLineCreateRequest] = Field(min_length=1)
    replacement_lines: list[SaleLineCreateRequest] = Field(min_length=1)


class ExchangePaymentAllocationResponse(BaseModel):
    payment_method: str
    amount: float


class ExchangeResponse(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    original_sale_id: str
    replacement_sale_id: str
    sale_return_id: str
    status: str
    balance_direction: str
    balance_amount: float
    settlement_method: str
    payment_allocations: list[ExchangePaymentAllocationResponse]
    sale_return: SaleReturnResponse
    replacement_sale: SaleResponse
