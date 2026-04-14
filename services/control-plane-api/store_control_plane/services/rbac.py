from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import RoleCapability, RoleDefinition
from ..utils import new_id


ROLE_CAPABILITY_MAP: dict[str, tuple[str, ...]] = {
    "platform_super_admin": (
        "platform.manage",
        "tenant.manage",
        "branch.manage",
        "staff.manage",
        "audit.view",
        "reports.view",
    ),
    "tenant_owner": (
        "tenant.manage",
        "branch.manage",
        "catalog.manage",
        "pricing.manage",
        "barcode.manage",
        "purchase.manage",
        "inventory.adjust",
        "inventory.transfer",
        "sales.bill",
        "sales.return",
        "refund.approve",
        "compliance.export",
        "staff.manage",
        "settings.manage",
        "audit.view",
        "reports.view",
    ),
    "finance_admin": ("refund.approve", "compliance.export", "reports.view", "audit.view"),
    "catalog_admin": ("catalog.manage", "pricing.manage", "barcode.manage", "reports.view"),
    "inventory_admin": ("purchase.manage", "inventory.adjust", "inventory.transfer", "reports.view"),
    "store_manager": ("branch.manage", "staff.manage", "reports.view"),
    "cashier": ("sales.bill", "sales.return"),
    "stock_clerk": ("inventory.adjust", "inventory.transfer"),
    "sales_associate": ("sales.bill",),
    "auditor": ("audit.view", "reports.view"),
}

ROLE_SCOPE_MAP: dict[str, str] = {
    "platform_super_admin": "platform",
    "tenant_owner": "tenant",
    "finance_admin": "tenant",
    "catalog_admin": "tenant",
    "inventory_admin": "tenant",
    "store_manager": "branch",
    "cashier": "branch",
    "stock_clerk": "branch",
    "sales_associate": "branch",
    "auditor": "branch",
}


def capabilities_for_role(role_name: str) -> tuple[str, ...]:
    return ROLE_CAPABILITY_MAP.get(role_name, ())


async def seed_role_definitions(session: AsyncSession) -> None:
    existing_roles = list((await session.scalars(select(RoleDefinition))).all())
    if existing_roles:
        return
    for role_name, scope in ROLE_SCOPE_MAP.items():
        role_definition = RoleDefinition(id=new_id(), scope=scope, role_name=role_name)
        session.add(role_definition)
        await session.flush()
        for capability in ROLE_CAPABILITY_MAP[role_name]:
            session.add(
                RoleCapability(
                    id=new_id(),
                    role_definition_id=role_definition.id,
                    capability=capability,
                )
            )
    await session.flush()
