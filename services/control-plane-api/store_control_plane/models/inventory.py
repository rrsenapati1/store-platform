from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class GoodsReceipt(Base, TimestampMixin):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", name="uq_goods_receipts_purchase_order"),
        UniqueConstraint("branch_id", "goods_receipt_number", name="uq_goods_receipts_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    purchase_order_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), index=True)
    goods_receipt_number: Mapped[str] = mapped_column(String(64), index=True)
    received_on: Mapped[date] = mapped_column(Date())


class GoodsReceiptLine(Base, TimestampMixin):
    __tablename__ = "goods_receipt_lines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    goods_receipt_id: Mapped[str] = mapped_column(ForeignKey("goods_receipts.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_cost: Mapped[float] = mapped_column(default=0.0)
    line_total: Mapped[float] = mapped_column(default=0.0)


class InventoryLedgerEntry(Base, TimestampMixin):
    __tablename__ = "inventory_ledger_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    entry_type: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    reference_type: Mapped[str] = mapped_column(String(64))
    reference_id: Mapped[str] = mapped_column(String(32), index=True)


class StockAdjustment(Base, TimestampMixin):
    __tablename__ = "stock_adjustments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    quantity_delta: Mapped[float] = mapped_column(default=0.0)
    reason: Mapped[str] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(1024), default=None)


class StockCountSession(Base, TimestampMixin):
    __tablename__ = "stock_count_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    counted_quantity: Mapped[float] = mapped_column(default=0.0)
    expected_quantity: Mapped[float] = mapped_column(default=0.0)
    variance_quantity: Mapped[float] = mapped_column(default=0.0)
    note: Mapped[str | None] = mapped_column(String(1024), default=None)


class TransferOrder(Base, TimestampMixin):
    __tablename__ = "transfer_orders"
    __table_args__ = (
        UniqueConstraint("source_branch_id", "transfer_number", name="uq_transfer_orders_source_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    source_branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    destination_branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.id", ondelete="CASCADE"), index=True)
    transfer_number: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")
    note: Mapped[str | None] = mapped_column(String(1024), default=None)
