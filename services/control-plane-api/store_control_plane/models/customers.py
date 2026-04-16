from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from .billing import CreditNote, ExchangeOrder, Payment, Sale, SaleReturn, SalesInvoice


class CustomerProfile(Base, TimestampMixin):
    __tablename__ = "customer_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "gstin", name="uq_customer_profiles_tenant_gstin"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    gstin: Mapped[str | None] = mapped_column(String(32), default=None, index=True)
    default_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)


@dataclass(slots=True)
class CustomerSaleSnapshot:
    sale: Sale
    invoice: SalesInvoice
    payments: list[Payment]


@dataclass(slots=True)
class CustomerSaleReturnSnapshot:
    sale_return: SaleReturn
    credit_note: CreditNote


@dataclass(slots=True)
class CustomerExchangeSnapshot:
    exchange_order: ExchangeOrder
