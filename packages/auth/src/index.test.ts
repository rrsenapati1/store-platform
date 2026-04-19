import { describe, expect, test } from 'vitest';
import {
  buildCapabilitySet,
  canPerform,
  consumeLocalDevBootstrapFromWindow,
  mergeRoleAssignments,
  readKorsenexCallback,
  readLocalDevBootstrap,
  rolePermissions,
  buildKorsenexSignInUrl,
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

  test('reads local bootstrap token from hash parameters and defaults auto-start on', () => {
    expect(
      readLocalDevBootstrap({
        hash: '#stub_sub=owner-1&stub_email=owner@acme.local&stub_name=Acme%20Owner',
      }),
    ).toEqual({
      autoClockIn: false,
      autoOpenCashier: false,
      autoStart: true,
      korsenexToken: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner',
    });
  });

  test('query-string token can explicitly disable auto-start and request runtime follow-up actions', () => {
    expect(
      readLocalDevBootstrap({
        search: '?korsenex_token=stub%3Asub%3Dcashier-1%3Bemail%3Dcashier%40acme.local%3Bname%3DCounter%20Cashier&auto_start=0&auto_clock_in=1&auto_open_cashier=1',
      }),
    ).toEqual({
      autoClockIn: true,
      autoOpenCashier: true,
      autoStart: false,
      korsenexToken: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier',
    });
  });

  test('consumes bootstrap parameters from the browser URL after reading them', () => {
    const targetWindow = {
      location: {
        pathname: '/owner',
        search: '?tab=branches',
        hash: '#stub_sub=owner-1&stub_email=owner@acme.local&stub_name=Acme%20Owner&auto_open_cashier=1',
      },
      history: {
        replaceState: (_state: unknown, _title: string, nextUrl?: string | URL | null) => {
          const url = new URL(`${nextUrl ?? '/owner'}`, 'https://store.local');
          targetWindow.location.pathname = url.pathname;
          targetWindow.location.search = url.search;
          targetWindow.location.hash = url.hash;
        },
      },
    } as const;

    expect(consumeLocalDevBootstrapFromWindow(targetWindow as never)).toEqual({
      autoClockIn: false,
      autoOpenCashier: true,
      autoStart: true,
      korsenexToken: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner',
    });
    expect(targetWindow.location.pathname).toBe('/owner');
    expect(targetWindow.location.search).toBe('?tab=branches');
    expect(targetWindow.location.hash).toBe('');
  });

  test('exports the shared web-session browser helpers', () => {
    expect(typeof readKorsenexCallback).toBe('function');
    expect(
      buildKorsenexSignInUrl({
        authorizeBaseUrl: 'https://identity.korsenex.local/authorize',
        returnTo: 'https://owner.store.local/callback',
        state: 'owner-flow',
      }),
    ).toContain('owner-flow');
  });
});
