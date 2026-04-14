import type { ActorRole, Capability } from '@store/types';

type RolePermissionMap = Record<Exclude<ActorRole, 'platform_super_admin'>, Capability[]>;

export const rolePermissions: RolePermissionMap = {
  tenant_owner: [
    'catalog.manage',
    'pricing.manage',
    'barcode.manage',
    'inventory.adjust',
    'inventory.transfer',
    'purchase.manage',
    'sales.bill',
    'sales.return',
    'refund.approve',
    'reports.view',
    'compliance.export',
    'staff.manage',
    'settings.manage',
  ],
  finance_admin: ['reports.view', 'compliance.export', 'refund.approve'],
  catalog_admin: ['catalog.manage', 'pricing.manage', 'barcode.manage', 'reports.view'],
  inventory_admin: ['inventory.adjust', 'inventory.transfer', 'purchase.manage', 'reports.view'],
  store_manager: [
    'inventory.adjust',
    'inventory.transfer',
    'purchase.manage',
    'sales.bill',
    'sales.return',
    'refund.approve',
    'reports.view',
    'staff.manage',
  ],
  cashier: ['sales.bill', 'sales.return', 'reports.view'],
  stock_clerk: ['inventory.adjust', 'purchase.manage', 'reports.view'],
  sales_associate: ['sales.bill'],
  auditor: ['reports.view', 'compliance.export'],
};

export function mergeRoleAssignments(roles: ActorRole[]): ActorRole[] {
  return [...new Set(roles)];
}

export function buildCapabilitySet(roles: ActorRole[]): Set<Capability> {
  const capabilitySet = new Set<Capability>();
  for (const role of mergeRoleAssignments(roles)) {
    if (role === 'platform_super_admin') {
      continue;
    }
    for (const capability of rolePermissions[role] ?? []) {
      capabilitySet.add(capability);
    }
  }
  return capabilitySet;
}

export function canPerform(input: { actorRoles: ActorRole[]; requiredCapability: Capability }): boolean {
  if (input.actorRoles.includes('platform_super_admin')) {
    return true;
  }
  return buildCapabilitySet(input.actorRoles).has(input.requiredCapability);
}
