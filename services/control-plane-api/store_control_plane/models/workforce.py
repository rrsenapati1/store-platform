from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class StaffProfile(Base, TimestampMixin):
    __tablename__ = "staff_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    primary_branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), default=None, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(32), default=None)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")


class DeviceRegistration(Base, TimestampMixin):
    __tablename__ = "device_registrations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    assigned_staff_profile_id: Mapped[str | None] = mapped_column(ForeignKey("staff_profiles.id"), default=None, index=True)
    installation_id: Mapped[str | None] = mapped_column(String(96), default=None, unique=True, index=True)
    device_name: Mapped[str] = mapped_column(String(255))
    device_code: Mapped[str] = mapped_column(String(64), index=True)
    session_surface: Mapped[str] = mapped_column(String(64))
    is_branch_hub: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_secret_hash: Mapped[str | None] = mapped_column(String(128), default=None)
    sync_secret_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class DeviceClaim(Base, TimestampMixin):
    __tablename__ = "device_claims"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    installation_id: Mapped[str] = mapped_column(String(96), index=True)
    claim_code: Mapped[str] = mapped_column(String(32), index=True)
    runtime_kind: Mapped[str] = mapped_column(String(64))
    hostname: Mapped[str | None] = mapped_column(String(255), default=None)
    operating_system: Mapped[str | None] = mapped_column(String(64), default=None)
    architecture: Mapped[str | None] = mapped_column(String(64), default=None)
    app_version: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    approved_device_id: Mapped[str | None] = mapped_column(ForeignKey("device_registrations.id"), default=None, index=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
