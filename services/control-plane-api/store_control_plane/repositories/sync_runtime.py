from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import HubSpokeObservation, HubSyncStatus, SyncConflict, SyncEnvelope, SyncMutationLog
from ..utils import new_id


class SyncRuntimeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_sync_envelope(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        idempotency_key: str,
        direction: str,
    ) -> SyncEnvelope | None:
        statement = select(SyncEnvelope).where(
            SyncEnvelope.tenant_id == tenant_id,
            SyncEnvelope.branch_id == branch_id,
            SyncEnvelope.device_id == device_id,
            SyncEnvelope.idempotency_key == idempotency_key,
            SyncEnvelope.direction == direction,
        )
        return await self._session.scalar(statement)

    async def create_sync_envelope(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        idempotency_key: str,
        direction: str,
        entity_type: str,
        payload_json: dict[str, object],
        entity_id: str | None = None,
    ) -> SyncEnvelope:
        envelope = SyncEnvelope(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            idempotency_key=idempotency_key,
            direction=direction,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=payload_json,
            response_payload={},
            status="QUEUED",
            attempt_count=1,
        )
        self._session.add(envelope)
        await self._session.flush()
        return envelope

    async def finalize_sync_envelope(
        self,
        *,
        envelope: SyncEnvelope,
        status: str,
        response_payload: dict[str, object],
        last_error: str | None = None,
    ) -> SyncEnvelope:
        envelope.status = status
        envelope.response_payload = response_payload
        envelope.last_error = last_error
        await self._session.flush()
        return envelope

    async def get_latest_branch_cursor(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.max(SyncMutationLog.server_version)).where(
            SyncMutationLog.tenant_id == tenant_id,
            SyncMutationLog.branch_id == branch_id,
        )
        value = await self._session.scalar(statement)
        return int(value or 0)

    async def get_current_record_version(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        table_name: str,
        record_id: str,
    ) -> int:
        statement = select(func.max(SyncMutationLog.server_version)).where(
            SyncMutationLog.tenant_id == tenant_id,
            SyncMutationLog.branch_id == branch_id,
            SyncMutationLog.table_name == table_name,
            SyncMutationLog.record_id == record_id,
        )
        value = await self._session.scalar(statement)
        return int(value or 0)

    async def create_sync_mutation(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        idempotency_key: str,
        table_name: str,
        record_id: str,
        operation: str,
        client_version: int,
        expected_server_version: int,
        server_version: int,
        request_hash: str,
        payload_json: dict[str, object],
    ) -> SyncMutationLog:
        record = SyncMutationLog(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            idempotency_key=idempotency_key,
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            client_version=client_version,
            expected_server_version=expected_server_version,
            server_version=server_version,
            request_hash=request_hash,
            payload_json=payload_json,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_sync_mutations_since(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        cursor: int,
        limit: int,
    ) -> list[SyncMutationLog]:
        statement = (
            select(SyncMutationLog)
            .where(
                SyncMutationLog.tenant_id == tenant_id,
                SyncMutationLog.branch_id == branch_id,
                SyncMutationLog.server_version > cursor,
            )
            .order_by(SyncMutationLog.server_version.asc(), SyncMutationLog.id.asc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def create_sync_conflict(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        device_id: str,
        source_idempotency_key: str,
        conflict_index: int,
        request_hash: str,
        table_name: str,
        record_id: str,
        reason: str,
        message: str,
        client_version: int,
        server_version: int,
        retry_strategy: str,
    ) -> SyncConflict:
        conflict = SyncConflict(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=device_id,
            source_idempotency_key=source_idempotency_key,
            conflict_index=conflict_index,
            request_hash=request_hash,
            table_name=table_name,
            record_id=record_id,
            reason=reason,
            message=message,
            client_version=client_version,
            server_version=server_version,
            retry_strategy=retry_strategy,
            status="OPEN",
        )
        self._session.add(conflict)
        await self._session.flush()
        return conflict

    async def list_open_sync_conflicts(self, *, tenant_id: str, branch_id: str) -> list[SyncConflict]:
        statement = (
            select(SyncConflict)
            .where(
                SyncConflict.tenant_id == tenant_id,
                SyncConflict.branch_id == branch_id,
                SyncConflict.status == "OPEN",
            )
            .order_by(SyncConflict.created_at.desc(), SyncConflict.id.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def count_open_sync_conflicts(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(SyncConflict.id)).where(
            SyncConflict.tenant_id == tenant_id,
            SyncConflict.branch_id == branch_id,
            SyncConflict.status == "OPEN",
        )
        value = await self._session.scalar(statement)
        return int(value or 0)

    async def list_sync_envelopes(self, *, tenant_id: str, branch_id: str, limit: int) -> list[SyncEnvelope]:
        statement = (
            select(SyncEnvelope)
            .where(
                SyncEnvelope.tenant_id == tenant_id,
                SyncEnvelope.branch_id == branch_id,
            )
            .order_by(SyncEnvelope.created_at.desc(), SyncEnvelope.id.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def count_failed_pushes(self, *, tenant_id: str, branch_id: str) -> int:
        statement = select(func.count(SyncEnvelope.id)).where(
            SyncEnvelope.tenant_id == tenant_id,
            SyncEnvelope.branch_id == branch_id,
            SyncEnvelope.entity_type == "sync_push",
            SyncEnvelope.status.in_(("CONFLICT", "FAILED")),
        )
        value = await self._session.scalar(statement)
        return int(value or 0)

    async def get_hub_sync_status(self, *, tenant_id: str, branch_id: str) -> HubSyncStatus | None:
        statement = select(HubSyncStatus).where(
            HubSyncStatus.tenant_id == tenant_id,
            HubSyncStatus.branch_id == branch_id,
        )
        return await self._session.scalar(statement)

    async def upsert_hub_sync_status(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        hub_device_id: str,
        source_device_id: str,
        updates: dict[str, object],
    ) -> HubSyncStatus:
        status_record = await self.get_hub_sync_status(tenant_id=tenant_id, branch_id=branch_id)
        if status_record is None:
            status_record = HubSyncStatus(
                id=new_id(),
                tenant_id=tenant_id,
                branch_id=branch_id,
                hub_device_id=hub_device_id,
                source_device_id=source_device_id,
            )
            self._session.add(status_record)
        status_record.hub_device_id = hub_device_id
        status_record.source_device_id = source_device_id
        for key, value in updates.items():
            setattr(status_record, key, value)
        await self._session.flush()
        return status_record

    async def list_hub_spoke_observations(
        self,
        *,
        tenant_id: str,
        branch_id: str,
    ) -> list[HubSpokeObservation]:
        statement = (
            select(HubSpokeObservation)
            .where(
                HubSpokeObservation.tenant_id == tenant_id,
                HubSpokeObservation.branch_id == branch_id,
            )
            .order_by(
                HubSpokeObservation.connection_state.asc(),
                HubSpokeObservation.last_seen_at.desc(),
                HubSpokeObservation.spoke_device_id.asc(),
            )
        )
        return list((await self._session.scalars(statement)).all())

    async def replace_hub_spoke_observations(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        hub_device_id: str,
        observations: list[dict[str, object]],
        observed_at,
    ) -> list[HubSpokeObservation]:
        statement = select(HubSpokeObservation).where(
            HubSpokeObservation.tenant_id == tenant_id,
            HubSpokeObservation.branch_id == branch_id,
            HubSpokeObservation.hub_device_id == hub_device_id,
        )
        existing_records = list((await self._session.scalars(statement)).all())
        existing_by_spoke = {record.spoke_device_id: record for record in existing_records}
        observed_spoke_ids: set[str] = set()

        for payload in observations:
            spoke_device_id = str(payload["spoke_device_id"])
            observed_spoke_ids.add(spoke_device_id)
            record = existing_by_spoke.get(spoke_device_id)
            if record is None:
                record = HubSpokeObservation(
                    id=new_id(),
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    hub_device_id=hub_device_id,
                    spoke_device_id=spoke_device_id,
                )
                self._session.add(record)
                existing_records.append(record)
            record.runtime_kind = str(payload["runtime_kind"])
            record.runtime_profile = str(payload.get("runtime_profile") or record.runtime_profile or "desktop_spoke")
            record.hostname = str(payload["hostname"]) if payload.get("hostname") else None
            record.operating_system = str(payload["operating_system"]) if payload.get("operating_system") else None
            record.app_version = str(payload["app_version"]) if payload.get("app_version") else None
            record.connection_state = str(payload["connection_state"])
            record.last_seen_at = observed_at
            record.last_local_sync_at = payload.get("last_local_sync_at")

        for record in existing_records:
            if record.spoke_device_id in observed_spoke_ids:
                continue
            record.connection_state = "DISCONNECTED"

        await self._session.flush()
        return sorted(
            existing_records,
            key=lambda record: (record.connection_state, -(record.last_seen_at.timestamp() if record.last_seen_at else 0), record.spoke_device_id),
        )
