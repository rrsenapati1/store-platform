import { createBrowserStoreRuntimeCache, resolveBrowserStorage } from './browserStoreRuntimeCache';
import { createNativeStoreRuntimeCache, isNativeStoreRuntimeAvailable } from './nativeStoreRuntimeCache';
import type {
  StorageLike,
  StoreRuntimeCacheAdapter,
  StoreRuntimeCacheInvoke,
} from './storeRuntimeCacheContract';

export * from './storeRuntimeCacheContract';
export { createBrowserStoreRuntimeCache } from './browserStoreRuntimeCache';
export { createNativeStoreRuntimeCache, isNativeStoreRuntimeAvailable } from './nativeStoreRuntimeCache';

interface CreateResolvedStoreRuntimeCacheOptions {
  browserStorage?: () => StorageLike | null | undefined;
  invoke?: StoreRuntimeCacheInvoke;
  isNativeRuntime?: () => boolean;
}

export function createResolvedStoreRuntimeCache(options: CreateResolvedStoreRuntimeCacheOptions = {}): StoreRuntimeCacheAdapter {
  const browserAdapter = createBrowserStoreRuntimeCache(options.browserStorage ?? resolveBrowserStorage);
  if (!(options.isNativeRuntime ?? isNativeStoreRuntimeAvailable)()) {
    return browserAdapter;
  }
  return createNativeStoreRuntimeCache({ invoke: options.invoke });
}
