import asyncio
from datetime import timedelta

from conftest import sqlite_test_database_url
from store_control_plane.config.settings import build_settings
from store_control_plane.db.session import bootstrap_database, create_session_factory
from store_control_plane.repositories.commerce import CommerceRepository
from store_control_plane.repositories.tenants import TenantRepository
from store_control_plane.services.commerce import CommerceService
from store_control_plane.utils import utc_now


async def _exercise_commerce_persistence() -> None:
    database_url = sqlite_test_database_url("commerce-lifecycle")
    engine, session_factory = create_session_factory(database_url)
    try:
        await bootstrap_database(session_factory, engine=engine)
        issued_at = utc_now()

        async with session_factory() as session:
            tenant_repo = TenantRepository(session)
            commerce_repo = CommerceRepository(session)
            tenant = await tenant_repo.create_tenant(name="Acme Retail", slug="acme-retail")
            plan = await commerce_repo.create_billing_plan(
                code="launch-starter",
                display_name="Launch Starter",
                billing_cadence="monthly",
                currency_code="INR",
                amount_minor=149900,
                trial_days=14,
                branch_limit=2,
                device_limit=4,
                offline_runtime_hours=48,
                grace_window_days=5,
                feature_flags={"offline_continuity": True},
                provider_plan_refs={
                    "cashfree": "cf_plan_launch_starter",
                    "razorpay": "rp_plan_launch_starter",
                },
                is_default=True,
            )
            subscription = await commerce_repo.create_tenant_subscription(
                tenant_id=tenant.id,
                billing_plan_id=plan.id,
                provider_name=None,
                lifecycle_status="TRIALING",
                trial_started_at=issued_at,
                trial_ends_at=issued_at + timedelta(days=14),
            )
            entitlement = await commerce_repo.upsert_tenant_entitlement(
                tenant_id=tenant.id,
                billing_plan_id=plan.id,
                active_plan_code=plan.code,
                lifecycle_status="TRIALING",
                branch_limit=plan.branch_limit,
                device_limit=plan.device_limit,
                offline_runtime_hours=plan.offline_runtime_hours,
                grace_until=None,
                suspend_at=issued_at + timedelta(days=19),
                feature_flags=plan.feature_flags,
                policy_source="subscription",
                policy_metadata={"reason": "trial_issued"},
            )
            event_first = await commerce_repo.record_webhook_event(
                provider_name="cashfree",
                provider_event_id="cashfree_evt_1",
                tenant_id=tenant.id,
                event_type="subscription.activated",
                payload={"subscription_id": "cf_sub_1"},
            )
            event_second = await commerce_repo.record_webhook_event(
                provider_name="cashfree",
                provider_event_id="cashfree_evt_1",
                tenant_id=tenant.id,
                event_type="subscription.activated",
                payload={"subscription_id": "cf_sub_1"},
            )
            await session.commit()

        async with session_factory() as session:
            commerce_repo = CommerceRepository(session)
            default_plan = await commerce_repo.get_default_billing_plan()
            active_subscription = await commerce_repo.get_current_subscription(tenant_id=tenant.id)
            current_entitlement = await commerce_repo.get_tenant_entitlement(tenant_id=tenant.id)
            webhook_events = await commerce_repo.list_webhook_events(provider_name="cashfree")

            assert default_plan is not None
            assert default_plan.id == plan.id
            assert active_subscription is not None
            assert active_subscription.id == subscription.id
            assert current_entitlement is not None
            assert current_entitlement.id == entitlement.id
            assert current_entitlement.lifecycle_status == "TRIALING"
            assert current_entitlement.policy_source == "subscription"
            assert current_entitlement.feature_flags["offline_continuity"] is True
            assert event_first.id == event_second.id
            assert len(webhook_events) == 1
    finally:
        await engine.dispose()


def test_commerce_repository_persists_plan_subscription_entitlement_and_dedupes_webhooks() -> None:
    asyncio.run(_exercise_commerce_persistence())


