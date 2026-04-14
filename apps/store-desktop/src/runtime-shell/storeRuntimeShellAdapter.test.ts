import { describe, expect, test, vi } from 'vitest';
import { createResolvedStoreRuntimeShell } from './storeRuntimeShell';

describe('resolved store runtime shell adapter', () => {
  test('uses native shell bridge when packaged runtime is available', async () => {
    const invoke = vi.fn(async (command: string) => {
      if (command === 'cmd_get_store_runtime_shell_status') {
        return {
          runtime_kind: 'packaged_desktop',
          runtime_label: 'Store Desktop packaged runtime',
          bridge_state: 'ready',
          app_version: '0.1.0',
          hostname: 'COUNTER-01',
          operating_system: 'windows',
          architecture: 'x86_64',
          installation_id: 'install-123',
          claim_code: 'STORE-NSTALL23',
          runtime_home: 'C:/StoreRuntime',
          cache_db_path: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
          control_plane_base_url: 'https://control.acme.local',
          release_environment: 'staging',
          release_profile_source: 'bundled',
          updater_endpoint: 'https://updates.acme.local/latest.json',
          updater_pubkey_configured: true,
          hub_service_state: 'ready',
          hub_service_url: 'http://127.0.0.1:45123',
          hub_manifest_url: 'http://127.0.0.1:45123/v1/spoke-manifest',
        };
      }
      throw new Error(`Unexpected command: ${command}`);
    });

    const adapter = createResolvedStoreRuntimeShell({
      invoke,
      isNativeRuntime: () => true,
    });

    await expect(adapter.getStatus()).resolves.toEqual({
      runtime_kind: 'packaged_desktop',
      runtime_label: 'Store Desktop packaged runtime',
      bridge_state: 'ready',
      app_version: '0.1.0',
      hostname: 'COUNTER-01',
      operating_system: 'windows',
      architecture: 'x86_64',
      installation_id: 'install-123',
      claim_code: 'STORE-NSTALL23',
      runtime_home: 'C:/StoreRuntime',
      cache_db_path: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
      control_plane_base_url: 'https://control.acme.local',
      release_environment: 'staging',
      release_profile_source: 'bundled',
      updater_endpoint: 'https://updates.acme.local/latest.json',
      updater_pubkey_configured: true,
      hub_service_state: 'ready',
      hub_service_url: 'http://127.0.0.1:45123',
      hub_manifest_url: 'http://127.0.0.1:45123/v1/spoke-manifest',
    });
    expect(invoke).toHaveBeenCalledWith('cmd_get_store_runtime_shell_status');
  });

  test('falls back to browser shell status in the web shell', async () => {
    const adapter = createResolvedStoreRuntimeShell({
      browserWindow: () =>
        ({
          location: { hostname: 'localhost', origin: 'http://localhost:1420' },
        }) as Window,
      isNativeRuntime: () => false,
    });

    await expect(adapter.getStatus()).resolves.toEqual({
      runtime_kind: 'browser_web',
      runtime_label: 'Browser web runtime',
      bridge_state: 'browser_fallback',
      app_version: null,
      hostname: 'localhost',
      operating_system: null,
      architecture: null,
      installation_id: null,
      claim_code: null,
      runtime_home: null,
      cache_db_path: null,
      control_plane_base_url: 'http://localhost:1420',
      release_environment: null,
      release_profile_source: null,
      updater_endpoint: null,
      updater_pubkey_configured: null,
      hub_service_state: null,
      hub_service_url: null,
      hub_manifest_url: null,
    });
  });
});
