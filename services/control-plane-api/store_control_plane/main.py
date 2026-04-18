from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import build_settings
from .db.session import bootstrap_database, create_session_factory
from .logging import configure_logging
from .middleware import RateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from .routes import auth_router, batches_router, barcode_router, billing_router, catalog_router, commerce_router, compliance_router, customers_router, exchange_router, inventory_router, operations_router, platform_router, procurement_finance_router, promotions_router, purchasing_router, reporting_router, runtime_router, supplier_reporting_router, sync_runtime_router, system_router, tenant_router, workforce_router
from .sentry import initialize_sentry
from .services import build_identity_provider


def _bootstrap_sync(*, database_url: str, should_bootstrap: bool) -> None:
    if not should_bootstrap:
        return

    bootstrap_engine, bootstrap_session_factory = create_session_factory(database_url)
    try:
        asyncio.run(
            bootstrap_database(
                bootstrap_session_factory,
                engine=bootstrap_engine,
            )
        )
    finally:
        asyncio.run(bootstrap_engine.dispose())


def create_app(
    *,
    database_url: str | None = None,
    bootstrap_database: bool = False,
    deployment_environment: str | None = None,
    public_base_url: str | None = None,
    release_version: str | None = None,
    korsenex_idp_mode: str | None = None,
    korsenex_idp_jwks_url: str | None = None,
    korsenex_idp_issuer: str | None = None,
    korsenex_idp_audience: str | None = None,
    legacy_write_mode: str | None = None,
    platform_admin_emails: list[str] | None = None,
    compliance_secret_key: str | None = None,
    compliance_irp_mode: str | None = None,
    object_storage_endpoint_url: str | None = None,
    object_storage_region: str | None = None,
    object_storage_bucket: str | None = None,
    object_storage_prefix: str | None = None,
    object_storage_access_key_id: str | None = None,
    object_storage_secret_access_key: str | None = None,
    object_storage_session_token: str | None = None,
    object_storage_force_path_style: bool | None = None,
    sentry_dsn: str | None = None,
    sentry_traces_sample_rate: float | None = None,
    log_format: str | None = None,
    rate_limit_window_seconds: int | None = None,
    rate_limit_auth_requests: int | None = None,
    rate_limit_activation_requests: int | None = None,
    rate_limit_webhook_requests: int | None = None,
    secure_headers_enabled: bool | None = None,
    secure_headers_hsts_enabled: bool | None = None,
    secure_headers_csp: str | None = None,
) -> FastAPI:
    settings = build_settings(
        database_url=database_url,
        deployment_environment=deployment_environment,
        public_base_url=public_base_url,
        release_version=release_version,
        korsenex_idp_mode=korsenex_idp_mode,
        korsenex_idp_jwks_url=korsenex_idp_jwks_url,
        korsenex_idp_issuer=korsenex_idp_issuer,
        korsenex_idp_audience=korsenex_idp_audience,
        legacy_write_mode=legacy_write_mode,
        platform_admin_emails=platform_admin_emails,
        compliance_secret_key=compliance_secret_key,
        compliance_irp_mode=compliance_irp_mode,
        object_storage_endpoint_url=object_storage_endpoint_url,
        object_storage_region=object_storage_region,
        object_storage_bucket=object_storage_bucket,
        object_storage_prefix=object_storage_prefix,
        object_storage_access_key_id=object_storage_access_key_id,
        object_storage_secret_access_key=object_storage_secret_access_key,
        object_storage_session_token=object_storage_session_token,
        object_storage_force_path_style=object_storage_force_path_style,
        sentry_dsn=sentry_dsn,
        sentry_traces_sample_rate=sentry_traces_sample_rate,
        log_format=log_format,
        rate_limit_window_seconds=rate_limit_window_seconds,
        rate_limit_auth_requests=rate_limit_auth_requests,
        rate_limit_activation_requests=rate_limit_activation_requests,
        rate_limit_webhook_requests=rate_limit_webhook_requests,
        secure_headers_enabled=secure_headers_enabled,
        secure_headers_hsts_enabled=secure_headers_hsts_enabled,
        secure_headers_csp=secure_headers_csp,
    )
    configure_logging(settings)
    initialize_sentry(settings)
    engine, session_factory = create_session_factory(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            await app.state.engine.dispose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.identity_provider = build_identity_provider(settings)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    app.add_middleware(RequestContextMiddleware, settings=settings)
    _bootstrap_sync(database_url=settings.database_url, should_bootstrap=bootstrap_database)
    app.include_router(auth_router)
    app.include_router(system_router)
    app.include_router(platform_router)
    app.include_router(commerce_router)
    app.include_router(promotions_router)
    app.include_router(tenant_router)
    app.include_router(workforce_router)
    app.include_router(catalog_router)
    app.include_router(barcode_router)
    app.include_router(purchasing_router)
    app.include_router(inventory_router)
    app.include_router(operations_router)
    app.include_router(batches_router)
    app.include_router(procurement_finance_router)
    app.include_router(billing_router)
    app.include_router(compliance_router)
    app.include_router(customers_router)
    app.include_router(exchange_router)
    app.include_router(supplier_reporting_router)
    app.include_router(reporting_router)
    app.include_router(runtime_router)
    app.include_router(sync_runtime_router)
    return app
