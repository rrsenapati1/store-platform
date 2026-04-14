import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import {
  resolveBrowserStorage as resolveSharedBrowserStorage,
  type StorageLike,
} from '../storage/browserStorage';

const STORE_RUNTIME_SESSION_KEY = 'store.runtime-session.v1';

export interface StoreRuntimeSessionRecord {
  access_token: string;
  expires_at: string;
}

function isNativeRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function isSessionRecord(value: unknown): value is StoreRuntimeSessionRecord {
  return typeof value === 'object'
    && value !== null
    && typeof (value as Record<string, unknown>).access_token === 'string'
    && typeof (value as Record<string, unknown>).expires_at === 'string';
}

function resolveBrowserStorage(): StorageLike | null {
  return resolveSharedBrowserStorage();
}

export async function loadStoreRuntimeSession(): Promise<StoreRuntimeSessionRecord | null> {
  if (isNativeRuntime()) {
    const result = await tauriInvoke<StoreRuntimeSessionRecord | null>('cmd_load_store_runtime_session');
    return isSessionRecord(result) ? result : null;
  }
  const storage = resolveBrowserStorage();
  if (!storage) {
    return null;
  }
  const raw = storage.getItem(STORE_RUNTIME_SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isSessionRecord(parsed) ? parsed : null;
  } catch {
    storage.removeItem(STORE_RUNTIME_SESSION_KEY);
    return null;
  }
}

export async function saveStoreRuntimeSession(session: StoreRuntimeSessionRecord): Promise<void> {
  if (isNativeRuntime()) {
    await tauriInvoke('cmd_save_store_runtime_session', { session });
    return;
  }
  resolveBrowserStorage()?.setItem(STORE_RUNTIME_SESSION_KEY, JSON.stringify(session));
}

export async function clearStoreRuntimeSession(): Promise<void> {
  if (isNativeRuntime()) {
    await tauriInvoke('cmd_clear_store_runtime_session');
    return;
  }
  resolveBrowserStorage()?.removeItem(STORE_RUNTIME_SESSION_KEY);
}

export function isStoreRuntimeSessionExpired(session: StoreRuntimeSessionRecord, now = Date.now()): boolean {
  const expiresAt = Date.parse(session.expires_at);
  if (Number.isNaN(expiresAt)) {
    return true;
  }
  return expiresAt <= now;
}
