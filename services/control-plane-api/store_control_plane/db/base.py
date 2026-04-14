from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..utils import utc_now


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=utc_now,
        onupdate=utc_now,
    )
