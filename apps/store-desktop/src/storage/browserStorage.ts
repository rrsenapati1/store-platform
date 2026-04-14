export type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

export function isStorageLike(value: unknown): value is StorageLike {
  return typeof value === 'object'
    && value !== null
    && typeof (value as StorageLike).getItem === 'function'
    && typeof (value as StorageLike).setItem === 'function'
    && typeof (value as StorageLike).removeItem === 'function';
}

function isVitestRuntime() {
  return Boolean(import.meta.env?.VITEST);
}

function isNativeStorageObject(value: unknown) {
  return Object.prototype.toString.call(value) === '[object Storage]';
}

function resolveStorageFromValueDescriptor(target: object | null | undefined): StorageLike | null {
  if (!target) {
    return null;
  }
  const descriptor = Object.getOwnPropertyDescriptor(target, 'localStorage');
  if (!descriptor || !('value' in descriptor)) {
    return null;
  }
  if (isNativeStorageObject(descriptor.value)) {
    return null;
  }
  return isStorageLike(descriptor.value) ? descriptor.value : null;
}

export function resolveBrowserStorage(): StorageLike | null {
  if (isVitestRuntime()) {
    return resolveStorageFromValueDescriptor(globalThis)
      ?? resolveStorageFromValueDescriptor(typeof window !== 'undefined' ? window : undefined);
  }

  if (typeof document !== 'undefined' && document.defaultView) {
    try {
      const storage = document.defaultView.localStorage;
      return isStorageLike(storage) ? storage : null;
    } catch {
      return null;
    }
  }

  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const storage = window.localStorage;
    return isStorageLike(storage) ? storage : null;
  } catch {
    return null;
  }
}
