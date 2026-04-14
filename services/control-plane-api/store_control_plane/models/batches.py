from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class BatchLot(Base, TimestampMixin):
    __tablename__ = "batch_lots"
    __table_args__ = (
        UniqueConstraint("goods_receipt_id", "batch_number", name="uq_batch_lots_goods_receipt_batch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    goods_receipt_id: Mapped[str] = mapped_column(ForeignKey("goods_receipts.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    batch_number: Mapped[str] = mapped_column(String(128), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    expiry_date: Mapped[date] = mapped_column(Date())


class BatchExpiryWriteOff(Base, TimestampMixin):
    __tablename__ = "batch_expiry_write_offs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    batch_lot_id: Mapped[str] = mapped_column(ForeignKey("batch_lots.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    reason: Mapped[str] = mapped_column(String(255))
