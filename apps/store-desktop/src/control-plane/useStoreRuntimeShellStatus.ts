import { useEffect, useState } from 'react';
import {
  createResolvedStoreRuntimeShell,
  type StoreRuntimeShellStatus,
} from '../runtime-shell/storeRuntimeShell';

export async function loadStoreRuntimeShellStatus() {
  return createResolvedStoreRuntimeShell().getStatus();
}

export function useStoreRuntimeShellStatus() {
  const [runtimeShellStatus, setRuntimeShellStatus] = useState<StoreRuntimeShellStatus | null>(null);
  const [runtimeShellError, setRuntimeShellError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    void loadStoreRuntimeShellStatus()
      .then((status) => {
        if (!isCancelled) {
          setRuntimeShellStatus(status);
          setRuntimeShellError(null);
        }
      })
      .catch((error) => {
        if (!isCancelled) {
          setRuntimeShellError(error instanceof Error ? error.message : 'Unable to load runtime shell status');
        }
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  return {
    runtimeShellError,
    runtimeShellStatus,
  };
}
