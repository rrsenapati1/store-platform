import type { StoreRuntimeShellKind } from '../runtime-shell/storeRuntimeShell';

export type StoreRuntimeSessionRestorePolicy =
  | 'AUTO_RESTORE'
  | 'DEFER_TO_LOCAL_AUTH'
  | 'CLEAR_STALE_PACKAGED_SESSION';

export function resolveStoreRuntimeSessionRestorePolicy(args: {
  runtimeShellKind: StoreRuntimeShellKind | null;
  hasLocalAuthRecord: boolean;
}): StoreRuntimeSessionRestorePolicy {
  if (args.runtimeShellKind !== 'packaged_desktop') {
    return 'AUTO_RESTORE';
  }
  if (args.hasLocalAuthRecord) {
    return 'DEFER_TO_LOCAL_AUTH';
  }
  return 'CLEAR_STALE_PACKAGED_SESSION';
}
