from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..repositories import CommerceRepository, TenantRepository
from ..utils import utc_now
from .subscription_providers import build_subscription_provider


DEFAULT_LAUNCH_PLAN = {
    "code": "launch-starter",
    "display_name": "Launch Starter",
    "billing_cadence": "monthly",
    "currency_code": "INR",
    "amount_minor": 149900,
    "trial_days": 14,
    "branch_limit": 2,
    "device_limit": 4,
    "offline_runtime_hours": 48,
    "grace_window_days": 5,
    "feature_flags": {
        "offline_continuity": True,
        "desktop_runtime": True,
    },
    "provider_plan_refs": {
        "cashfree": "cf_plan_launch_starter",
        "razorpay": "rp_plan_launch_starter",
    },
}


class CommerceService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self._session = session
        self._settings = settings
        self._commerce_repo = CommerceRepository(session)
        self._tenant_repo = TenantRepository(session)

    async def ensure_default_billing_plan(self) -> dict[str, object]:
        plan = await self._commerce_repo.get_default_billing_plan()
        if plan is None:
            plan = await self._commerce_repo.create_billing_plan(
                is_default=True,
                status="ACTIVE",
                **DEFAULT_LAUNCH_PLAN,
            )
        return self._serialize_billing_plan(plan)

    async def list_billing_plans(self) -> list[dict[str, object]]:
        default_plan = await self._commerce_repo.get_default_billing_plan()
        if default_plan is None:
            await self.ensure_default_billing_plan()
        plans = await self._commerce_repo.list_billing_plans()
        return [self._serialize_billing_plan(plan) for plan in plans]

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
        feature_flags: dict[str, object],
        provider_plan_refs: dict[str, str],
        is_default: bool,
    ) -> dict[str, object]:
        existing = await self._commerce_repo.get_billing_plan_by_code(code=code)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Billing plan code already exists")
        plan = await self._commerce_repo.create_billing_plan(
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
        )
        await self._session.commit()
        return self._serialize_billing_plan(plan)

    async def issue_trial_subscription(self, *, tenant_id: str) -> dict[str, dict[str, object]]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        current_subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if current_subscription is not None:
            entitlement = await self._commerce_repo.get_tenant_entitlement(tenant_id=tenant_id)
            return {
                "subscription": self._serialize_subscription(current_subscription),
                "entitlement": self._serialize_entitlement(entitlement) if entitlement is not None else {},
            }

        default_plan = await self._commerce_repo.get_default_billing_plan()
        if default_plan is None:
            default_plan = await self._commerce_repo.create_billing_plan(
                is_default=True,
                status="ACTIVE",
                **DEFAULT_LAUNCH_PLAN,
            )
        now = utc_now()
        trial_ends_at = now + timedelta(days=default_plan.trial_days)
        subscription = await self._commerce_repo.create_tenant_subscription(
            tenant_id=tenant_id,
            billing_plan_id=default_plan.id,
            provider_name=None,
            lifecycle_status="TRIALING",
            trial_started_at=now,
            trial_ends_at=trial_ends_at,
        )
        entitlement = await self._commerce_repo.upsert_tenant_entitlement(
            tenant_id=tenant_id,
            billing_plan_id=default_plan.id,
            active_plan_code=default_plan.code,
            lifecycle_status="TRIALING",
            branch_limit=default_plan.branch_limit,
            device_limit=default_plan.device_limit,
            offline_runtime_hours=default_plan.offline_runtime_hours,
            grace_until=None,
            suspend_at=trial_ends_at + timedelta(days=default_plan.grace_window_days),
            feature_flags=default_plan.feature_flags,
            policy_source="subscription",
            policy_metadata={"reason": "trial_issued"},
        )
        await self._session.flush()
        return {
            "subscription": self._serialize_subscription(subscription),
            "entitlement": self._serialize_entitlement(entitlement),
        }

    async def bootstrap_subscription_checkout(self, *, tenant_id: str, provider_name: str) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            await self.issue_trial_subscription(tenant_id=tenant_id)
            subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to initialize subscription")
        plan = await self._commerce_repo.get_billing_plan(plan_id=subscription.billing_plan_id)
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing plan not found")
        provider = build_subscription_provider(provider_name, self._settings)
        checkout = provider.create_subscription_checkout(
            tenant_id=tenant.id,
            plan_code=plan.code,
            tenant_name=tenant.name,
        )
        subscription.provider_name = checkout["provider_name"]
        subscription.provider_customer_id = checkout["provider_customer_id"]
        subscription.provider_subscription_id = checkout["provider_subscription_id"]
        subscription.mandate_status = checkout["mandate_status"]
        await self._session.commit()
        return checkout

    async def get_tenant_lifecycle_summary(self, *, tenant_id: str) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            await self.issue_trial_subscription(tenant_id=tenant_id)
            subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Subscription not initialized")
        entitlement = await self._rebuild_entitlement(tenant_id=tenant_id, tenant_status=tenant.status, subscription=subscription)
        active_override = await self._commerce_repo.get_active_billing_override(tenant_id=tenant_id, now=utc_now())
        await self._session.flush()
        return {
            "tenant_id": tenant_id,
            "subscription": self._serialize_subscription(subscription),
            "entitlement": self._serialize_entitlement(entitlement),
            "active_override": self._serialize_billing_override(active_override) if active_override is not None else None,
        }

    async def suspend_tenant_commercial_access(self, *, tenant_id: str, reason: str) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        tenant.status = "SUSPENDED"
        subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            await self.issue_trial_subscription(tenant_id=tenant_id)
            subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        entitlement = await self._rebuild_entitlement(
            tenant_id=tenant_id,
            tenant_status=tenant.status,
            subscription=subscription,
            manual_metadata={"reason": reason},
        )
        await self._session.commit()
        return {
            "tenant_id": tenant_id,
            "subscription": self._serialize_subscription(subscription),
            "entitlement": self._serialize_entitlement(entitlement),
            "active_override": None,
        }

    async def reactivate_tenant_commercial_access(self, *, tenant_id: str) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        tenant.status = "ACTIVE"
        subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            await self.issue_trial_subscription(tenant_id=tenant_id)
            subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        entitlement = await self._rebuild_entitlement(tenant_id=tenant_id, tenant_status=tenant.status, subscription=subscription)
        active_override = await self._commerce_repo.get_active_billing_override(tenant_id=tenant_id, now=utc_now())
        await self._session.commit()
        return {
            "tenant_id": tenant_id,
            "subscription": self._serialize_subscription(subscription),
            "entitlement": self._serialize_entitlement(entitlement),
            "active_override": self._serialize_billing_override(active_override) if active_override is not None else None,
        }

    async def create_billing_override(
        self,
        *,
        tenant_id: str,
        created_by_user_id: str | None,
        grants_lifecycle_status: str,
        branch_limit_override: int | None,
        device_limit_override: int | None,
        offline_runtime_hours_override: int | None,
        feature_flags_override: dict[str, object],
        reason: str,
        expires_at: datetime,
    ) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        override = await self._commerce_repo.create_billing_override(
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
        subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        if subscription is None:
            await self.issue_trial_subscription(tenant_id=tenant_id)
            subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        entitlement = await self._rebuild_entitlement(tenant_id=tenant_id, tenant_status=tenant.status, subscription=subscription)
        await self._session.commit()
        return {
            "tenant_id": tenant_id,
            "subscription": self._serialize_subscription(subscription),
            "entitlement": self._serialize_entitlement(entitlement),
            "active_override": self._serialize_billing_override(override),
        }

    async def handle_provider_webhook(self, *, provider_name: str, payload: dict[str, object]) -> dict[str, object]:
        provider = build_subscription_provider(provider_name, self._settings)
        normalized_event = provider.normalize_webhook_payload(payload)
        recorded_event = await self._commerce_repo.record_webhook_event(
            provider_name=provider_name,
            provider_event_id=str(normalized_event["provider_event_id"]),
            tenant_id=str(normalized_event["tenant_id"]) if normalized_event.get("tenant_id") else None,
            event_type=str(normalized_event["event_type"]),
            payload=dict(normalized_event["payload"]),
        )
        if recorded_event.processing_status == "PROCESSED":
            return {"status": "ok", "event": self._serialize_webhook_event(recorded_event)}

        subscription = None
        tenant_id = normalized_event.get("tenant_id")
        if isinstance(tenant_id, str):
            subscription = await self._commerce_repo.get_current_subscription(tenant_id=tenant_id)
        provider_subscription_id = normalized_event.get("provider_subscription_id")
        if subscription is None and isinstance(provider_subscription_id, str):
            subscription = await self._commerce_repo.find_subscription_by_provider_reference(
                provider_name=provider_name,
                provider_subscription_id=provider_subscription_id,
            )
        if subscription is None:
            await self._commerce_repo.mark_webhook_event_processed(
                event=recorded_event,
                processing_status="IGNORED",
                error_message="Subscription not found",
                processed_at=utc_now(),
            )
            await self._session.flush()
            return {"status": "ignored", "event": self._serialize_webhook_event(recorded_event)}

        plan = await self._commerce_repo.get_billing_plan(plan_id=subscription.billing_plan_id)
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing plan not found")

        self._apply_normalized_event_to_subscription(
            subscription=subscription,
            plan=plan,
            normalized_event=normalized_event,
        )
        entitlement = await self._commerce_repo.upsert_tenant_entitlement(
            tenant_id=subscription.tenant_id,
            billing_plan_id=plan.id,
            active_plan_code=plan.code,
            lifecycle_status=subscription.lifecycle_status,
            branch_limit=plan.branch_limit,
            device_limit=plan.device_limit,
            offline_runtime_hours=plan.offline_runtime_hours,
            grace_until=subscription.grace_until,
            suspend_at=self._compute_suspend_at(subscription=subscription, plan=plan),
            feature_flags=plan.feature_flags,
            policy_source="subscription",
            policy_metadata={"last_event_type": normalized_event["event_type"]},
        )
        await self._commerce_repo.mark_webhook_event_processed(
            event=recorded_event,
            processing_status="PROCESSED",
            processed_at=utc_now(),
        )
        await self._session.commit()
        return {
            "status": "ok",
            "event": self._serialize_webhook_event(recorded_event),
            "subscription": self._serialize_subscription(subscription),
            "entitlement": self._serialize_entitlement(entitlement),
        }

    async def _rebuild_entitlement(
        self,
        *,
        tenant_id: str,
        tenant_status: str,
        subscription,
        manual_metadata: dict[str, object] | None = None,
    ):
        plan = await self._commerce_repo.get_billing_plan(plan_id=subscription.billing_plan_id)
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing plan not found")
        active_override = await self._commerce_repo.get_active_billing_override(tenant_id=tenant_id, now=utc_now())

        lifecycle_status = self._derive_base_lifecycle(subscription=subscription)
        branch_limit = plan.branch_limit
        device_limit = plan.device_limit
        offline_runtime_hours = plan.offline_runtime_hours
        feature_flags = dict(plan.feature_flags)
        policy_source = "subscription"
        policy_metadata: dict[str, object] = {"subscription_status": subscription.lifecycle_status}
        if active_override is not None:
            lifecycle_status = active_override.grants_lifecycle_status
            branch_limit = active_override.branch_limit_override or branch_limit
            device_limit = active_override.device_limit_override or device_limit
            offline_runtime_hours = active_override.offline_runtime_hours_override or offline_runtime_hours
            feature_flags.update(active_override.feature_flags_override)
            policy_source = "billing_override"
            policy_metadata = {"override_id": active_override.id}
        if tenant_status == "SUSPENDED":
            lifecycle_status = "SUSPENDED"
            policy_source = "tenant_status"
            policy_metadata = manual_metadata or {"tenant_status": tenant_status}
        return await self._commerce_repo.upsert_tenant_entitlement(
            tenant_id=tenant_id,
            billing_plan_id=plan.id,
            active_plan_code=plan.code,
            lifecycle_status=lifecycle_status,
            branch_limit=branch_limit,
            device_limit=device_limit,
            offline_runtime_hours=offline_runtime_hours,
            grace_until=subscription.grace_until,
            suspend_at=self._compute_suspend_at(subscription=subscription, plan=plan),
            feature_flags=feature_flags,
            policy_source=policy_source,
            policy_metadata=policy_metadata,
        )

    @staticmethod
    def _derive_base_lifecycle(*, subscription) -> str:
        if subscription.lifecycle_status in {"ACTIVE", "GRACE", "CANCELED"}:
            return "SUSPENDED" if subscription.lifecycle_status == "CANCELED" else subscription.lifecycle_status
        if subscription.lifecycle_status == "TRIALING" and subscription.trial_ends_at is not None:
            now = utc_now()
            if now <= subscription.trial_ends_at:
                return "TRIALING"
            if subscription.grace_until is not None and now <= subscription.grace_until:
                return "GRACE"
            return "SUSPENDED"
        return subscription.lifecycle_status

    def _apply_normalized_event_to_subscription(self, *, subscription, plan, normalized_event: dict[str, object]) -> None:
        event_type = str(normalized_event["event_type"])
        if normalized_event.get("provider_customer_id"):
            subscription.provider_customer_id = str(normalized_event["provider_customer_id"])
        if normalized_event.get("provider_subscription_id"):
            subscription.provider_subscription_id = str(normalized_event["provider_subscription_id"])
        subscription.provider_name = str(normalized_event["provider_name"])
        subscription.last_provider_event_id = str(normalized_event["provider_event_id"])
        subscription.last_provider_event_at = utc_now()

        if event_type in {"subscription.activated", "subscription.payment_captured"}:
            period_start = self._parse_datetime(normalized_event.get("current_period_started_at")) or utc_now()
            period_end = self._parse_datetime(normalized_event.get("current_period_ends_at")) or (period_start + timedelta(days=30))
            subscription.lifecycle_status = "ACTIVE"
            subscription.mandate_status = "ACTIVE"
            subscription.grace_until = None
            subscription.current_period_started_at = period_start
            subscription.current_period_ends_at = period_end
        elif event_type == "subscription.renewal_failed":
            subscription.lifecycle_status = "GRACE"
            subscription.mandate_status = "PAYMENT_FAILED"
            subscription.grace_until = self._parse_datetime(normalized_event.get("grace_until")) or (
                utc_now() + timedelta(days=plan.grace_window_days)
            )
        elif event_type == "subscription.canceled":
            subscription.lifecycle_status = "CANCELED"
            subscription.canceled_at = utc_now()
            subscription.grace_until = None
            subscription.mandate_status = "CANCELED"

    @staticmethod
    def _compute_suspend_at(*, subscription, plan) -> datetime | None:
        if subscription.lifecycle_status == "GRACE":
            return subscription.grace_until
        if subscription.lifecycle_status == "CANCELED":
            return subscription.canceled_at
        if subscription.lifecycle_status == "TRIALING":
            return subscription.trial_ends_at + timedelta(days=plan.grace_window_days) if subscription.trial_ends_at else None
        if subscription.current_period_ends_at is not None:
            return subscription.current_period_ends_at + timedelta(days=plan.grace_window_days)
        return None

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if isinstance(value, str) and value:
            return datetime.fromisoformat(value)
        return None

    @staticmethod
    def _serialize_billing_plan(plan) -> dict[str, object]:
        return {
            "id": plan.id,
            "code": plan.code,
            "display_name": plan.display_name,
            "billing_cadence": plan.billing_cadence,
            "currency_code": plan.currency_code,
            "amount_minor": plan.amount_minor,
            "trial_days": plan.trial_days,
            "branch_limit": plan.branch_limit,
            "device_limit": plan.device_limit,
            "offline_runtime_hours": plan.offline_runtime_hours,
            "grace_window_days": plan.grace_window_days,
            "feature_flags": dict(plan.feature_flags),
            "provider_plan_refs": dict(plan.provider_plan_refs),
            "is_default": plan.is_default,
            "status": plan.status,
        }

    @staticmethod
    def _serialize_subscription(subscription) -> dict[str, object]:
        return {
            "id": subscription.id,
            "tenant_id": subscription.tenant_id,
            "billing_plan_id": subscription.billing_plan_id,
            "provider_name": subscription.provider_name,
            "provider_customer_id": subscription.provider_customer_id,
            "provider_subscription_id": subscription.provider_subscription_id,
            "lifecycle_status": subscription.lifecycle_status,
            "mandate_status": subscription.mandate_status,
            "trial_started_at": subscription.trial_started_at.isoformat() if subscription.trial_started_at else None,
            "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
            "current_period_started_at": subscription.current_period_started_at.isoformat() if subscription.current_period_started_at else None,
            "current_period_ends_at": subscription.current_period_ends_at.isoformat() if subscription.current_period_ends_at else None,
            "grace_until": subscription.grace_until.isoformat() if subscription.grace_until else None,
            "canceled_at": subscription.canceled_at.isoformat() if subscription.canceled_at else None,
        }

    @staticmethod
    def _serialize_entitlement(entitlement) -> dict[str, object]:
        return {
            "id": entitlement.id,
            "tenant_id": entitlement.tenant_id,
            "billing_plan_id": entitlement.billing_plan_id,
            "active_plan_code": entitlement.active_plan_code,
            "lifecycle_status": entitlement.lifecycle_status,
            "branch_limit": entitlement.branch_limit,
            "device_limit": entitlement.device_limit,
            "offline_runtime_hours": entitlement.offline_runtime_hours,
            "grace_until": entitlement.grace_until.isoformat() if entitlement.grace_until else None,
            "suspend_at": entitlement.suspend_at.isoformat() if entitlement.suspend_at else None,
            "feature_flags": dict(entitlement.feature_flags),
            "policy_source": entitlement.policy_source,
            "policy_metadata": dict(entitlement.policy_metadata),
        }

    @staticmethod
    def _serialize_webhook_event(event) -> dict[str, object]:
        return {
            "id": event.id,
            "provider_name": event.provider_name,
            "provider_event_id": event.provider_event_id,
            "tenant_id": event.tenant_id,
            "event_type": event.event_type,
            "processing_status": event.processing_status,
            "received_at": event.received_at.isoformat(),
            "processed_at": event.processed_at.isoformat() if event.processed_at else None,
            "error_message": event.error_message,
        }

    @staticmethod
    def _serialize_billing_override(override) -> dict[str, object]:
        return {
            "id": override.id,
            "tenant_id": override.tenant_id,
            "grants_lifecycle_status": override.grants_lifecycle_status,
            "branch_limit_override": override.branch_limit_override,
            "device_limit_override": override.device_limit_override,
            "offline_runtime_hours_override": override.offline_runtime_hours_override,
            "feature_flags_override": dict(override.feature_flags_override),
            "reason": override.reason,
            "expires_at": override.expires_at.isoformat(),
            "status": override.status,
        }
