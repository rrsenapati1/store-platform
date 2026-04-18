from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditEvent
from ..utils import new_id


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(
        self,
        *,
        tenant_id: str | None,
        branch_id: str | None,
        actor_user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        payload: dict,
    ) -> AuditEvent:
        event = AuditEvent(
            id=new_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_for_tenant(
        self,
        tenant_id: str,
        *,
        branch_id: str | None = None,
        action_prefixes: tuple[str, ...] | None = None,
    ) -> list[AuditEvent]:
        statement = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)
        if branch_id is not None:
            statement = statement.where(AuditEvent.branch_id == branch_id)
        if action_prefixes:
            action_filters = [AuditEvent.action.like(f"{prefix}%") for prefix in action_prefixes]
            statement = statement.where(or_(*action_filters))
        statement = statement.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        return list((await self._session.scalars(statement)).all())
