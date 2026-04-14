import { describe, expect, test } from 'vitest';
import { actorRoles, capabilities } from './index';

describe('shared retail types', () => {
  test('exposes the planned role hierarchy', () => {
    expect(actorRoles).toContain('platform_super_admin');
    expect(actorRoles).toContain('store_manager');
  });

  test('exposes the planned capability set', () => {
    expect(capabilities).toContain('sales.bill');
    expect(capabilities).toContain('compliance.export');
  });
});
