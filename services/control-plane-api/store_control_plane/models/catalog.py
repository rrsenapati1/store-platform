from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class CatalogProduct(Base, TimestampMixin):
    __tablename__ = "catalog_products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku_code", name="uq_catalog_products_tenant_sku"),
        UniqueConstraint("tenant_id", "barcode", name="uq_catalog_products_tenant_barcode"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    sku_code: Mapped[str] = mapped_column(String(128))
    barcode: Mapped[str] = mapped_column(String(64))
    hsn_sac_code: Mapped[str] = mapped_column(String(32))
    gst_rate: Mapped[float] = mapped_column(default=0.0)
    mrp: Mapped[float] = mapped_column(Float(), default=0.0)
    category_code: Mapped[str | None] = mapped_column(String(64), default=None)
    selling_price: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")


class BranchCatalogItem(Base, TimestampMixin):
    __tablename__ = "branch_catalog_items"
    __table_args__ = (
        UniqueConstraint("branch_id", "product_id", name="uq_branch_catalog_items_branch_product"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    selling_price_override: Mapped[float | None] = mapped_column(default=None)
    availability_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    reorder_point: Mapped[float | None] = mapped_column(Float(), default=None)
    target_stock: Mapped[float | None] = mapped_column(Float(), default=None)


class PriceTier(Base, TimestampMixin):
    __tablename__ = "price_tiers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_price_tiers_tenant_code"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")


class BranchPriceTierPrice(Base, TimestampMixin):
    __tablename__ = "branch_price_tier_prices"
    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "product_id",
            "price_tier_id",
            name="uq_branch_price_tier_prices_branch_product_tier",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    price_tier_id: Mapped[str] = mapped_column(ForeignKey("price_tiers.id", ondelete="CASCADE"), index=True)
    selling_price: Mapped[float] = mapped_column(Float())
