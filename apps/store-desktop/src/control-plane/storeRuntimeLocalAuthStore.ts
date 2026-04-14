import { invoke as tauriInvoke } from '@tauri-apps/api/core';

const STORE_RUNTIME_LOCAL_AUTH_KEY = 'store.runtime-local-auth.v1';
export const STORE_RUNTIME_LOCAL_AUTH_SCHEMA_VERSION = 1;

export interface StoreRuntimeLocalAuthRecord {
  schema_version: typeof STORE_RUNTIME_LOCAL_AUTH_SCHEMA_VERSION;
  installation_id: string;
  device_id: string;
  staff_profile_id: string;
  local_auth_token: string;
  activation_version: number;
  offline_valid_until: string;
  pin_attempt_limit: number;
  pin_lockout_seconds: number;
  pin_salt: string;
  pin_hash: string;
  failed_attempts: number;
  locked_until: string | null;
  enrolled_at: string;
  last_unlocked_at: string | null;
}

function isNativeRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isLocalAuthRecord(value: unknown): value is StoreRuntimeLocalAuthRecord {
  return isObject(value)
    && value.schema_version === STORE_RUNTIME_LOCAL_AUTH_SCHEMA_VERSION
    && typeof value.installation_id === 'string'
    && typeof value.device_id === 'string'
    && typeof value.staff_profile_id === 'string'
    && typeof value.local_auth_token === 'string'
    && typeof value.activation_version === 'number'
    && typeof value.offline_valid_until === 'string'
    && typeof value.pin_attempt_limit === 'number'
    && typeof value.pin_lockout_seconds === 'number'
    && typeof value.pin_salt === 'string'
    && typeof value.pin_hash === 'string'
    && typeof value.failed_attempts === 'number'
    && (typeof value.locked_until === 'string' || value.locked_until === null)
    && typeof value.enrolled_at === 'string'
    && (typeof value.last_unlocked_at === 'string' || value.last_unlocked_at === null);
}

function resolveBrowserStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const storage = window.localStorage ?? null;
  if (
    !storage
    || typeof storage.getItem !== 'function'
    || typeof storage.setItem !== 'function'
    || typeof storage.removeItem !== 'function'
  ) {
    return null;
  }
  return storage;
}

export async function loadStoreRuntimeLocalAuth(): Promise<StoreRuntimeLocalAuthRecord | null> {
  if (isNativeRuntime()) {
    const result = await tauriInvoke<StoreRuntimeLocalAuthRecord | null>('cmd_load_store_runtime_local_auth');
    return isLocalAuthRecord(result) ? result : null;
  }
  const storage = resolveBrowserStorage();
  if (!storage) {
    return null;
  }
  const raw = storage.getItem(STORE_RUNTIME_LOCAL_AUTH_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isLocalAuthRecord(parsed) ? parsed : null;
  } catch {
    storage.removeItem(STORE_RUNTIME_LOCAL_AUTH_KEY);
    return null;
  }
}

export async function saveStoreRuntimeLocalAuth(localAuth: StoreRuntimeLocalAuthRecord): Promise<void> {
  if (isNativeRuntime()) {
    await tauriInvoke('cmd_save_store_runtime_local_auth', { localAuth });
    return;
  }
  resolveBrowserStorage()?.setItem(STORE_RUNTIME_LOCAL_AUTH_KEY, JSON.stringify(localAuth));
}

export async function clearStoreRuntimeLocalAuth(): Promise<void> {
  if (isNativeRuntime()) {
    await tauriInvoke('cmd_clear_store_runtime_local_auth');
    return;
  }
  resolveBrowserStorage()?.removeItem(STORE_RUNTIME_LOCAL_AUTH_KEY);
}

export function isStoreRuntimeLocalAuthOfflineExpired(localAuth: StoreRuntimeLocalAuthRecord, now = Date.now()): boolean {
  const offlineValidUntil = Date.parse(localAuth.offline_valid_until);
  if (Number.isNaN(offlineValidUntil)) {
    return true;
  }
  return offlineValidUntil <= now;
}
