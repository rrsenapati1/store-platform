from __future__ import annotations

from ..config import Settings
from ..schemas.system import AuthorityBoundaryResponse


MIGRATED_DOMAINS = [
    "onboarding",
    "workforce",
    "catalog",
    "barcode_foundation",
    "purchasing",
    "inventory",
    "batch_tracking",
    "billing",
    "compliance_exports",
    "customer_reporting",
    "supplier_reporting",
    "runtime_print",
    "sync_runtime",
]

LEGACY_REMAINING_DOMAINS = [
]

SHUTDOWN_CRITERIA = [
    "Control-plane verification script passes on Postgres",
    "Migrated writes are blocked on the legacy retail API",
    "Legacy-only domain list is empty",
]

SHUTDOWN_STEPS = [
    "Enable cutover mode on the legacy retail API",
    "Verify migrated write attempts fail with authority headers",
    "Keep legacy reads only for the unmigrated domains until their replacements land",
]


def build_authority_boundary(settings: Settings) -> AuthorityBoundaryResponse:
    return AuthorityBoundaryResponse(
        control_plane_service="services/control-plane-api",
        legacy_service="services/api/store_api",
        cutover_phase="control_plane_primary",
        legacy_write_mode=settings.legacy_write_mode,
        migrated_domains=MIGRATED_DOMAINS,
        legacy_remaining_domains=LEGACY_REMAINING_DOMAINS,
        shutdown_criteria=SHUTDOWN_CRITERIA,
        shutdown_steps=SHUTDOWN_STEPS,
    )
