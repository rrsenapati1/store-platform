from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class PrintJob(Base, TimestampMixin):
    __tablename__ = "print_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    reference_type: Mapped[str] = mapped_column(String(32))
    reference_id: Mapped[str] = mapped_column(String(32), index=True)
    job_type: Mapped[str] = mapped_column(String(32))
    copies: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")
    failure_reason: Mapped[str | None] = mapped_column(String(255), default=None)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
