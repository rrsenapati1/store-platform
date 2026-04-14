from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SyncMutationRequest(BaseModel):
    table_name: str
    record_id: str
    operation: str
    payload: dict[str, object] = Field(default_factory=dict)
    client_version: int = 1
    expected_server_version: int = 0


class SyncPushRequest(BaseModel):
    idempotency_key: str
    mutations: list[SyncMutationRequest]


class SyncConflictResponse(BaseModel):
    id: str
    table_name: str
    record_id: str
    reason: str
    retry_strategy: str | None = None
    client_version: int | None = None
    server_version: int | None = None


class SyncPushResponse(BaseModel):
    duplicate: bool
    accepted_mutations: int
    conflict_count: int
    conflicts: list[SyncConflictResponse]
    server_cursor: int


class SyncPullRecordResponse(BaseModel):
    table_name: str
    record_id: str
    operation: str
    payload: dict[str, object]
    client_version: int
    expected_server_version: int
    server_version: int


class SyncPullResponse(BaseModel):
    cursor: int
    records: list[SyncPullRecordResponse]


class SyncHeartbeatResponse(BaseModel):
    status: str
    runtime_state: str
    connected_spoke_count: int
    local_outbox_depth: int
    branch_cursor: int
    last_heartbeat_at: datetime | None = None


class SyncSpokeObservationRequest(BaseModel):
    spoke_device_id: str
    runtime_kind: str
    runtime_profile: str | None = None
    hostname: str | None = None
    operating_system: str | None = None
    app_version: str | None = None
    connection_state: str = "DISCOVERED"
    last_local_sync_at: datetime | None = None


class SyncSpokeObserveRequest(BaseModel):
    spokes: list[SyncSpokeObservationRequest]


class SyncSpokeObserveResponse(BaseModel):
    observed_spoke_count: int
    connected_spoke_count: int
    last_local_spoke_sync_at: datetime | None = None


class SyncSpokeActivationRequest(BaseModel):
    runtime_profile: str
    pairing_mode: str = "approval_code"


class SyncSpokeActivationResponse(BaseModel):
    activation_code: str
    pairing_mode: str
    runtime_profile: str
    hub_device_id: str
    expires_at: str


class SyncOfflineSaleReplayLineRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SyncOfflineSaleReplayRequest(BaseModel):
    continuity_sale_id: str
    continuity_invoice_number: str
    idempotency_key: str
    issued_offline_at: datetime
    staff_actor_id: str
    customer_name: str
    customer_gstin: str | None = None
    payment_method: str
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    lines: list[SyncOfflineSaleReplayLineRequest] = Field(min_length=1)


class SyncOfflineSaleReplayResponse(BaseModel):
    result: str
    duplicate: bool
    continuity_sale_id: str
    sale_id: str | None = None
    invoice_number: str | None = None
    conflict_id: str | None = None
    message: str | None = None


class SyncSpokeRecord(BaseModel):
    spoke_device_id: str
    hub_device_id: str
    runtime_kind: str
    runtime_profile: str
    hostname: str | None = None
    operating_system: str | None = None
    app_version: str | None = None
    connection_state: str
    last_seen_at: datetime
    last_local_sync_at: datetime | None = None


class SyncSpokeListResponse(BaseModel):
    records: list[SyncSpokeRecord]


class SyncStatusResponse(BaseModel):
    hub_device_id: str | None = None
    source_device_id: str | None = None
    branch_cursor: int
    last_pull_cursor: int
    last_heartbeat_at: datetime | None = None
    last_successful_push_at: datetime | None = None
    last_successful_pull_at: datetime | None = None
    last_successful_push_mutations: int | None = None
    last_idempotency_key: str | None = None
    open_conflict_count: int
    failed_push_count: int
    connected_spoke_count: int
    local_outbox_depth: int
    pending_mutation_count: int
    oldest_unsynced_mutation_age_seconds: int | None = None
    runtime_state: str
    last_local_spoke_sync_at: datetime | None = None


class SyncConflictRecord(BaseModel):
    id: str
    device_id: str
    source_idempotency_key: str
    table_name: str
    record_id: str
    reason: str
    message: str | None = None
    client_version: int | None = None
    server_version: int | None = None
    retry_strategy: str | None = None
    status: str
    created_at: datetime


class SyncConflictListResponse(BaseModel):
    records: list[SyncConflictRecord]


class SyncEnvelopeRecord(BaseModel):
    id: str
    device_id: str
    idempotency_key: str
    transport: str
    direction: str
    entity_type: str
    entity_id: str | None = None
    status: str
    attempt_count: int
    last_error: str | None = None
    created_at: datetime


class SyncEnvelopeListResponse(BaseModel):
    records: list[SyncEnvelopeRecord]
