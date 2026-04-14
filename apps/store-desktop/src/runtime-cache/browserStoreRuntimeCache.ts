import {
  STORE_RUNTIME_CACHE_KEY,
  type StorageLike,
  type StoreRuntimeCacheAdapter,
  type StoreRuntimeCachePersistence,
  type StoreRuntimeCacheSnapshot,
  isStorageLike,
  isStoreRuntimeCacheSnapshot,
} from './storeRuntimeCacheContract';

type StorageResolver = () => StorageLike | null | undefined;

function buildPersistence(args: {
  cachedAt: string | null;
  location?: string | null;
  snapshotPresent: boolean;
}): StoreRuntimeCachePersistence {
  return {
    backend_kind: 'browser_storage',
    backend_label: 'Browser local storage',
    cached_at: args.cachedAt,
    detail: null,
    location: args.location ?? STORE_RUNTIME_CACHE_KEY,
    snapshot_present: args.snapshotPresent,
  };
}

export function resolveBrowserStorage(): StorageLike | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return isStorageLike(window.localStorage) ? window.localStorage : null;
}

export function createBrowserStoreRuntimeCache(resolveStorage: StorageResolver = resolveBrowserStorage): StoreRuntimeCacheAdapter {
  return {
    async load() {
      const storage = resolveStorage();
      if (!storage) {
        return null;
      }
      const raw = storage.getItem(STORE_RUNTIME_CACHE_KEY);
      if (!raw) {
        return null;
      }
      try {
        const parsed = JSON.parse(raw) as unknown;
        if (!isStoreRuntimeCacheSnapshot(parsed)) {
          storage.removeItem(STORE_RUNTIME_CACHE_KEY);
          return null;
        }
        return parsed;
      } catch {
        storage.removeItem(STORE_RUNTIME_CACHE_KEY);
        return null;
      }
    },
    async save(snapshot: StoreRuntimeCacheSnapshot) {
      const storage = resolveStorage();
      if (storage) {
        storage.setItem(STORE_RUNTIME_CACHE_KEY, JSON.stringify(snapshot));
      }
      return buildPersistence({
        cachedAt: snapshot.cached_at,
        snapshotPresent: Boolean(storage),
      });
    },
    async clear() {
      resolveStorage()?.removeItem(STORE_RUNTIME_CACHE_KEY);
      return buildPersistence({
        cachedAt: null,
        snapshotPresent: false,
      });
    },
    async getPersistence() {
      const snapshot = await this.load();
      return buildPersistence({
        cachedAt: snapshot?.cached_at ?? null,
        snapshotPresent: Boolean(snapshot),
      });
    },
  };
}
