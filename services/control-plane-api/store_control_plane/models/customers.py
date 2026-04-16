from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from ..utils import utc_now
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


class TenantLoyaltyProgram(Base, TimestampMixin):
    __tablename__ = "tenant_loyalty_programs"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_loyalty_programs_tenant"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="DISABLED")
    earn_points_per_currency_unit: Mapped[float] = mapped_column(Float(), default=0.0)
    redeem_step_points: Mapped[int] = mapped_column(Integer(), default=100)
    redeem_value_per_step: Mapped[float] = mapped_column(Float(), default=0.0)
    minimum_redeem_points: Mapped[int] = mapped_column(Integer(), default=0)


class CustomerCreditAccount(Base, TimestampMixin):
    __tablename__ = "customer_credit_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "customer_profile_id",
            name="uq_customer_credit_accounts_tenant_customer_profile",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_profile_id: Mapped[str] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    available_balance: Mapped[float] = mapped_column(Float(), default=0.0)
    issued_total: Mapped[float] = mapped_column(Float(), default=0.0)
    redeemed_total: Mapped[float] = mapped_column(Float(), default=0.0)
    adjusted_total: Mapped[float] = mapped_column(Float(), default=0.0)


class CustomerLoyaltyAccount(Base, TimestampMixin):
    __tablename__ = "customer_loyalty_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "customer_profile_id",
            name="uq_customer_loyalty_accounts_tenant_customer_profile",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_profile_id: Mapped[str] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    available_points: Mapped[int] = mapped_column(Integer(), default=0)
    earned_total: Mapped[int] = mapped_column(Integer(), default=0)
    redeemed_total: Mapped[int] = mapped_column(Integer(), default=0)
    adjusted_total: Mapped[int] = mapped_column(Integer(), default=0)


class CustomerCreditLot(Base, TimestampMixin):
    __tablename__ = "customer_credit_lots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_profile_id: Mapped[str] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("customer_credit_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), default=None)
    source_type: Mapped[str] = mapped_column(String(32))
    source_reference_id: Mapped[str | None] = mapped_column(String(64), default=None)
    original_amount: Mapped[float] = mapped_column(Float(), default=0.0)
    remaining_amount: Mapped[float] = mapped_column(Float(), default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utc_now, index=True)


class CustomerCreditLedgerEntry(Base, TimestampMixin):
    __tablename__ = "customer_credit_ledger_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_profile_id: Mapped[str] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("customer_credit_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    lot_id: Mapped[str | None] = mapped_column(
        ForeignKey("customer_credit_lots.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), default=None)
    entry_type: Mapped[str] = mapped_column(String(32))
    source_type: Mapped[str] = mapped_column(String(32))
    source_reference_id: Mapped[str | None] = mapped_column(String(64), default=None)
    amount: Mapped[float] = mapped_column(Float(), default=0.0)
    running_balance: Mapped[float] = mapped_column(Float(), default=0.0)
    note: Mapped[str | None] = mapped_column(String(1024), default=None)


class CustomerLoyaltyLedgerEntry(Base, TimestampMixin):
    __tablename__ = "customer_loyalty_ledger_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    customer_profile_id: Mapped[str] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        ForeignKey("customer_loyalty_accounts.id", ondelete="CASCADE"),
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), default=None)
    entry_type: Mapped[str] = mapped_column(String(32))
    source_type: Mapped[str] = mapped_column(String(32))
    source_reference_id: Mapped[str | None] = mapped_column(String(64), default=None)
    points_delta: Mapped[int] = mapped_column(Integer(), default=0)
    balance_after: Mapped[int] = mapped_column(Integer(), default=0)
    note: Mapped[str | None] = mapped_column(String(1024), default=None)


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
