import { describe, expect, test } from 'vitest';
import {
  buildCapabilitySet,
  canPerform,
  mergeRoleAssignments,
  rolePermissions,
} from './index';

describe('RBAC capability mapping', () => {
  test('tenant owner inherits broad tenant controls', () => {
    const capabilities = buildCapabilitySet(['tenant_owner']);

    expect(capabilities.has('catalog.manage')).toBe(true);
    expect(capabilities.has('settings.manage')).toBe(true);
    expect(capabilities.has('refund.approve')).toBe(true);
  });

  test('cashier is limited to billing and returns', () => {
    const capabilities = buildCapabilitySet(['cashier']);

    expect(capabilities.has('sales.bill')).toBe(true);
    expect(capabilities.has('sales.return')).toBe(true);
    expect(capabilities.has('inventory.transfer')).toBe(false);
    expect(capabilities.has('staff.manage')).toBe(false);
  });

  test('platform super admin bypasses scoped permission checks', () => {
    expect(
      canPerform({
        actorRoles: ['platform_super_admin'],
        requiredCapability: 'inventory.transfer',
      }),
    ).toBe(true);
  });

  test('merged assignments flatten permissions without duplication', () => {
    expect(mergeRoleAssignments(['catalog_admin', 'catalog_admin', 'inventory_admin'])).toEqual([
      'catalog_admin',
      'inventory_admin',
    ]);
    expect(rolePermissions.store_manager).toContain('sales.return');
  });
});
