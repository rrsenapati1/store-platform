export type StoreRuntimeShellKind = 'browser_web' | 'packaged_desktop';
export type StoreRuntimeShellBridgeState = 'browser_fallback' | 'ready' | 'unavailable';
export const DEFAULT_PACKAGED_CONTROL_PLANE_BASE_URL = 'http://127.0.0.1:8000';

export interface StoreRuntimeShellStatus {
  runtime_kind: StoreRuntimeShellKind;
  runtime_label: string;
  bridge_state: StoreRuntimeShellBridgeState;
  app_version: string | null;
  hostname: string | null;
  operating_system: string | null;
  architecture: string | null;
  installation_id: string | null;
  claim_code: string | null;
  runtime_home: string | null;
  cache_db_path: string | null;
  control_plane_base_url: string | null;
  release_environment: string | null;
  release_profile_source: string | null;
  updater_endpoint: string | null;
  updater_pubkey_configured: boolean | null;
  hub_service_state: string | null;
  hub_service_url: string | null;
  hub_manifest_url: string | null;
}

export interface BrowserRuntimeShellWindow {
  location?: {
    hostname?: string | null;
    origin?: string | null;
  } | null;
}

export interface StoreRuntimeShellAdapter {
  getStatus(): Promise<StoreRuntimeShellStatus>;
}

export type StoreRuntimeShellInvoke = (command: string, payload?: Record<string, unknown>) => Promise<unknown>;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export function isStoreRuntimeShellStatus(value: unknown): value is StoreRuntimeShellStatus {
  if (!isObject(value)) {
    return false;
  }

  return (value.runtime_kind === 'browser_web' || value.runtime_kind === 'packaged_desktop')
    && typeof value.runtime_label === 'string'
    && (value.bridge_state === 'browser_fallback' || value.bridge_state === 'ready' || value.bridge_state === 'unavailable')
    && (typeof value.app_version === 'string' || value.app_version === null)
    && (typeof value.hostname === 'string' || value.hostname === null)
    && (typeof value.operating_system === 'string' || value.operating_system === null)
    && (typeof value.architecture === 'string' || value.architecture === null)
    && (typeof value.installation_id === 'string' || value.installation_id === null)
    && (typeof value.claim_code === 'string' || value.claim_code === null)
    && (typeof value.runtime_home === 'string' || value.runtime_home === null)
    && (typeof value.cache_db_path === 'string' || value.cache_db_path === null)
    && (typeof value.control_plane_base_url === 'string' || value.control_plane_base_url === null || typeof value.control_plane_base_url === 'undefined')
    && (typeof value.release_environment === 'string' || value.release_environment === null || typeof value.release_environment === 'undefined')
    && (typeof value.release_profile_source === 'string' || value.release_profile_source === null || typeof value.release_profile_source === 'undefined')
    && (typeof value.updater_endpoint === 'string' || value.updater_endpoint === null || typeof value.updater_endpoint === 'undefined')
    && (typeof value.updater_pubkey_configured === 'boolean' || value.updater_pubkey_configured === null || typeof value.updater_pubkey_configured === 'undefined')
    && (typeof value.hub_service_state === 'string' || value.hub_service_state === null || typeof value.hub_service_state === 'undefined')
    && (typeof value.hub_service_url === 'string' || value.hub_service_url === null || typeof value.hub_service_url === 'undefined')
    && (typeof value.hub_manifest_url === 'string' || value.hub_manifest_url === null || typeof value.hub_manifest_url === 'undefined');
}
