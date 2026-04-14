from __future__ import annotations

from collections.abc import Iterable

ROLE_PERMISSIONS = {
    "tenant_owner": {
        "catalog.manage",
        "pricing.manage",
        "barcode.manage",
        "inventory.adjust",
        "inventory.transfer",
        "purchase.manage",
        "sales.bill",
        "sales.return",
        "refund.approve",
        "reports.view",
        "compliance.export",
        "staff.manage",
        "settings.manage",
    },
    "finance_admin": {"reports.view", "compliance.export", "refund.approve"},
    "catalog_admin": {"catalog.manage", "pricing.manage", "barcode.manage", "reports.view"},
    "inventory_admin": {"inventory.adjust", "inventory.transfer", "purchase.manage", "reports.view"},
    "store_manager": {
        "inventory.adjust",
        "inventory.transfer",
        "purchase.manage",
        "sales.bill",
        "sales.return",
        "refund.approve",
        "reports.view",
        "staff.manage",
    },
    "cashier": {"sales.bill", "sales.return", "reports.view"},
    "stock_clerk": {"inventory.adjust", "purchase.manage", "reports.view"},
    "sales_associate": {"sales.bill"},
    "auditor": {"reports.view", "compliance.export"},
}


def build_capability_set(roles: Iterable[str]) -> set[str]:
    capability_set: set[str] = set()
    for role in roles:
        if role == "platform_super_admin":
            continue
        capability_set.update(ROLE_PERMISSIONS.get(role, set()))
    return capability_set


def can_perform(roles: Iterable[str], capability: str) -> bool:
    role_list = list(roles)
    if "platform_super_admin" in role_list:
        return True
    return capability in build_capability_set(role_list)