async def _exercise_billing_override_persistence() -> None:
    database_url = sqlite_test_database_url("commerce-override")
    engine, session_factory = create_session_factory(database_url)
    try:
        await bootstrap_database(session_factory, engine=engine)
        issued_at = utc_now()

        async with session_factory() as session:
            tenant_repo = TenantRepository(session)
            commerce_repo = CommerceRepository(session)
            tenant = await tenant_repo.create_tenant(name="Northwind Retail", slug="northwind-retail")
            override = await commerce_repo.create_billing_override(
                tenant_id=tenant.id,
                created_by_user_id=None,
                grants_lifecycle_status="ACTIVE",
                branch_limit_override=5,
                device_limit_override=9,
                offline_runtime_hours_override=72,
                feature_flags_override={"manual_recovery": True},
                reason="Sales-assisted recovery",
                expires_at=issued_at + timedelta(days=2),
            )
            await session.commit()

        async with session_factory() as session:
            commerce_repo = CommerceRepository(session)
            active_override = await commerce_repo.get_active_billing_override(tenant_id=tenant.id, now=issued_at)
            expired_override = await commerce_repo.get_active_billing_override(
                tenant_id=tenant.id,
                now=issued_at + timedelta(days=3),
            )
            assert active_override is not None
            assert active_override.id == override.id
            assert active_override.feature_flags_override["manual_recovery"] is True
            assert expired_override is None
    finally:
        await engine.dispose()


def test_commerce_repository_tracks_expiring_billing_overrides() -> None:
    asyncio.run(_exercise_billing_override_persistence())


async def _exercise_trial_bootstrap_and_lifecycle_transitions() -> None:
    database_url = sqlite_test_database_url("commerce-service")
    engine, session_factory = create_session_factory(database_url)
    try:
        await bootstrap_database(session_factory, engine=engine)

        async with session_factory() as session:
            settings = build_settings(database_url=database_url)
            tenant_repo = TenantRepository(session)
            commerce_service = CommerceService(session, settings)
            tenant = await tenant_repo.create_tenant(name="Orbit Retail", slug="orbit-retail")
            trial_state = await commerce_service.issue_trial_subscription(tenant_id=tenant.id)
            assert trial_state["subscription"]["lifecycle_status"] == "TRIALING"
            assert trial_state["entitlement"]["lifecycle_status"] == "TRIALING"

            bootstrap = await commerce_service.bootstrap_subscription_checkout(
                tenant_id=tenant.id,
                provider_name="cashfree",
            )
            assert bootstrap["provider_name"] == "cashfree"
            await commerce_service.handle_provider_webhook(
                provider_name="cashfree",
                payload={
                    "event_id": "cashfree_evt_activate",
                    "event_type": "subscription.activated",
                    "tenant_id": tenant.id,
                    "provider_customer_id": bootstrap["provider_customer_id"],
                    "provider_subscription_id": bootstrap["provider_subscription_id"],
                    "current_period_started_at": utc_now().isoformat(),
                    "current_period_ends_at": (utc_now() + timedelta(days=30)).isoformat(),
                },
            )
            await commerce_service.handle_provider_webhook(
                provider_name="cashfree",
                payload={
                    "event_id": "cashfree_evt_failed",
                    "event_type": "subscription.renewal_failed",
                    "tenant_id": tenant.id,
                },
            )
            await commerce_service.handle_provider_webhook(
                provider_name="cashfree",
                payload={
                    "event_id": "cashfree_evt_recovered",
                    "event_type": "subscription.payment_captured",
                    "tenant_id": tenant.id,
                    "current_period_started_at": utc_now().isoformat(),
                    "current_period_ends_at": (utc_now() + timedelta(days=30)).isoformat(),
                },
            )
            await session.commit()

        async with session_factory() as session:
            commerce_repo = CommerceRepository(session)
            subscription = await commerce_repo.get_current_subscription(tenant_id=tenant.id)
            entitlement = await commerce_repo.get_tenant_entitlement(tenant_id=tenant.id)
            assert subscription is not None
            assert subscription.lifecycle_status == "ACTIVE"
            assert subscription.provider_name == "cashfree"
            assert subscription.provider_subscription_id == bootstrap["provider_subscription_id"]
            assert entitlement is not None
            assert entitlement.lifecycle_status == "ACTIVE"
            assert entitlement.active_plan_code == "launch-starter"
    finally:
        await engine.dispose()


def test_commerce_service_issues_trial_bootstraps_subscription_and_recovers_from_grace() -> None:
    asyncio.run(_exercise_trial_bootstrap_and_lifecycle_transitions())
