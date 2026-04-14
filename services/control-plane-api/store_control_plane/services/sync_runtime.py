from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, SyncRuntimeRepository, TenantRepository, WorkforceRepository
from ..utils import utc_now
from .sync_runtime_auth import SyncDeviceContext


def _request_hash(payload: dict[str, object]) -> str:
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


class SyncRuntimeService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._workforce_repo = WorkforceRepository(session)
        self._sync_repo = SyncRuntimeRepository(session)
        self._audit_repo = AuditRepository(session)

    async def record_heartbeat(
        self,
        *,
        device: SyncDeviceContext,
        connected_spoke_count: int,
        last_local_spoke_sync_at: datetime | None,
        oldest_unsynced_mutation_age_seconds: int,
        local_outbox_depth: int,
        runtime_state: str,
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=device.tenant_id, branch_id=device.branch_id)
        device_record = await self._workforce_repo.get_device_registration(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
        )
        if device_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        now = utc_now()
        await self._workforce_repo.touch_device_registration(device=device_record, seen_at=now)
        envelope = await self._sync_repo.create_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=f"heartbeat-{now.isoformat()}",
            direction="INGRESS",
            entity_type="sync_heartbeat",
            payload_json={
                "connected_spoke_count": connected_spoke_count,
                "last_local_spoke_sync_at": last_local_spoke_sync_at.isoformat() if last_local_spoke_sync_at else None,
                "oldest_unsynced_mutation_age_seconds": oldest_unsynced_mutation_age_seconds,
                "local_outbox_depth": local_outbox_depth,
                "runtime_state": runtime_state,
            },
        )
        branch_cursor = await self._sync_repo.get_latest_branch_cursor(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        status_record = await self._sync_repo.upsert_hub_sync_status(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            source_device_id=device.device_code,
            updates={
                "last_heartbeat_at": now,
                "branch_cursor": branch_cursor,
                "pending_mutation_count": local_outbox_depth,
                "connected_spoke_count": connected_spoke_count,
                "local_outbox_depth": local_outbox_depth,
                "oldest_unsynced_mutation_age_seconds": oldest_unsynced_mutation_age_seconds,
                "runtime_state": runtime_state,
                "last_local_spoke_sync_at": last_local_spoke_sync_at,
            },
        )
        response = {
            "status": "current",
            "runtime_state": status_record.runtime_state,
            "connected_spoke_count": status_record.connected_spoke_count,
            "local_outbox_depth": status_record.local_outbox_depth,
            "branch_cursor": status_record.branch_cursor,
            "last_heartbeat_at": status_record.last_heartbeat_at,
        }
        persisted_response = _json_ready(response)
        await self._sync_repo.finalize_sync_envelope(
            envelope=envelope,
            status="SYNCED",
            response_payload=persisted_response,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=None,
            action="sync_runtime.heartbeat",
            entity_type="device_registration",
            entity_id=device.device_id,
            payload=persisted_response,
        )
        await self._session.commit()
        return response

    async def observe_spokes(
        self,
        *,
        device: SyncDeviceContext,
        spokes: list[dict[str, object]],
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=device.tenant_id, branch_id=device.branch_id)
        observed_at = utc_now()
        envelope = await self._sync_repo.create_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=f"spokes-{observed_at.isoformat()}",
            direction="INGRESS",
            entity_type="sync_spoke_observe",
            payload_json={"spokes": [_json_ready(spoke) for spoke in spokes]},
        )
        records = await self._sync_repo.replace_hub_spoke_observations(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            observations=spokes,
            observed_at=observed_at,
        )
        connected_spoke_count = sum(1 for record in records if record.connection_state == "CONNECTED")
        latest_local_spoke_sync_at = max(
            (record.last_local_sync_at for record in records if record.last_local_sync_at is not None),
            default=None,
        )
        await self._sync_repo.upsert_hub_sync_status(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            source_device_id=device.device_code,
            updates={
                "connected_spoke_count": connected_spoke_count,
                "last_local_spoke_sync_at": latest_local_spoke_sync_at,
            },
        )
        response = {
            "observed_spoke_count": len(records),
            "connected_spoke_count": connected_spoke_count,
            "last_local_spoke_sync_at": latest_local_spoke_sync_at,
        }
        await self._sync_repo.finalize_sync_envelope(
            envelope=envelope,
            status="SYNCED",
            response_payload=_json_ready(response),
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=None,
            action="sync_runtime.spoke_observe",
            entity_type="device_registration",
            entity_id=device.device_id,
            payload=_json_ready(response),
        )
        await self._session.commit()
        return response

    async def push(
        self,
        *,
        device: SyncDeviceContext,
        idempotency_key: str,
        mutations: list[dict[str, object]],
    ) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=device.tenant_id, branch_id=device.branch_id)
        existing_envelope = await self._sync_repo.get_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=idempotency_key,
            direction="INGRESS",
        )
        if existing_envelope is not None:
            response = dict(existing_envelope.response_payload)
            response["duplicate"] = True
            response["accepted_mutations"] = 0
            return response

        envelope = await self._sync_repo.create_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=idempotency_key,
            direction="INGRESS",
            entity_type="sync_push",
            payload_json={"mutations": mutations},
        )

        accepted_mutations = 0
        conflicts: list[dict[str, object]] = []
        next_server_version = await self._sync_repo.get_latest_branch_cursor(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        for index, mutation in enumerate(mutations):
            table_name = str(mutation["table_name"])
            record_id = str(mutation["record_id"])
            operation = str(mutation["operation"])
            payload = dict(mutation.get("payload") or {})
            client_version = int(mutation.get("client_version") or 1)
            expected_server_version = int(mutation.get("expected_server_version") or 0)
            current_server_version = await self._sync_repo.get_current_record_version(
                tenant_id=device.tenant_id,
                branch_id=device.branch_id,
                table_name=table_name,
                record_id=record_id,
            )
            mutation_hash = _request_hash(
                {
                    "table_name": table_name,
                    "record_id": record_id,
                    "operation": operation,
                    "payload": payload,
                    "client_version": client_version,
                    "expected_server_version": expected_server_version,
                }
            )
            if current_server_version != expected_server_version:
                conflict = await self._sync_repo.create_sync_conflict(
                    tenant_id=device.tenant_id,
                    branch_id=device.branch_id,
                    device_id=device.device_id,
                    source_idempotency_key=idempotency_key,
                    conflict_index=index,
                    request_hash=mutation_hash,
                    table_name=table_name,
                    record_id=record_id,
                    reason="VERSION_MISMATCH",
                    message="Client attempted to write against a stale server version",
                    client_version=client_version,
                    server_version=current_server_version,
                    retry_strategy="PULL_LATEST_THEN_RETRY",
                )
                conflicts.append(
                    {
                        "id": conflict.id,
                        "table_name": conflict.table_name,
                        "record_id": conflict.record_id,
                        "reason": conflict.reason,
                        "retry_strategy": conflict.retry_strategy,
                        "client_version": conflict.client_version,
                        "server_version": conflict.server_version,
                    }
                )
                continue
            next_server_version += 1
            await self._sync_repo.create_sync_mutation(
                tenant_id=device.tenant_id,
                branch_id=device.branch_id,
                device_id=device.device_id,
                idempotency_key=idempotency_key,
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                client_version=client_version,
                expected_server_version=expected_server_version,
                server_version=next_server_version,
                request_hash=mutation_hash,
                payload_json=payload,
            )
            accepted_mutations += 1

        branch_cursor = await self._sync_repo.get_latest_branch_cursor(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        await self._sync_repo.upsert_hub_sync_status(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            source_device_id=device.device_code,
            updates={
                "last_successful_push_at": utc_now() if accepted_mutations else None,
                "last_successful_push_mutations": accepted_mutations,
                "last_idempotency_key": idempotency_key,
                "branch_cursor": branch_cursor,
            },
        )
        response = {
            "duplicate": False,
            "accepted_mutations": accepted_mutations,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "server_cursor": branch_cursor,
        }
        await self._sync_repo.finalize_sync_envelope(
            envelope=envelope,
            status="CONFLICT" if conflicts else "SYNCED",
            response_payload=_json_ready(response),
            last_error="Version conflict detected" if conflicts else None,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=None,
            action="sync_runtime.push",
            entity_type="sync_envelope",
            entity_id=envelope.id,
            payload=_json_ready(response),
        )
        await self._session.commit()
        return response

    async def pull(self, *, device: SyncDeviceContext, cursor: int, limit: int) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=device.tenant_id, branch_id=device.branch_id)
        envelope = await self._sync_repo.create_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=f"pull-{device.device_id}-{cursor}-{limit}-{utc_now().isoformat()}",
            direction="EGRESS",
            entity_type="sync_pull",
            payload_json={"cursor": cursor, "limit": limit},
        )
        mutations = await self._sync_repo.list_sync_mutations_since(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            cursor=cursor,
            limit=limit,
        )
        next_cursor = cursor
        records: list[dict[str, object]] = []
        for mutation in mutations:
            next_cursor = max(next_cursor, mutation.server_version)
            records.append(
                {
                    "table_name": mutation.table_name,
                    "record_id": mutation.record_id,
                    "operation": mutation.operation,
                    "payload": mutation.payload_json,
                    "client_version": mutation.client_version,
                    "expected_server_version": mutation.expected_server_version,
                    "server_version": mutation.server_version,
                }
            )
        await self._sync_repo.upsert_hub_sync_status(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            source_device_id=device.device_code,
            updates={
                "last_successful_pull_at": utc_now(),
                "last_pull_cursor": next_cursor,
                "branch_cursor": await self._sync_repo.get_latest_branch_cursor(
                    tenant_id=device.tenant_id,
                    branch_id=device.branch_id,
                ),
            },
        )
        response = {"cursor": next_cursor, "records": records}
        await self._sync_repo.finalize_sync_envelope(
            envelope=envelope,
            status="SYNCED",
            response_payload=_json_ready(response),
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=None,
            action="sync_runtime.pull",
            entity_type="sync_envelope",
            entity_id=envelope.id,
            payload=_json_ready({"cursor": next_cursor, "record_count": len(records)}),
        )
        await self._session.commit()
        return response

    async def get_sync_status(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        status_record = await self._sync_repo.get_hub_sync_status(tenant_id=tenant_id, branch_id=branch_id)
        if status_record is None:
            return {
                "hub_device_id": None,
                "branch_cursor": 0,
                "last_pull_cursor": 0,
                "open_conflict_count": 0,
                "failed_push_count": 0,
                "connected_spoke_count": 0,
                "local_outbox_depth": 0,
                "pending_mutation_count": 0,
                "runtime_state": "UNKNOWN",
                "last_heartbeat_at": None,
                "last_successful_push_at": None,
                "last_successful_pull_at": None,
                "last_local_spoke_sync_at": None,
            }
        return {
            "hub_device_id": status_record.hub_device_id,
            "source_device_id": status_record.source_device_id,
            "branch_cursor": status_record.branch_cursor,
            "last_pull_cursor": status_record.last_pull_cursor,
            "last_heartbeat_at": status_record.last_heartbeat_at,
            "last_successful_push_at": status_record.last_successful_push_at,
            "last_successful_pull_at": status_record.last_successful_pull_at,
            "last_successful_push_mutations": status_record.last_successful_push_mutations,
            "last_idempotency_key": status_record.last_idempotency_key,
            "open_conflict_count": await self._sync_repo.count_open_sync_conflicts(
                tenant_id=tenant_id,
                branch_id=branch_id,
            ),
            "failed_push_count": await self._sync_repo.count_failed_pushes(tenant_id=tenant_id, branch_id=branch_id),
            "connected_spoke_count": status_record.connected_spoke_count,
            "local_outbox_depth": status_record.local_outbox_depth,
            "pending_mutation_count": status_record.pending_mutation_count,
            "oldest_unsynced_mutation_age_seconds": status_record.oldest_unsynced_mutation_age_seconds,
            "runtime_state": status_record.runtime_state,
            "last_local_spoke_sync_at": status_record.last_local_spoke_sync_at,
        }

    async def list_sync_conflicts(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        records = await self._sync_repo.list_open_sync_conflicts(tenant_id=tenant_id, branch_id=branch_id)
        return [
            {
                "id": record.id,
                "device_id": record.device_id,
                "source_idempotency_key": record.source_idempotency_key,
                "table_name": record.table_name,
                "record_id": record.record_id,
                "reason": record.reason,
                "message": record.message,
                "client_version": record.client_version,
                "server_version": record.server_version,
                "retry_strategy": record.retry_strategy,
                "status": record.status,
                "created_at": record.created_at,
            }
            for record in records
        ]

    async def list_sync_envelopes(self, *, tenant_id: str, branch_id: str, limit: int) -> list[dict[str, object]]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        records = await self._sync_repo.list_sync_envelopes(tenant_id=tenant_id, branch_id=branch_id, limit=limit)
        return [
            {
                "id": record.id,
                "device_id": record.device_id,
                "idempotency_key": record.idempotency_key,
                "transport": record.transport,
                "direction": record.direction,
                "entity_type": record.entity_type,
                "entity_id": record.entity_id,
                "status": record.status,
                "attempt_count": record.attempt_count,
                "last_error": record.last_error,
                "created_at": record.created_at,
            }
            for record in records
        ]

    async def list_sync_spokes(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        records = await self._sync_repo.list_hub_spoke_observations(tenant_id=tenant_id, branch_id=branch_id)
        return [
            {
                "spoke_device_id": record.spoke_device_id,
                "hub_device_id": record.hub_device_id,
                "runtime_kind": record.runtime_kind,
                "hostname": record.hostname,
                "operating_system": record.operating_system,
                "app_version": record.app_version,
                "connection_state": record.connection_state,
                "last_seen_at": record.last_seen_at,
                "last_local_sync_at": record.last_local_sync_at,
            }
            for record in records
        ]

    async def _assert_branch_exists(self, *, tenant_id: str, branch_id: str) -> None:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
