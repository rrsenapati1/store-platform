import { afterEach, describe, expect, test } from 'vitest';
import { resolveBrowserStorage, type StorageLike } from './browserStorage';

function createStorageStub(): StorageLike {
  const store = new Map<string, string>();
  return {
    getItem(key) {
      return store.get(key) ?? null;
    },
    setItem(key, value) {
      store.set(key, value);
    },
    removeItem(key) {
      store.delete(key);
    },
  };
}

const originalWindow = globalThis.window;
const originalDocument = globalThis.document;
const originalLocalStorageDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');

afterEach(() => {
  if (typeof originalWindow === 'undefined') {
    Reflect.deleteProperty(globalThis, 'window');
  } else {
    Object.defineProperty(globalThis, 'window', {
      value: originalWindow,
      configurable: true,
      writable: true,
    });
  }

  if (typeof originalDocument === 'undefined') {
    Reflect.deleteProperty(globalThis, 'document');
  } else {
    Object.defineProperty(globalThis, 'document', {
      value: originalDocument,
      configurable: true,
      writable: true,
    });
  }

  if (originalLocalStorageDescriptor) {
    Object.defineProperty(globalThis, 'localStorage', originalLocalStorageDescriptor);
  } else {
    Reflect.deleteProperty(globalThis, 'localStorage');
  }
});

describe('resolveBrowserStorage', () => {
  test('uses an explicitly stubbed localStorage value without touching the global window getter', () => {
    const storage = createStorageStub();
    const explodingWindow = {} as Window;
    Object.defineProperty(explodingWindow, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('window localStorage getter should not be touched');
      },
    });

    Object.defineProperty(globalThis, 'window', {
      value: explodingWindow,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(globalThis, 'localStorage', {
      value: storage,
      configurable: true,
      writable: true,
    });

    expect(resolveBrowserStorage()).toBe(storage);
  });

  test('returns null when no safe browser storage is available', () => {
    const explodingWindow = {} as Window;
    Object.defineProperty(explodingWindow, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('missing storage');
      },
    });

    Object.defineProperty(globalThis, 'window', {
      value: explodingWindow,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(globalThis, 'document', {
      value: {
        defaultView: null,
      },
      configurable: true,
      writable: true,
    });

    expect(resolveBrowserStorage()).toBeNull();
  });
});
