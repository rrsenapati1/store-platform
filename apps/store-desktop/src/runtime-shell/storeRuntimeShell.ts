import { createBrowserStoreRuntimeShell, resolveBrowserRuntimeWindow } from './browserStoreRuntimeShell';
import { createNativeStoreRuntimeShell, isNativeStoreRuntimeShellAvailable } from './nativeStoreRuntimeShell';
import type {
  BrowserRuntimeShellWindow,
  StoreRuntimeShellAdapter,
  StoreRuntimeShellInvoke,
} from './storeRuntimeShellContract';

export * from './storeRuntimeShellContract';
export { createBrowserStoreRuntimeShell } from './browserStoreRuntimeShell';
export { createNativeStoreRuntimeShell, isNativeStoreRuntimeShellAvailable } from './nativeStoreRuntimeShell';

interface CreateResolvedStoreRuntimeShellOptions {
  browserWindow?: () => BrowserRuntimeShellWindow | null | undefined;
  invoke?: StoreRuntimeShellInvoke;
  isNativeRuntime?: () => boolean;
}

export function createResolvedStoreRuntimeShell(options: CreateResolvedStoreRuntimeShellOptions = {}): StoreRuntimeShellAdapter {
  if ((options.isNativeRuntime ?? isNativeStoreRuntimeShellAvailable)()) {
    return createNativeStoreRuntimeShell({ invoke: options.invoke });
  }
  return createBrowserStoreRuntimeShell(options.browserWindow ?? resolveBrowserRuntimeWindow);
}
