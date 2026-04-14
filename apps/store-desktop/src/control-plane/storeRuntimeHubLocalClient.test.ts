import { describe, expect, test, vi } from 'vitest';
import {
  issueStoreRuntimeSpokeActivation,
  loadStoreRuntimeHubManifest,
} from './storeRuntimeHubLocalClient';

describe('store runtime hub local client', () => {
  test('loads the local spoke manifest', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        installation_id: 'store-runtime-abcd1234efgh5678',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        hub_device_id: 'device-hub-1',
        hub_device_code: 'BLR-HUB-01',
        auth_mode: 'spoke_runtime_token_pending',
        issued_at: '2026-04-14T08:00:00.000Z',
        supported_runtime_profiles: ['desktop_spoke'],
        pairing_modes: ['qr', 'approval_code'],
        register_url: 'http://127.0.0.1:45123/v1/spokes/register',
        relay_base_url: 'http://127.0.0.1:45123/v1/relay',
        manifest_version: 1,
      }),
    }));
    vi.stubGlobal('fetch', fetchMock);

    const manifest = await loadStoreRuntimeHubManifest('http://127.0.0.1:45123/v1/spoke-manifest');

    expect(manifest.hub_device_id).toBe('device-hub-1');
    expect(manifest.supported_runtime_profiles).toEqual(['desktop_spoke']);
    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:45123/v1/spoke-manifest', expect.anything());
  });

  test('issues a spoke activation through the local hub service', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        activation_code: 'ACTV-ABCD-1234',
        pairing_mode: 'qr',
        runtime_profile: 'desktop_spoke',
        hub_device_id: 'device-hub-1',
        expires_at: '2099-01-01T00:00:00Z',
      }),
    }));
    vi.stubGlobal('fetch', fetchMock);

    const activation = await issueStoreRuntimeSpokeActivation('http://127.0.0.1:45123', {
      runtimeProfile: 'desktop_spoke',
    });

    expect(activation.activation_code).toBe('ACTV-ABCD-1234');
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:45123/v1/spokes/activate',
      expect.objectContaining({
        method: 'POST',
      }),
    );
  });
});
