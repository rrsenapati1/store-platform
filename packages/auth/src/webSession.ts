import type { ControlPlaneSession } from '@store/types';

export type StoreWebSessionRecord = {
  accessToken: string;
  expiresAt: string;
};

type StoreWebSessionSource = StoreWebSessionRecord | Pick<ControlPlaneSession, 'access_token' | 'expires_at'>;

export type StoreWebSessionExchange = (token: string) => Promise<StoreWebSessionSource>;
export type StoreWebSessionRefresh = (accessToken: string) => Promise<StoreWebSessionSource>;
export type StoreWebSessionSignOut = (accessToken: string) => Promise<void>;

export type StoreWebSessionCallback = {
  token: string | null;
  state: string | null;
  error: string | null;
};

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

const CALLBACK_PARAM_KEYS = ['token', 'korsenex_token', 'state', 'error', 'error_description'] as const;

function isStorageLike(value: unknown): value is StorageLike {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as StorageLike).getItem === 'function' &&
    typeof (value as StorageLike).setItem === 'function' &&
    typeof (value as StorageLike).removeItem === 'function'
  );
}

function resolveStorage(): StorageLike | null {
  if (typeof globalThis === 'undefined') {
    return null;
  }
  const candidate = (globalThis as { localStorage?: unknown }).localStorage;
  return isStorageLike(candidate) ? candidate : null;
}

function normalizeHashParams(hash: string | null | undefined): URLSearchParams {
  const trimmed = `${hash ?? ''}`.trim();
  if (!trimmed.startsWith('#')) {
    return new URLSearchParams();
  }
  return new URLSearchParams(trimmed.slice(1));
}

function normalizeRecord(source: StoreWebSessionSource): StoreWebSessionRecord {
  if ('accessToken' in source) {
    return source;
  }
  return {
    accessToken: source.access_token,
    expiresAt: source.expires_at,
  };
}

export function loadStoreWebSession(storageKey: string): StoreWebSessionRecord | null {
  const storage = resolveStorage();
  if (!storage) {
    return null;
  }
  const raw = storage.getItem(storageKey);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<StoreWebSessionRecord>;
    if (typeof parsed.accessToken !== 'string' || typeof parsed.expiresAt !== 'string') {
      return null;
    }
    return {
      accessToken: parsed.accessToken,
      expiresAt: parsed.expiresAt,
    };
  } catch {
    return null;
  }
}

export function saveStoreWebSession(storageKey: string, record: StoreWebSessionRecord): void {
  const storage = resolveStorage();
  if (!storage) {
    return;
  }
  storage.setItem(storageKey, JSON.stringify(record));
}

export function clearStoreWebSession(storageKey: string): void {
  const storage = resolveStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(storageKey);
}

export function isStoreWebSessionExpired(record: StoreWebSessionRecord, now = Date.now()): boolean {
  return Date.parse(record.expiresAt) <= now;
}

export function shouldRefreshStoreWebSession(
  record: StoreWebSessionRecord,
  now = Date.now(),
  leadSeconds = 120,
): boolean {
  return Date.parse(record.expiresAt) - now <= leadSeconds * 1000;
}

export function readKorsenexCallback(targetWindow: Pick<Window, 'location' | 'history'>): StoreWebSessionCallback {
  const searchParams = new URLSearchParams(`${targetWindow.location.search ?? ''}`.trim());
  const hashParams = normalizeHashParams(targetWindow.location.hash);
  const token = searchParams.get('token') ?? searchParams.get('korsenex_token') ?? hashParams.get('token') ?? hashParams.get('korsenex_token');
  const state = searchParams.get('state') ?? hashParams.get('state');
  const error = searchParams.get('error') ?? hashParams.get('error');
  let mutated = false;

  for (const key of CALLBACK_PARAM_KEYS) {
    if (searchParams.has(key)) {
      searchParams.delete(key);
      mutated = true;
    }
    if (hashParams.has(key)) {
      hashParams.delete(key);
      mutated = true;
    }
  }

  if (mutated) {
    const nextSearch = searchParams.toString();
    const nextHash = hashParams.toString();
    const nextUrl = `${targetWindow.location.pathname}${nextSearch ? `?${nextSearch}` : ''}${nextHash ? `#${nextHash}` : ''}`;
    targetWindow.history.replaceState(null, '', nextUrl);
  }

  return {
    error: error?.trim() || null,
    state: state?.trim() || null,
    token: token?.trim() || null,
  };
}

export function buildKorsenexSignInUrl(input: {
  authorizeBaseUrl: string;
  returnTo: string;
  state?: string;
}): string {
  const url = new URL(input.authorizeBaseUrl);
  url.searchParams.set('return_to', input.returnTo);
  if (input.state?.trim()) {
    url.searchParams.set('state', input.state.trim());
  }
  return url.toString();
}

export async function exchangeStoreWebSession(input: {
  token: string;
  exchange: StoreWebSessionExchange;
  storageKey: string;
}): Promise<StoreWebSessionRecord> {
  const record = normalizeRecord(await input.exchange(input.token));
  saveStoreWebSession(input.storageKey, record);
  return record;
}

export async function refreshStoreWebSession(input: {
  record: StoreWebSessionRecord;
  refresh: StoreWebSessionRefresh;
  storageKey: string;
}): Promise<StoreWebSessionRecord> {
  const refreshed = normalizeRecord(await input.refresh(input.record.accessToken));
  saveStoreWebSession(input.storageKey, refreshed);
  return refreshed;
}

export async function signOutStoreWebSession(input: {
  storageKey: string;
  accessToken: string;
  signOut: StoreWebSessionSignOut;
}): Promise<void> {
  try {
    await input.signOut(input.accessToken);
  } finally {
    clearStoreWebSession(input.storageKey);
  }
}
