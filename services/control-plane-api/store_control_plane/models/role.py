from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class RoleDefinition(Base, TimestampMixin):
    __tablename__ = "role_definitions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), index=True)
    role_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class RoleCapability(Base, TimestampMixin):
    __tablename__ = "role_capabilities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    role_definition_id: Mapped[str] = mapped_column(ForeignKey("role_definitions.id", ondelete="CASCADE"), index=True)
    capability: Mapped[str] = mapped_column(String(128), index=True)
