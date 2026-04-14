from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.id"), default=None, index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), default=None, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
