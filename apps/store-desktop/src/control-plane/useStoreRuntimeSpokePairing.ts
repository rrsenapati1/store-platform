import { useEffect, useState } from 'react';
import type { ControlPlaneSpokeRuntimeActivation } from '@store/types';
import {
  issueStoreRuntimeSpokeActivation,
  loadStoreRuntimeHubManifest,
  STORE_RUNTIME_HUB_ALLOWED_RELAY_OPERATIONS,
  type StoreRuntimeHubManifest,
} from './storeRuntimeHubLocalClient';

type UseStoreRuntimeSpokePairingArgs = {
  isEnabled: boolean;
  runtimeHubManifestUrl: string | null;
  runtimeHubServiceUrl: string | null;
};

export function useStoreRuntimeSpokePairing({
  isEnabled,
  runtimeHubManifestUrl,
  runtimeHubServiceUrl,
}: UseStoreRuntimeSpokePairingArgs) {
  const [manifest, setManifest] = useState<StoreRuntimeHubManifest | null>(null);
  const [spokeActivation, setSpokeActivation] = useState<ControlPlaneSpokeRuntimeActivation | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    let isCancelled = false;

    if (!isEnabled || !runtimeHubManifestUrl) {
      setManifest(null);
      return () => {
        isCancelled = true;
      };
    }

    void loadStoreRuntimeHubManifest(runtimeHubManifestUrl)
      .then((nextManifest) => {
        if (!isCancelled) {
          setManifest(nextManifest);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setManifest(null);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [isEnabled, runtimeHubManifestUrl]);

  async function prepareDesktopSpokeActivation() {
    if (!isEnabled || !runtimeHubServiceUrl) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const activation = await issueStoreRuntimeSpokeActivation(runtimeHubServiceUrl, {
        runtimeProfile: 'desktop_spoke',
        pairingMode: 'qr',
      });
      setSpokeActivation(activation);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to prepare spoke activation');
    } finally {
      setIsBusy(false);
    }
  }

  return {
    errorMessage,
    isBusy,
    manifest,
    prepareDesktopSpokeActivation,
    relayOperations: STORE_RUNTIME_HUB_ALLOWED_RELAY_OPERATIONS,
    spokeActivation,
  };
}
