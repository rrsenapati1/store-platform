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

export type LocalDevBootstrap = {
  korsenexToken: string | null;
  autoStart: boolean;
  autoClockIn: boolean;
  autoOpenCashier: boolean;
};

const LOCAL_DEV_BOOTSTRAP_KEYS = [
  'korsenex_token',
  'stub_sub',
  'stub_email',
  'stub_name',
  'auto_start',
  'auto_clock_in',
  'auto_open_cashier',
] as const;

function normalizeHashParams(hash: string | null | undefined): URLSearchParams {
  const trimmed = `${hash ?? ''}`.trim();
  if (!trimmed.startsWith('#')) {
    return new URLSearchParams();
  }
  return new URLSearchParams(trimmed.slice(1));
}

function normalizeSearchParams(search: string | null | undefined): URLSearchParams {
  return new URLSearchParams(`${search ?? ''}`.trim());
}

function parseBooleanParam(value: string | null): boolean {
  if (value == null) {
    return false;
  }
  return ['1', 'true', 'yes', 'on'].includes(value.trim().toLowerCase());
}

function resolveBootstrapParam(hashParams: URLSearchParams, searchParams: URLSearchParams, key: string): string | null {
  return hashParams.get(key) ?? searchParams.get(key);
}

export function readLocalDevBootstrap(input?: {
  hash?: string | null;
  search?: string | null;
}): LocalDevBootstrap {
  const hashParams = normalizeHashParams(input?.hash);
  const searchParams = normalizeSearchParams(input?.search);
  const explicitToken = resolveBootstrapParam(hashParams, searchParams, 'korsenex_token')?.trim() ?? '';
  const stubSubject = resolveBootstrapParam(hashParams, searchParams, 'stub_sub')?.trim() ?? '';
  const stubEmail = resolveBootstrapParam(hashParams, searchParams, 'stub_email')?.trim() ?? '';
  const stubName = resolveBootstrapParam(hashParams, searchParams, 'stub_name')?.trim() ?? '';
  const stubToken = stubSubject
    ? `stub:sub=${stubSubject};email=${stubEmail};name=${stubName || stubSubject}`
    : '';
  const korsenexToken = explicitToken || stubToken || null;
  const explicitAutoStart = resolveBootstrapParam(hashParams, searchParams, 'auto_start');

  return {
    korsenexToken,
    autoStart: korsenexToken ? (explicitAutoStart == null ? true : parseBooleanParam(explicitAutoStart)) : false,
    autoClockIn: parseBooleanParam(resolveBootstrapParam(hashParams, searchParams, 'auto_clock_in')),
    autoOpenCashier: parseBooleanParam(resolveBootstrapParam(hashParams, searchParams, 'auto_open_cashier')),
  };
}

export function consumeLocalDevBootstrapFromWindow(targetWindow: Pick<Window, 'location' | 'history'>): LocalDevBootstrap {
  const bootstrap = readLocalDevBootstrap({
    hash: targetWindow.location.hash,
    search: targetWindow.location.search,
  });
  const hashParams = normalizeHashParams(targetWindow.location.hash);
  const searchParams = normalizeSearchParams(targetWindow.location.search);
  let mutated = false;

  for (const key of LOCAL_DEV_BOOTSTRAP_KEYS) {
    if (hashParams.has(key)) {
      hashParams.delete(key);
      mutated = true;
    }
    if (searchParams.has(key)) {
      searchParams.delete(key);
      mutated = true;
    }
  }

  if (mutated) {
    const nextSearch = searchParams.toString();
    const nextHash = hashParams.toString();
    const nextUrl = `${targetWindow.location.pathname}${nextSearch ? `?${nextSearch}` : ''}${nextHash ? `#${nextHash}` : ''}`;
    targetWindow.history.replaceState(null, '', nextUrl);
  }

  return bootstrap;
}
