from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CustomerProfileCreateRequest(BaseModel):
    full_name: str
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    default_note: str | None = None
    tags: list[str] = Field(default_factory=list)


class CustomerProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    default_note: str | None = None
    tags: list[str] | None = None


class CustomerProfileResponse(BaseModel):
    id: str
    tenant_id: str
    full_name: str
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    default_note: str | None = None
    tags: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerProfileListResponse(BaseModel):
    records: list[CustomerProfileResponse]


class CustomerDirectoryRecord(BaseModel):
    customer_id: str
    customer_profile_id: str | None = None
    name: str
    phone: str | None
    email: str | None
    gstin: str | None
    visit_count: int
    lifetime_value: float
    last_sale_id: str | None
    last_invoice_number: str | None
    last_branch_id: str | None


class CustomerDirectoryResponse(BaseModel):
    records: list[CustomerDirectoryRecord]


class CustomerHistoryCustomer(BaseModel):
    customer_id: str
    customer_profile_id: str | None = None
    name: str
    phone: str | None
    email: str | None
    gstin: str | None
    visit_count: int
    lifetime_value: float
    last_sale_id: str | None


class CustomerHistorySummary(BaseModel):
    sales_count: int
    sales_total: float
    return_count: int
    credit_note_total: float
    exchange_count: int


class CustomerSaleHistoryRecord(BaseModel):
    sale_id: str
    branch_id: str
    invoice_id: str
    invoice_number: str
    grand_total: float
    payment_method: str


class CustomerReturnHistoryRecord(BaseModel):
    sale_return_id: str
    sale_id: str
    branch_id: str
    credit_note_id: str
    credit_note_number: str
    grand_total: float
    refund_amount: float
    status: str


class CustomerExchangeHistoryRecord(BaseModel):
    exchange_order_id: str
    sale_id: str
    branch_id: str
    return_total: float
    replacement_total: float
    balance_direction: str
    balance_amount: float


class CustomerHistoryResponse(BaseModel):
    customer: CustomerHistoryCustomer
    sales_summary: CustomerHistorySummary
    sales: list[CustomerSaleHistoryRecord]
    returns: list[CustomerReturnHistoryRecord]
    exchanges: list[CustomerExchangeHistoryRecord]


class BranchCustomerTopRecord(BaseModel):
    customer_id: str
    customer_profile_id: str | None = None
    customer_name: str
    sales_count: int
    sales_total: float
    last_invoice_number: str | None


class BranchCustomerReturnRecord(BaseModel):
    customer_id: str
    customer_profile_id: str | None = None
    customer_name: str
    return_count: int
    credit_note_total: float
    exchange_count: int


class BranchCustomerReportResponse(BaseModel):
    branch_id: str
    customer_count: int
    repeat_customer_count: int
    anonymous_sales_count: int
    anonymous_sales_total: float
    top_customers: list[BranchCustomerTopRecord]
    return_activity: list[BranchCustomerReturnRecord]
