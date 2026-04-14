import type {
  BrowserRuntimeShellWindow,
  StoreRuntimeShellAdapter,
  StoreRuntimeShellStatus,
} from './storeRuntimeShellContract';

export function resolveBrowserRuntimeWindow(): BrowserRuntimeShellWindow | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return window;
}

function normalizeHostname(value: string | null | undefined): string | null {
  const normalized = `${value ?? ''}`.trim();
  return normalized ? normalized : null;
}

function normalizeOrigin(value: string | null | undefined): string | null {
  const normalized = `${value ?? ''}`.trim().replace(/\/+$/, '');
  return normalized ? normalized : null;
}

export function createBrowserStoreRuntimeShell(
  resolveWindow: () => BrowserRuntimeShellWindow | null | undefined = resolveBrowserRuntimeWindow,
): StoreRuntimeShellAdapter {
  return {
    async getStatus(): Promise<StoreRuntimeShellStatus> {
      const hostname = normalizeHostname(resolveWindow()?.location?.hostname);
      const controlPlaneBaseUrl = normalizeOrigin(resolveWindow()?.location?.origin);
      return {
        runtime_kind: 'browser_web',
        runtime_label: 'Browser web runtime',
        bridge_state: 'browser_fallback',
        app_version: null,
        hostname,
        operating_system: null,
        architecture: null,
        installation_id: null,
        claim_code: null,
        runtime_home: null,
        cache_db_path: null,
        control_plane_base_url: controlPlaneBaseUrl,
        release_environment: null,
        release_profile_source: null,
        updater_endpoint: null,
        updater_pubkey_configured: null,
        hub_service_state: null,
        hub_service_url: null,
        hub_manifest_url: null,
      };
    },
  };
}
