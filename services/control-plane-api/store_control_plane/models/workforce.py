from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
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
    runtime_profile: Mapped[str] = mapped_column(String(64), default="desktop_spoke")
    is_branch_hub: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_secret_hash: Mapped[str | None] = mapped_column(String(128), default=None)
    sync_secret_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class BranchCashierSession(Base, TimestampMixin):
    __tablename__ = "branch_cashier_sessions"
    __table_args__ = (
        UniqueConstraint("branch_id", "session_number", name="uq_branch_cashier_sessions_branch_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    device_registration_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id"), index=True)
    staff_profile_id: Mapped[str] = mapped_column(ForeignKey("staff_profiles.id"), index=True)
    runtime_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    opened_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    closed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    session_number: Mapped[str] = mapped_column(String(64), index=True)
    opening_float_amount: Mapped[float] = mapped_column(default=0.0)
    opening_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    closing_note: Mapped[str | None] = mapped_column(String(1024), default=None)
    force_close_reason: Mapped[str | None] = mapped_column(String(1024), default=None)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None, index=True)


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


class StoreDesktopActivation(Base, TimestampMixin):
    __tablename__ = "store_desktop_activations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    staff_profile_id: Mapped[str] = mapped_column(ForeignKey("staff_profiles.id", ondelete="CASCADE"), index=True)
    activation_code_hash: Mapped[str] = mapped_column(String(128), index=True)
    local_auth_token_hash: Mapped[str | None] = mapped_column(String(128), default=None, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ISSUED")
    activation_version: Mapped[int] = mapped_column(Integer, default=1)
    issued_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    offline_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class SpokeRuntimeActivation(Base, TimestampMixin):
    __tablename__ = "spoke_runtime_activations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    hub_device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    activation_code_hash: Mapped[str] = mapped_column(String(128), index=True)
    pairing_mode: Mapped[str] = mapped_column(String(32), default="approval_code")
    runtime_profile: Mapped[str] = mapped_column(String(64), default="desktop_spoke")
    status: Mapped[str] = mapped_column(String(32), default="ISSUED")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    redeemed_spoke_installation_id: Mapped[str | None] = mapped_column(String(96), default=None, index=True)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
