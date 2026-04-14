import { createBrowserStoreRuntimeHardware } from './browserStoreRuntimeHardware';
import { createNativeStoreRuntimeHardware, isNativeStoreRuntimeHardwareAvailable } from './nativeStoreRuntimeHardware';
import type {
  StoreRuntimeHardwareAdapter,
  StoreRuntimeHardwareInvoke,
} from './storeRuntimeHardwareContract';

export * from './storeRuntimeHardwareContract';
export { createBrowserStoreRuntimeHardware } from './browserStoreRuntimeHardware';
export { createNativeStoreRuntimeHardware, isNativeStoreRuntimeHardwareAvailable } from './nativeStoreRuntimeHardware';

interface CreateResolvedStoreRuntimeHardwareOptions {
  invoke?: StoreRuntimeHardwareInvoke;
  isNativeRuntime?: () => boolean;
}

export function createResolvedStoreRuntimeHardware(
  options: CreateResolvedStoreRuntimeHardwareOptions = {},
): StoreRuntimeHardwareAdapter {
  if ((options.isNativeRuntime ?? isNativeStoreRuntimeHardwareAvailable)()) {
    return createNativeStoreRuntimeHardware({ invoke: options.invoke });
  }
  return createBrowserStoreRuntimeHardware();
}
