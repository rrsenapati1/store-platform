from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import BillingPlan, SubscriptionWebhookEvent, TenantBillingOverride, TenantEntitlement, TenantSubscription
from ..utils import new_id


class CommerceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_billing_plan(
        self,
        *,
        code: str,
        display_name: str,
        billing_cadence: str,
        currency_code: str,
        amount_minor: int,
        trial_days: int,
        branch_limit: int,
        device_limit: int,
        offline_runtime_hours: int,
        grace_window_days: int,
        feature_flags: dict,
        provider_plan_refs: dict,
        is_default: bool = False,
        status: str = "ACTIVE",
    ) -> BillingPlan:
        if is_default:
            for existing_plan in await self.list_billing_plans():
                existing_plan.is_default = False
        plan = BillingPlan(
            id=new_id(),
            code=code,
            display_name=display_name,
            billing_cadence=billing_cadence,
            currency_code=currency_code,
            amount_minor=amount_minor,
            trial_days=trial_days,
            branch_limit=branch_limit,
            device_limit=device_limit,
            offline_runtime_hours=offline_runtime_hours,
            grace_window_days=grace_window_days,
            feature_flags=feature_flags,
            provider_plan_refs=provider_plan_refs,
            is_default=is_default,
            status=status,
        )
        self._session.add(plan)
        await self._session.flush()
        return plan

    async def get_billing_plan(self, *, plan_id: str) -> BillingPlan | None:
        return await self._session.get(BillingPlan, plan_id)

    async def get_billing_plan_by_code(self, *, code: str) -> BillingPlan | None:
        statement = select(BillingPlan).where(BillingPlan.code == code)
        return await self._session.scalar(statement)

    async def list_billing_plans(self) -> list[BillingPlan]:
        statement = select(BillingPlan).order_by(BillingPlan.created_at.asc(), BillingPlan.id.asc())
        return list((await self._session.scalars(statement)).all())

    async def get_default_billing_plan(self) -> BillingPlan | None:
        statement = select(BillingPlan).where(BillingPlan.is_default.is_(True)).order_by(BillingPlan.created_at.desc(), BillingPlan.id.desc())
        return await self._session.scalar(statement)

    async def create_tenant_subscription(
        self,
        *,
        tenant_id: str,
        billing_plan_id: str,
        provider_name: str | None,
        lifecycle_status: str,
        trial_started_at: datetime | None,
        trial_ends_at: datetime | None,
        provider_customer_id: str | None = None,
        provider_subscription_id: str | None = None,
        mandate_status: str | None = None,
        current_period_started_at: datetime | None = None,
        current_period_ends_at: datetime | None = None,
        grace_until: datetime | None = None,
        canceled_at: datetime | None = None,
        last_provider_event_id: str | None = None,
        last_provider_event_at: datetime | None = None,
    ) -> TenantSubscription:
        subscription = TenantSubscription(
            id=new_id(),
            tenant_id=tenant_id,
            billing_plan_id=billing_plan_id,
            provider_name=provider_name,
            provider_customer_id=provider_customer_id,
            provider_subscription_id=provider_subscription_id,
            lifecycle_status=lifecycle_status,
            mandate_status=mandate_status,
            trial_started_at=trial_started_at,
            trial_ends_at=trial_ends_at,
            current_period_started_at=current_period_started_at,
            current_period_ends_at=current_period_ends_at,
            grace_until=grace_until,
            canceled_at=canceled_at,
            last_provider_event_id=last_provider_event_id,
            last_provider_event_at=last_provider_event_at,
        )
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def get_current_subscription(self, *, tenant_id: str) -> TenantSubscription | None:
        active_statuses = ("TRIALING", "ACTIVE", "GRACE", "SUSPENDED")
        statement = (
            select(TenantSubscription)
            .where(
                TenantSubscription.tenant_id == tenant_id,
                TenantSubscription.lifecycle_status.in_(active_statuses),
            )
            .order_by(TenantSubscription.created_at.desc(), TenantSubscription.id.desc())
        )
        return await self._session.scalar(statement)

    async def find_subscription_by_provider_reference(
        self,
        *,
        provider_name: str,
        provider_subscription_id: str,
    ) -> TenantSubscription | None:
        statement = select(TenantSubscription).where(
            TenantSubscription.provider_name == provider_name,
            TenantSubscription.provider_subscription_id == provider_subscription_id,
        )
        return await self._session.scalar(statement)

    async def upsert_tenant_entitlement(
        self,
        *,
        tenant_id: str,
        billing_plan_id: str | None,
        active_plan_code: str,
        lifecycle_status: str,
        branch_limit: int,
        device_limit: int,
        offline_runtime_hours: int,
        grace_until: datetime | None,
        suspend_at: datetime | None,
        feature_flags: dict,
        policy_source: str,
        policy_metadata: dict,
    ) -> TenantEntitlement:
        entitlement = await self.get_tenant_entitlement(tenant_id=tenant_id)
        if entitlement is None:
            entitlement = TenantEntitlement(
                id=new_id(),
                tenant_id=tenant_id,
                billing_plan_id=billing_plan_id,
                active_plan_code=active_plan_code,
                lifecycle_status=lifecycle_status,
                branch_limit=branch_limit,
                device_limit=device_limit,
                offline_runtime_hours=offline_runtime_hours,
                grace_until=grace_until,
                suspend_at=suspend_at,
                feature_flags=feature_flags,
                policy_source=policy_source,
                policy_metadata=policy_metadata,
            )
            self._session.add(entitlement)
        else:
            entitlement.billing_plan_id = billing_plan_id
            entitlement.active_plan_code = active_plan_code
            entitlement.lifecycle_status = lifecycle_status
            entitlement.branch_limit = branch_limit
            entitlement.device_limit = device_limit
            entitlement.offline_runtime_hours = offline_runtime_hours
            entitlement.grace_until = grace_until
            entitlement.suspend_at = suspend_at
            entitlement.feature_flags = feature_flags
            entitlement.policy_source = policy_source
            entitlement.policy_metadata = policy_metadata
        await self._session.flush()
        return entitlement

    async def get_tenant_entitlement(self, *, tenant_id: str) -> TenantEntitlement | None:
        statement = select(TenantEntitlement).where(TenantEntitlement.tenant_id == tenant_id)
        return await self._session.scalar(statement)

    async def record_webhook_event(
        self,
        *,
        provider_name: str,
        provider_event_id: str,
        tenant_id: str | None,
        event_type: str,
        payload: dict,
    ) -> SubscriptionWebhookEvent:
        existing = await self.get_webhook_event(provider_name=provider_name, provider_event_id=provider_event_id)
        if existing is not None:
            return existing
        event = SubscriptionWebhookEvent(
            id=new_id(),
            provider_name=provider_name,
            provider_event_id=provider_event_id,
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_webhook_event(self, *, provider_name: str, provider_event_id: str) -> SubscriptionWebhookEvent | None:
        statement = select(SubscriptionWebhookEvent).where(
            SubscriptionWebhookEvent.provider_name == provider_name,
            SubscriptionWebhookEvent.provider_event_id == provider_event_id,
        )
        return await self._session.scalar(statement)

    async def mark_webhook_event_processed(
        self,
        *,
        event: SubscriptionWebhookEvent,
        processing_status: str,
        error_message: str | None = None,
        processed_at: datetime | None = None,
    ) -> SubscriptionWebhookEvent:
        event.processing_status = processing_status
        event.error_message = error_message
        event.processed_at = processed_at
        await self._session.flush()
        return event

    async def list_webhook_events(self, *, provider_name: str | None = None, tenant_id: str | None = None) -> list[SubscriptionWebhookEvent]:
        statement: Select[tuple[SubscriptionWebhookEvent]] = select(SubscriptionWebhookEvent)
        if provider_name is not None:
            statement = statement.where(SubscriptionWebhookEvent.provider_name == provider_name)
        if tenant_id is not None:
            statement = statement.where(SubscriptionWebhookEvent.tenant_id == tenant_id)
        statement = statement.order_by(SubscriptionWebhookEvent.received_at.asc(), SubscriptionWebhookEvent.id.asc())
        return list((await self._session.scalars(statement)).all())

    async def create_billing_override(
        self,
        *,
        tenant_id: str,
        created_by_user_id: str | None,
        grants_lifecycle_status: str,
        branch_limit_override: int | None,
        device_limit_override: int | None,
        offline_runtime_hours_override: int | None,
        feature_flags_override: dict,
        reason: str,
        expires_at: datetime,
    ) -> TenantBillingOverride:
        override = TenantBillingOverride(
            id=new_id(),
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            grants_lifecycle_status=grants_lifecycle_status,
            branch_limit_override=branch_limit_override,
            device_limit_override=device_limit_override,
            offline_runtime_hours_override=offline_runtime_hours_override,
            feature_flags_override=feature_flags_override,
            reason=reason,
            expires_at=expires_at,
        )
        self._session.add(override)
        await self._session.flush()
        return override

    async def get_active_billing_override(self, *, tenant_id: str, now: datetime) -> TenantBillingOverride | None:
        statement = (
            select(TenantBillingOverride)
            .where(
                TenantBillingOverride.tenant_id == tenant_id,
                TenantBillingOverride.status == "ACTIVE",
                TenantBillingOverride.revoked_at.is_(None),
                TenantBillingOverride.expires_at > now,
            )
            .order_by(TenantBillingOverride.expires_at.desc(), TenantBillingOverride.created_at.desc())
        )
        return await self._session.scalar(statement)
