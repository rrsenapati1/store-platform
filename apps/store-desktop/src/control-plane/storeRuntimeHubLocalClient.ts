import type { ControlPlaneSpokeRuntimeActivation } from '@store/types';

export interface StoreRuntimeHubManifest {
  installation_id: string;
  tenant_id: string;
  branch_id: string;
  hub_device_id: string;
  hub_device_code: string;
  auth_mode: string;
  issued_at: string;
  supported_runtime_profiles: string[];
  pairing_modes: string[];
  register_url: string;
  relay_base_url: string;
  manifest_version: number;
}

export const STORE_RUNTIME_HUB_ALLOWED_RELAY_OPERATIONS = [
  'runtime.status',
  'runtime.print_jobs.submit',
  'runtime.print_jobs.list',
  'runtime.sync_status',
] as const;

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Local hub request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function loadStoreRuntimeHubManifest(manifestUrl: string) {
  return request<StoreRuntimeHubManifest>(manifestUrl);
}

export function issueStoreRuntimeSpokeActivation(
  hubServiceUrl: string,
  payload: {
    runtimeProfile: string;
    pairingMode?: 'approval_code' | 'qr';
  },
) {
  return request<ControlPlaneSpokeRuntimeActivation>(`${hubServiceUrl}/v1/spokes/activate`, {
    method: 'POST',
    body: JSON.stringify({
      runtime_profile: payload.runtimeProfile,
      pairing_mode: payload.pairingMode ?? 'qr',
    }),
  });
}
