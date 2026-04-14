from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import build_settings
from .db.session import bootstrap_database, create_session_factory
from .routes import auth_router, batches_router, barcode_router, billing_router, catalog_router, compliance_router, customers_router, exchange_router, inventory_router, operations_router, platform_router, procurement_finance_router, purchasing_router, runtime_router, supplier_reporting_router, sync_runtime_router, system_router, tenant_router, workforce_router
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
    korsenex_idp_mode: str | None = None,
    korsenex_idp_jwks_url: str | None = None,
    korsenex_idp_issuer: str | None = None,
    korsenex_idp_audience: str | None = None,
    legacy_write_mode: str | None = None,
    platform_admin_emails: list[str] | None = None,
) -> FastAPI:
    settings = build_settings(
        database_url=database_url,
        korsenex_idp_mode=korsenex_idp_mode,
        korsenex_idp_jwks_url=korsenex_idp_jwks_url,
        korsenex_idp_issuer=korsenex_idp_issuer,
        korsenex_idp_audience=korsenex_idp_audience,
        legacy_write_mode=legacy_write_mode,
        platform_admin_emails=platform_admin_emails,
    )
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
    _bootstrap_sync(database_url=settings.database_url, should_bootstrap=bootstrap_database)
    app.include_router(auth_router)
    app.include_router(system_router)
    app.include_router(platform_router)
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
    app.include_router(runtime_router)
    app.include_router(sync_runtime_router)
    return app
