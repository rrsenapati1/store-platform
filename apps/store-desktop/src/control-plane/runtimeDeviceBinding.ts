import type { ControlPlaneDeviceRecord, ControlPlaneRuntimeDeviceClaimResolution } from '@store/types';
import type { StoreRuntimeShellStatus } from '../runtime-shell/storeRuntimeShell';
import { storeControlPlaneClient } from './client';

export type StoreRuntimeDeviceBinding = {
  selectedRuntimeDeviceId: string;
  runtimeDeviceClaim: ControlPlaneRuntimeDeviceClaimResolution | null;
};

type ResolveStoreRuntimeDeviceBindingArgs = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  runtimeDevices: ControlPlaneDeviceRecord[];
  runtimeShellStatus: StoreRuntimeShellStatus | null;
};

export async function resolveStoreRuntimeDeviceBinding({
  accessToken,
  tenantId,
  branchId,
  runtimeDevices,
  runtimeShellStatus,
}: ResolveStoreRuntimeDeviceBindingArgs): Promise<StoreRuntimeDeviceBinding> {
  if (runtimeShellStatus?.runtime_kind !== 'packaged_desktop' || !runtimeShellStatus.installation_id) {
    return {
      selectedRuntimeDeviceId: runtimeDevices[0]?.id ?? '',
      runtimeDeviceClaim: null,
    };
  }

  const runtimeDeviceClaim = await storeControlPlaneClient.resolveRuntimeDeviceClaim(
    accessToken,
    tenantId,
    branchId,
    {
      installation_id: runtimeShellStatus.installation_id,
      runtime_kind: runtimeShellStatus.runtime_kind,
      hostname: runtimeShellStatus.hostname,
      operating_system: runtimeShellStatus.operating_system,
      architecture: runtimeShellStatus.architecture,
      app_version: runtimeShellStatus.app_version,
    },
  );

  return {
    selectedRuntimeDeviceId: runtimeDeviceClaim.bound_device_id ?? '',
    runtimeDeviceClaim,
  };
}
