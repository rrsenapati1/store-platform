from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_current_sync_device, get_session
from ..schemas import (
    SyncConflictResponse,
    SyncConflictListResponse,
    SyncConflictRecord,
    SyncEnvelopeListResponse,
    SyncEnvelopeRecord,
    SyncHeartbeatResponse,
    SyncPullRecordResponse,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    SyncSpokeListResponse,
    SyncSpokeObserveRequest,
    SyncSpokeObserveResponse,
    SyncSpokeRecord,
    SyncStatusResponse,
)
from ..services import ActorContext, SyncDeviceContext, SyncRuntimeService, assert_branch_any_capability

router = APIRouter(tags=["sync_runtime"])


def _assert_runtime_monitoring_access(actor: ActorContext, *, tenant_id: str, branch_id: str) -> None:
    assert_branch_any_capability(
        actor,
        tenant_id=tenant_id,
        branch_id=branch_id,
        capabilities=("sales.bill", "sales.return", "refund.approve"),
    )


@router.get("/v1/sync/heartbeat", response_model=SyncHeartbeatResponse)
async def sync_heartbeat(
    connected_spoke_count: int = Query(default=0, ge=0),
    last_local_spoke_sync_at: datetime | None = Query(default=None),
    oldest_unsynced_mutation_age_seconds: int = Query(default=0, ge=0),
    local_outbox_depth: int = Query(default=0, ge=0),
    runtime_state: str = Query(default="CURRENT"),
    device: SyncDeviceContext = Depends(get_current_sync_device),
    session: AsyncSession = Depends(get_session),
) -> SyncHeartbeatResponse:
    service = SyncRuntimeService(session)
    record = await service.record_heartbeat(
        device=device,
        connected_spoke_count=connected_spoke_count,
        last_local_spoke_sync_at=last_local_spoke_sync_at,
        oldest_unsynced_mutation_age_seconds=oldest_unsynced_mutation_age_seconds,
        local_outbox_depth=local_outbox_depth,
        runtime_state=runtime_state.upper(),
    )
    return SyncHeartbeatResponse(**record)


@router.post("/v1/sync/spokes/observe", response_model=SyncSpokeObserveResponse)
async def observe_sync_spokes(
    payload: SyncSpokeObserveRequest,
    device: SyncDeviceContext = Depends(get_current_sync_device),
    session: AsyncSession = Depends(get_session),
) -> SyncSpokeObserveResponse:
    service = SyncRuntimeService(session)
    response = await service.observe_spokes(
        device=device,
        spokes=[spoke.model_dump() for spoke in payload.spokes],
    )
    return SyncSpokeObserveResponse(**response)


@router.post("/v1/sync/push", response_model=SyncPushResponse)
async def sync_push(
    payload: SyncPushRequest,
    device: SyncDeviceContext = Depends(get_current_sync_device),
    session: AsyncSession = Depends(get_session),
) -> SyncPushResponse:
    service = SyncRuntimeService(session)
    response = await service.push(
        device=device,
        idempotency_key=payload.idempotency_key,
        mutations=[mutation.model_dump() for mutation in payload.mutations],
    )
    return SyncPushResponse(
        duplicate=response["duplicate"],
        accepted_mutations=response["accepted_mutations"],
        conflict_count=response["conflict_count"],
        conflicts=[SyncConflictResponse(**record) for record in response["conflicts"]],
        server_cursor=response["server_cursor"],
    )


@router.get("/v1/sync/pull", response_model=SyncPullResponse)
async def sync_pull(
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    device: SyncDeviceContext = Depends(get_current_sync_device),
    session: AsyncSession = Depends(get_session),
) -> SyncPullResponse:
    service = SyncRuntimeService(session)
    response = await service.pull(device=device, cursor=cursor, limit=limit)
    return SyncPullResponse(
        cursor=response["cursor"],
        records=[SyncPullRecordResponse(**record) for record in response["records"]],
    )


@router.get("/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SyncStatusResponse:
    _assert_runtime_monitoring_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SyncRuntimeService(session)
    return SyncStatusResponse(**(await service.get_sync_status(tenant_id=tenant_id, branch_id=branch_id)))


@router.get("/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-conflicts", response_model=SyncConflictListResponse)
async def list_sync_conflicts(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SyncConflictListResponse:
    _assert_runtime_monitoring_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SyncRuntimeService(session)
    records = await service.list_sync_conflicts(tenant_id=tenant_id, branch_id=branch_id)
    return SyncConflictListResponse(records=[SyncConflictRecord(**record) for record in records])


@router.get("/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-envelopes", response_model=SyncEnvelopeListResponse)
async def list_sync_envelopes(
    tenant_id: str,
    branch_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SyncEnvelopeListResponse:
    _assert_runtime_monitoring_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SyncRuntimeService(session)
    records = await service.list_sync_envelopes(tenant_id=tenant_id, branch_id=branch_id, limit=limit)
    return SyncEnvelopeListResponse(records=[SyncEnvelopeRecord(**record) for record in records])


@router.get("/v1/tenants/{tenant_id}/branches/{branch_id}/runtime/sync-spokes", response_model=SyncSpokeListResponse)
async def list_sync_spokes(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> SyncSpokeListResponse:
    _assert_runtime_monitoring_access(actor, tenant_id=tenant_id, branch_id=branch_id)
    service = SyncRuntimeService(session)
    records = await service.list_sync_spokes(tenant_id=tenant_id, branch_id=branch_id)
    return SyncSpokeListResponse(records=[SyncSpokeRecord(**record) for record in records])
