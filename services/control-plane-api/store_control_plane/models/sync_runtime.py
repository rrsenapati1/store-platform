from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from ..utils import utc_now


class SyncEnvelope(Base, TimestampMixin):
    __tablename__ = "sync_envelopes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "branch_id",
            "device_id",
            "idempotency_key",
            "direction",
            name="uq_sync_envelope_scope_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True)
    transport: Mapped[str] = mapped_column(String(16), default="REST")
    direction: Mapped[str] = mapped_column(String(16))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(128), default=None)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    last_error: Mapped[str | None] = mapped_column(String(500), default=None)


class SyncMutationLog(Base, TimestampMixin):
    __tablename__ = "sync_mutation_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True)
    table_name: Mapped[str] = mapped_column(String(64), index=True)
    record_id: Mapped[str] = mapped_column(String(128), index=True)
    operation: Mapped[str] = mapped_column(String(32))
    client_version: Mapped[int] = mapped_column(Integer, default=1)
    expected_server_version: Mapped[int] = mapped_column(Integer, default=0)
    server_version: Mapped[int] = mapped_column(Integer, index=True)
    request_hash: Mapped[str] = mapped_column(String(128))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utc_now)


class SyncConflict(Base, TimestampMixin):
    __tablename__ = "sync_conflicts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    source_idempotency_key: Mapped[str] = mapped_column(String(128), index=True)
    conflict_index: Mapped[int] = mapped_column(Integer, default=0)
    request_hash: Mapped[str] = mapped_column(String(128))
    table_name: Mapped[str] = mapped_column(String(64), index=True)
    record_id: Mapped[str] = mapped_column(String(128), index=True)
    reason: Mapped[str] = mapped_column(String(64), default="UNKNOWN")
    resolution: Mapped[str | None] = mapped_column(String(64), default=None)
    message: Mapped[str | None] = mapped_column(String(500), default=None)
    client_version: Mapped[int | None] = mapped_column(Integer, default=None)
    server_version: Mapped[int | None] = mapped_column(Integer, default=None)
    retry_strategy: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[str] = mapped_column(String(24), default="OPEN")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    resolution_method: Mapped[str | None] = mapped_column(String(64), default=None)
    resolved_by_idempotency_key: Mapped[str | None] = mapped_column(String(128), default=None)
    resolved_by_device_id: Mapped[str | None] = mapped_column(String(64), default=None)


class HubSyncStatus(Base, TimestampMixin):
    __tablename__ = "hub_sync_status"
    __table_args__ = (
        UniqueConstraint("tenant_id", "branch_id", name="uq_hub_sync_status_scope"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    hub_device_id: Mapped[str | None] = mapped_column(ForeignKey("device_registrations.id", ondelete="SET NULL"), default=None)
    source_device_id: Mapped[str | None] = mapped_column(String(128), default=None)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_successful_push_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_successful_pull_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
    last_successful_push_mutations: Mapped[int] = mapped_column(Integer, default=0)
    last_idempotency_key: Mapped[str | None] = mapped_column(String(128), default=None)
    last_pull_cursor: Mapped[int] = mapped_column(Integer, default=0)
    branch_cursor: Mapped[int] = mapped_column(Integer, default=0)
    pending_mutation_count: Mapped[int] = mapped_column(Integer, default=0)
    connected_spoke_count: Mapped[int] = mapped_column(Integer, default=0)
    local_outbox_depth: Mapped[int] = mapped_column(Integer, default=0)
    oldest_unsynced_mutation_age_seconds: Mapped[int] = mapped_column(Integer, default=0)
    runtime_state: Mapped[str] = mapped_column(String(32), default="CURRENT")
    last_local_spoke_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)


class HubSpokeObservation(Base, TimestampMixin):
    __tablename__ = "hub_spoke_observations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "branch_id",
            "hub_device_id",
            "spoke_device_id",
            name="uq_hub_spoke_observation_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), index=True)
    hub_device_id: Mapped[str] = mapped_column(ForeignKey("device_registrations.id", ondelete="CASCADE"), index=True)
    spoke_device_id: Mapped[str] = mapped_column(String(128), index=True)
    runtime_kind: Mapped[str] = mapped_column(String(64))
    hostname: Mapped[str | None] = mapped_column(String(255), default=None)
    operating_system: Mapped[str | None] = mapped_column(String(64), default=None)
    app_version: Mapped[str | None] = mapped_column(String(64), default=None)
    connection_state: Mapped[str] = mapped_column(String(32), default="DISCOVERED")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utc_now)
    last_local_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), default=None)
