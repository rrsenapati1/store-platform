import type { ControlPlaneDeviceRecord } from '@store/types';
import type { StoreRuntimeShellStatus } from '../runtime-shell/storeRuntimeShell';
import { storeControlPlaneClient } from './client';
import {
  clearStoreRuntimeHubIdentity,
  saveStoreRuntimeHubIdentity,
  STORE_RUNTIME_HUB_IDENTITY_SCHEMA_VERSION,
  type StoreRuntimeHubIdentityRecord,
} from './storeRuntimeHubIdentityStore';

type EnsureStoreRuntimeHubIdentityArgs = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  selectedRuntimeDeviceId: string;
  runtimeDevices: ControlPlaneDeviceRecord[];
  runtimeShellStatus: StoreRuntimeShellStatus | null;
  currentHubIdentity: StoreRuntimeHubIdentityRecord | null;
};

function isSameHubIdentityScope(
  hubIdentity: StoreRuntimeHubIdentityRecord | null,
  scope: {
    installation_id: string;
    tenant_id: string;
    branch_id: string;
    device_id: string;
  },
) {
  return hubIdentity !== null
    && hubIdentity.installation_id === scope.installation_id
    && hubIdentity.tenant_id === scope.tenant_id
    && hubIdentity.branch_id === scope.branch_id
    && hubIdentity.device_id === scope.device_id;
}

async function clearIfPresent(hubIdentity: StoreRuntimeHubIdentityRecord | null) {
  if (hubIdentity === null) {
    return null;
  }
  await clearStoreRuntimeHubIdentity();
  return null;
}

export async function ensureStoreRuntimeHubIdentity({
  accessToken,
  tenantId,
  branchId,
  selectedRuntimeDeviceId,
  runtimeDevices,
  runtimeShellStatus,
  currentHubIdentity,
}: EnsureStoreRuntimeHubIdentityArgs): Promise<StoreRuntimeHubIdentityRecord | null> {
  if (runtimeShellStatus?.runtime_kind !== 'packaged_desktop' || !runtimeShellStatus.installation_id) {
    return clearIfPresent(currentHubIdentity);
  }

  const selectedDevice = runtimeDevices.find((device) => device.id === selectedRuntimeDeviceId) ?? null;
  if (!selectedDevice?.is_branch_hub) {
    return clearIfPresent(currentHubIdentity);
  }

  const scope = {
    installation_id: runtimeShellStatus.installation_id,
    tenant_id: tenantId,
    branch_id: branchId,
    device_id: selectedDevice.id,
  };
  if (isSameHubIdentityScope(currentHubIdentity, scope)) {
    return currentHubIdentity;
  }

  const bootstrap = await storeControlPlaneClient.bootstrapRuntimeHubIdentity(
    accessToken,
    tenantId,
    branchId,
    runtimeShellStatus.installation_id,
  );
  const hubIdentity: StoreRuntimeHubIdentityRecord = {
    schema_version: STORE_RUNTIME_HUB_IDENTITY_SCHEMA_VERSION,
    installation_id: bootstrap.installation_id,
    tenant_id: tenantId,
    branch_id: branchId,
    device_id: bootstrap.device_id,
    device_code: bootstrap.device_code,
    sync_access_secret: bootstrap.sync_access_secret,
    issued_at: bootstrap.issued_at,
  };
  await saveStoreRuntimeHubIdentity(hubIdentity);
  return hubIdentity;
}
