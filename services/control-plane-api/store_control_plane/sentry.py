from __future__ import annotations

import logging
from typing import Any

from .config import Settings
from .logging import scrub_sensitive_mapping


logger = logging.getLogger("store_control_plane.sentry")


def _load_sentry_sdk():
    try:
        import sentry_sdk  # type: ignore[import-not-found]
    except ImportError:
        return None
    return sentry_sdk


def _build_integrations() -> list[object]:
    integrations: list[object] = []
    try:
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore[import-not-found]

        integrations.append(FastApiIntegration())
    except ImportError:
        pass
    try:
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  # type: ignore[import-not-found]

        integrations.append(SqlalchemyIntegration())
    except ImportError:
        pass
    return integrations


def scrub_sentry_event(event: dict[str, Any], hint: Any) -> dict[str, Any]:
    return scrub_sensitive_mapping(event)


def initialize_sentry(settings: Settings, *, sentry_sdk=None) -> bool:
    if not settings.sentry_dsn:
        return False
    sdk = sentry_sdk or _load_sentry_sdk()
    if sdk is None:
        logger.warning("sentry.sdk_missing", extra={"extra_payload": {"environment": settings.deployment_environment}})
        return False

    init_kwargs: dict[str, Any] = {
        "dsn": settings.sentry_dsn,
        "environment": settings.sentry_environment,
        "release": settings.release_version,
        "traces_sample_rate": settings.sentry_traces_sample_rate,
        "before_send": scrub_sentry_event,
        "send_default_pii": False,
    }
    integrations = _build_integrations()
    if integrations:
        init_kwargs["integrations"] = integrations
    sdk.init(**init_kwargs)
    return True


def bind_request_scope(
    *,
    request_id: str,
    route: str,
    method: str,
    environment: str,
    release_version: str,
    sentry_sdk=None,
) -> None:
    sdk = sentry_sdk or _load_sentry_sdk()
    if sdk is None:
        return
    sdk.set_tag("request_id", request_id)
    sdk.set_tag("route", route)
    sdk.set_tag("method", method)
    sdk.set_tag("environment", environment)
    sdk.set_tag("release_version", release_version)


def bind_actor_scope(actor, *, sentry_sdk=None) -> None:
    sdk = sentry_sdk or _load_sentry_sdk()
    if sdk is None:
        return
    sdk.set_user({"id": actor.user_id, "email": actor.email, "username": actor.full_name})
    sdk.set_tag("actor_user_id", actor.user_id)
    sdk.set_tag("actor_email", actor.email)
    sdk.set_tag("is_platform_admin", "true" if actor.is_platform_admin else "false")

    tenant_ids = sorted({membership.tenant_id for membership in actor.tenant_memberships})
    branch_ids = sorted({membership.branch_id for membership in actor.branch_memberships if membership.branch_id})
    if tenant_ids:
        sdk.set_tag("tenant_ids", ",".join(tenant_ids))
    if branch_ids:
        sdk.set_tag("branch_ids", ",".join(branch_ids))


def bind_sync_device_scope(device, *, sentry_sdk=None) -> None:
    sdk = sentry_sdk or _load_sentry_sdk()
    if sdk is None:
        return
    sdk.set_tag("device_id", device.device_id)
    sdk.set_tag("tenant_id", device.tenant_id)
    sdk.set_tag("branch_id", device.branch_id)
