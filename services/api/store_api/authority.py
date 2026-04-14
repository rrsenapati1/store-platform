from __future__ import annotations

import os
import re

from fastapi.responses import JSONResponse

DEFAULT_LEGACY_WRITE_MODE = "shadow"
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

MIGRATED_DOMAIN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("onboarding", re.compile(r"^/v1/platform/tenants(?:/.*)?$")),
    ("workforce", re.compile(r"^/v1/tenants/[^/]+/(?:staff-profiles|memberships)(?:/.*)?$")),
    ("workforce", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/(?:devices|memberships)(?:/.*)?$")),
    ("catalog", re.compile(r"^/v1/tenants/[^/]+/products(?:/.*)?$")),
    ("catalog", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/catalog-items(?:/.*)?$")),
    ("barcode_foundation", re.compile(r"^/v1/tenants/[^/]+/barcode-allocations(?:/.*)?$")),
    ("barcode_foundation", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/barcode-labels(?:/.*)?$")),
    ("purchasing", re.compile(r"^/v1/tenants/[^/]+/suppliers(?:/.*)?$")),
    ("purchasing", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/purchase-orders(?:/.*)?$")),
    ("batch_tracking", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/goods-receipts/[^/]+/batch-lots(?:/.*)?$")),
    ("batch_tracking", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/batch-lots/[^/]+/expiry-write-offs(?:/.*)?$")),
    ("inventory", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/(?:goods-receipts|stock-adjustments|stock-counts|transfers)(?:/.*)?$")),
    ("billing", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/sales(?:/.*)?$")),
    ("billing", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/sale-returns(?:/.*)?$")),
    ("billing", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/exchanges(?:/.*)?$")),
    ("compliance_exports", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/compliance/gst-exports(?:/.*)?$")),
    ("customer_reporting", re.compile(r"^/v1/tenants/[^/]+/customers(?:/.*)?$")),
    ("customer_reporting", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/customer-report(?:/.*)?$")),
    ("supplier_reporting", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/vendor-disputes(?:/.*)?$")),
    ("runtime_print", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/print-jobs/(?:invoices|barcode-labels)$")),
    ("runtime_print", re.compile(r"^/v1/tenants/[^/]+/branches/[^/]+/devices/[^/]+/print-jobs/[^/]+/complete$")),
    ("sync_runtime", re.compile(r"^/v1/sync/(?:push|pull|heartbeat)$")),
)


def resolve_legacy_write_mode(override: str | None = None) -> str:
    value = (override or os.getenv("STORE_LEGACY_WRITE_MODE") or DEFAULT_LEGACY_WRITE_MODE).strip().lower()
    if value not in {"shadow", "cutover"}:
        return DEFAULT_LEGACY_WRITE_MODE
    return value


def classify_legacy_domain(path: str) -> str | None:
    for domain, pattern in MIGRATED_DOMAIN_PATTERNS:
        if pattern.match(path):
            return domain
    return None


def build_legacy_authority_headers(*, domain: str, status_value: str) -> dict[str, str]:
    return {
        "X-Store-Legacy-Authority-Status": status_value,
        "X-Store-Legacy-Domain": domain,
        "X-Store-Authority-Owner": "control-plane",
    }


def apply_legacy_authority_headers(response, *, domain: str, status_value: str) -> None:
    for key, value in build_legacy_authority_headers(domain=domain, status_value=status_value).items():
        response.headers[key] = value


def build_cutover_block_response(*, domain: str) -> JSONResponse:
    return JSONResponse(
        status_code=410,
        content={"detail": f"Legacy API write is disabled for migrated domain: {domain}"},
        headers=build_legacy_authority_headers(domain=domain, status_value="cutover"),
    )
