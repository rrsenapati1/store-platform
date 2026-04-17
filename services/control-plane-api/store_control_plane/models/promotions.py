from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class PromotionCampaign(Base, TimestampMixin):
    __tablename__ = "promotion_campaigns"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    trigger_mode: Mapped[str] = mapped_column(String(32), default="CODE", index=True)
    scope: Mapped[str] = mapped_column(String(32), default="CART")
    discount_type: Mapped[str] = mapped_column(String(32))
    discount_value: Mapped[float] = mapped_column(Float(), default=0.0)
    priority: Mapped[int] = mapped_column(Integer(), default=100)
    stacking_rule: Mapped[str] = mapped_column(String(32), default="STACKABLE")
    minimum_order_amount: Mapped[float | None] = mapped_column(Float(), default=None)
    maximum_discount_amount: Mapped[float | None] = mapped_column(Float(), default=None)
    redemption_limit_total: Mapped[int | None] = mapped_column(Integer(), default=None)
    redemption_count: Mapped[int] = mapped_column(Integer(), default=0)
    target_product_ids: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    target_category_codes: Mapped[list[str] | None] = mapped_column(JSON, default=None)


class PromotionCode(Base, TimestampMixin):
    __tablename__ = "promotion_codes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_promotion_codes_tenant_code"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("promotion_campaigns.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    redemption_limit_per_code: Mapped[int | None] = mapped_column(Integer(), default=None)
    redemption_count: Mapped[int] = mapped_column(Integer(), default=0)


class CustomerVoucherAssignment(Base, TimestampMixin):
    __tablename__ = "customer_voucher_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "voucher_code", name="uq_customer_vouchers_tenant_code"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("promotion_campaigns.id", ondelete="CASCADE"), index=True)
    customer_profile_id: Mapped[str] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    voucher_code: Mapped[str] = mapped_column(String(64), index=True)
    voucher_name_snapshot: Mapped[str] = mapped_column(String(255))
    voucher_amount: Mapped[float] = mapped_column(Float(), default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    issued_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    canceled_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    redeemed_sale_id: Mapped[str | None] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
