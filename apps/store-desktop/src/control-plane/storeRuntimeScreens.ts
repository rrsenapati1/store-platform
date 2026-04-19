import { buildCapabilitySet } from '@store/auth';
import { actorRoles, type ActorRole, type Capability, type ControlPlaneActor } from '@store/types';

export type StoreRuntimeScreenId = 'entry' | 'sell' | 'returns' | 'operations' | 'manager';

export type StoreRuntimeScreenDefinition = {
  id: StoreRuntimeScreenId;
  label: string;
  description: string;
};

const roleSet = new Set<string>(actorRoles);

const screenDefinitions: Record<StoreRuntimeScreenId, StoreRuntimeScreenDefinition> = {
  entry: {
    id: 'entry',
    label: 'Entry',
    description: 'Sign in, clock in, and open the register.',
  },
  sell: {
    id: 'sell',
    label: 'Sell',
    description: 'Run the live counter sale.',
  },
  returns: {
    id: 'returns',
    label: 'Returns',
    description: 'Process returns and exchanges.',
  },
  operations: {
    id: 'operations',
    label: 'Operations',
    description: 'Receiving, counts, expiry, and runtime operations.',
  },
  manager: {
    id: 'manager',
    label: 'Manager',
    description: 'Branch trade posture and runtime oversight.',
  },
};

export function getStoreRuntimeScreenDefinition(screenId: StoreRuntimeScreenId): StoreRuntimeScreenDefinition {
  return screenDefinitions[screenId];
}

export function getStoreRuntimeScreenDefinitions(screenIds: StoreRuntimeScreenId[]): StoreRuntimeScreenDefinition[] {
  return screenIds.map((screenId) => getStoreRuntimeScreenDefinition(screenId));
}

function normalizeActorRoles(actor: ControlPlaneActor | null): ActorRole[] {
  if (!actor) {
    return [];
  }
  const roles = new Set<ActorRole>();
  if (actor.is_platform_admin) {
    roles.add('platform_super_admin');
  }
  for (const membership of actor.tenant_memberships) {
    if (roleSet.has(membership.role_name)) {
      roles.add(membership.role_name as ActorRole);
    }
  }
  for (const membership of actor.branch_memberships) {
    if (roleSet.has(membership.role_name)) {
      roles.add(membership.role_name as ActorRole);
    }
  }
  return [...roles];
}

function hasCapability(actor: ControlPlaneActor | null, capability: Capability): boolean {
  const roles = normalizeActorRoles(actor);
  if (roles.includes('platform_super_admin')) {
    return true;
  }
  return buildCapabilitySet(roles).has(capability);
}

function hasAnyRole(actor: ControlPlaneActor | null, roles: ActorRole[]): boolean {
  const actorRoles = normalizeActorRoles(actor);
  return roles.some((role) => actorRoles.includes(role));
}

export function resolveVisibleRuntimeScreens(args: {
  actor: ControlPlaneActor | null;
  runtimeReady: boolean;
}): StoreRuntimeScreenId[] {
  const screens: StoreRuntimeScreenId[] = ['entry'];
  if (!args.runtimeReady) {
    return screens;
  }
  if (hasCapability(args.actor, 'sales.bill')) {
    screens.push('sell');
  }
  if (hasCapability(args.actor, 'sales.return')) {
    screens.push('returns');
  }
  if (
    hasCapability(args.actor, 'sales.bill')
    || hasCapability(args.actor, 'sales.return')
  ) {
    screens.push('operations');
  }
  if (
    hasCapability(args.actor, 'inventory.adjust')
    || hasCapability(args.actor, 'inventory.transfer')
    || hasCapability(args.actor, 'purchase.manage')
    || hasCapability(args.actor, 'barcode.manage')
  ) {
    screens.push('operations');
  }
  if (
    hasAnyRole(args.actor, ['platform_super_admin', 'tenant_owner', 'store_manager'])
    || hasCapability(args.actor, 'staff.manage')
    || hasCapability(args.actor, 'settings.manage')
  ) {
    screens.push('manager');
  }
  return [...new Set(screens)];
}

export function resolveDefaultRuntimeScreen(args: {
  actor: ControlPlaneActor | null;
  runtimeReady: boolean;
}): StoreRuntimeScreenId {
  const visible = resolveVisibleRuntimeScreens(args);
  if (!args.runtimeReady) {
    return 'entry';
  }
  if (visible.includes('sell')) {
    return 'sell';
  }
  if (visible.includes('returns')) {
    return 'returns';
  }
  if (visible.includes('operations')) {
    return 'operations';
  }
  if (visible.includes('manager')) {
    return 'manager';
  }
  return 'entry';
}

export function clampRuntimeScreen(
  desiredScreen: StoreRuntimeScreenId,
  args: { actor: ControlPlaneActor | null; runtimeReady: boolean },
): StoreRuntimeScreenId {
  const visible = resolveVisibleRuntimeScreens(args);
  if (visible.includes(desiredScreen)) {
    return desiredScreen;
  }
  return resolveDefaultRuntimeScreen(args);
}
