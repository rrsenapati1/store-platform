import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import {
  resolveBrowserStorage as resolveSharedBrowserStorage,
  type StorageLike,
} from '../storage/browserStorage';

const STORE_RUNTIME_HUB_IDENTITY_KEY = 'store.runtime-hub-identity.v1';
export const STORE_RUNTIME_HUB_IDENTITY_SCHEMA_VERSION = 1;

export interface StoreRuntimeHubIdentityRecord {
  schema_version: typeof STORE_RUNTIME_HUB_IDENTITY_SCHEMA_VERSION;
  installation_id: string;
  tenant_id: string;
  branch_id: string;
  device_id: string;
  device_code: string;
  sync_access_secret: string;
  issued_at: string;
}

function isNativeRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isHubIdentityRecord(value: unknown): value is StoreRuntimeHubIdentityRecord {
  return isObject(value)
    && value.schema_version === STORE_RUNTIME_HUB_IDENTITY_SCHEMA_VERSION
    && typeof value.installation_id === 'string'
    && typeof value.tenant_id === 'string'
    && typeof value.branch_id === 'string'
    && typeof value.device_id === 'string'
    && typeof value.device_code === 'string'
    && typeof value.sync_access_secret === 'string'
    && typeof value.issued_at === 'string';
}

function resolveBrowserStorage(): StorageLike | null {
  return resolveSharedBrowserStorage();
}

export async function loadStoreRuntimeHubIdentity(): Promise<StoreRuntimeHubIdentityRecord | null> {
  if (isNativeRuntime()) {
    const result = await tauriInvoke<StoreRuntimeHubIdentityRecord | null>('cmd_load_store_runtime_hub_identity');
    return isHubIdentityRecord(result) ? result : null;
  }
  const storage = resolveBrowserStorage();
  if (!storage) {
    return null;
  }
  const raw = storage.getItem(STORE_RUNTIME_HUB_IDENTITY_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isHubIdentityRecord(parsed) ? parsed : null;
  } catch {
    storage.removeItem(STORE_RUNTIME_HUB_IDENTITY_KEY);
    return null;
  }
}

export async function saveStoreRuntimeHubIdentity(hubIdentity: StoreRuntimeHubIdentityRecord): Promise<void> {
  if (isNativeRuntime()) {
    await tauriInvoke('cmd_save_store_runtime_hub_identity', { hubIdentity });
    return;
  }
  resolveBrowserStorage()?.setItem(STORE_RUNTIME_HUB_IDENTITY_KEY, JSON.stringify(hubIdentity));
}

export async function clearStoreRuntimeHubIdentity(): Promise<void> {
  if (isNativeRuntime()) {
    await tauriInvoke('cmd_clear_store_runtime_hub_identity');
    return;
  }
  resolveBrowserStorage()?.removeItem(STORE_RUNTIME_HUB_IDENTITY_KEY);
}
