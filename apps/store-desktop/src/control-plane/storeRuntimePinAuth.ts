import type { StoreRuntimeLocalAuthRecord } from './storeRuntimeLocalAuthStore';

export const STORE_RUNTIME_PIN_ATTEMPT_LIMIT = 5;
export const STORE_RUNTIME_PIN_LOCKOUT_SECONDS = 300;
const STORE_RUNTIME_PIN_PBKDF2_ITERATIONS = 120_000;

function getCrypto(): Crypto {
  if (!globalThis.crypto?.subtle) {
    throw new Error('Web Crypto is unavailable for runtime PIN hashing');
  }
  return globalThis.crypto;
}

function encodeBase64(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function decodeBase64(value: string): Uint8Array {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

export function isStoreRuntimePinFormatValid(pin: string): boolean {
  return /^\d{4}$/.test(pin.trim());
}

export function createStoreRuntimePinSalt(): string {
  const bytes = new Uint8Array(16);
  getCrypto().getRandomValues(bytes);
  return encodeBase64(bytes);
}

export async function hashStoreRuntimePin(pin: string, salt: string): Promise<string> {
  const normalizedPin = pin.trim();
  const crypto = getCrypto();
  const saltBytes = decodeBase64(salt);
  const saltBuffer = new ArrayBuffer(saltBytes.byteLength);
  new Uint8Array(saltBuffer).set(saltBytes);
  const importedKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(normalizedPin),
    'PBKDF2',
    false,
    ['deriveBits'],
  );
  const derivedBits = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      hash: 'SHA-256',
      iterations: STORE_RUNTIME_PIN_PBKDF2_ITERATIONS,
      salt: saltBuffer,
    },
    importedKey,
    256,
  );
  return encodeBase64(new Uint8Array(derivedBits));
}

export async function verifyStoreRuntimePin(pin: string, localAuth: StoreRuntimeLocalAuthRecord): Promise<boolean> {
  const expectedHash = await hashStoreRuntimePin(pin, localAuth.pin_salt);
  return expectedHash === localAuth.pin_hash;
}

export function isStoreRuntimePinLocked(localAuth: StoreRuntimeLocalAuthRecord, now = Date.now()): boolean {
  if (!localAuth.locked_until) {
    return false;
  }
  const lockedUntil = Date.parse(localAuth.locked_until);
  if (Number.isNaN(lockedUntil)) {
    return false;
  }
  return lockedUntil > now;
}

export function recordFailedStoreRuntimePinAttempt(
  localAuth: StoreRuntimeLocalAuthRecord,
  now = Date.now(),
): StoreRuntimeLocalAuthRecord {
  const nextFailedAttempts = localAuth.failed_attempts + 1;
  const shouldLock = nextFailedAttempts >= localAuth.pin_attempt_limit;
  return {
    ...localAuth,
    failed_attempts: shouldLock ? 0 : nextFailedAttempts,
    locked_until: shouldLock
      ? new Date(now + (localAuth.pin_lockout_seconds * 1000)).toISOString()
      : null,
  };
}

export function recordSuccessfulStoreRuntimePinUnlock(
  localAuth: StoreRuntimeLocalAuthRecord,
  args: {
    lastUnlockedAt?: string;
    offlineValidUntil?: string;
  } = {},
): StoreRuntimeLocalAuthRecord {
  return {
    ...localAuth,
    failed_attempts: 0,
    locked_until: null,
    last_unlocked_at: args.lastUnlockedAt ?? new Date().toISOString(),
    offline_valid_until: args.offlineValidUntil ?? localAuth.offline_valid_until,
  };
}
