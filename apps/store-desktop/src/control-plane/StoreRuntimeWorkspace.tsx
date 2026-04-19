import { useEffect, useRef, useState } from 'react';
import { consumeLocalDevBootstrapFromWindow } from '@store/auth';
import {
  clampRuntimeScreen,
  resolveDefaultRuntimeScreen,
  resolveVisibleRuntimeScreens,
  type StoreRuntimeScreenId,
} from './storeRuntimeScreens';
import { StoreRuntimeLayout } from './storeRuntimeLayout';
import { useStoreRuntimeWorkspace } from './useStoreRuntimeWorkspace';

export function StoreRuntimeWorkspace() {
  const workspace = useStoreRuntimeWorkspace();
  const bootstrapRef = useRef<ReturnType<typeof consumeLocalDevBootstrapFromWindow> | null>(null);
  const didAutoStartRef = useRef(false);
  const previousRuntimeReadyRef = useRef(false);
  const [requestedScreen, setRequestedScreen] = useState<StoreRuntimeScreenId>('entry');
  const isLocalAuthGateActive = workspace.runtimeShellKind === 'packaged_desktop'
    && (!workspace.hasLoadedLocalAuth || workspace.requiresPinEnrollment || workspace.requiresLocalUnlock);
  const runtimeReady = !isLocalAuthGateActive && workspace.isSessionLive && workspace.actor !== null;
  const visibilityArgs = { actor: workspace.actor, runtimeReady };
  const visibleScreens = resolveVisibleRuntimeScreens(visibilityArgs);
  const activeScreen = clampRuntimeScreen(requestedScreen, visibilityArgs);

  if (bootstrapRef.current == null && typeof window !== 'undefined') {
    bootstrapRef.current = consumeLocalDevBootstrapFromWindow(window);
  }

  useEffect(() => {
    const bootstrap = bootstrapRef.current;
    if (!bootstrap?.korsenexToken || workspace.korsenexToken === bootstrap.korsenexToken) {
      return;
    }
    workspace.setKorsenexToken(bootstrap.korsenexToken);
  }, [workspace.korsenexToken, workspace.setKorsenexToken]);

  useEffect(() => {
    const bootstrap = bootstrapRef.current;
    if (!bootstrap?.korsenexToken || !bootstrap.autoStart || didAutoStartRef.current) {
      return;
    }
    if (!workspace.supportsDeveloperSessionBootstrap || workspace.isSessionLive || workspace.isBusy) {
      return;
    }
    if (workspace.korsenexToken !== bootstrap.korsenexToken) {
      return;
    }
    didAutoStartRef.current = true;
    void workspace.startSession();
  }, [
    workspace.isBusy,
    workspace.isSessionLive,
    workspace.korsenexToken,
    workspace.startSession,
    workspace.supportsDeveloperSessionBootstrap,
  ]);

  useEffect(() => {
    const wasRuntimeReady = previousRuntimeReadyRef.current;
    setRequestedScreen((current) => {
      if (runtimeReady && !wasRuntimeReady) {
        return resolveDefaultRuntimeScreen(visibilityArgs);
      }
      return clampRuntimeScreen(current, visibilityArgs);
    });
    previousRuntimeReadyRef.current = runtimeReady;
  }, [runtimeReady, workspace.actor]);

  return (
    <StoreRuntimeLayout
      workspace={workspace}
      activeScreen={activeScreen}
      visibleScreens={visibleScreens}
      onSelectScreen={(screenId) => setRequestedScreen(clampRuntimeScreen(screenId, visibilityArgs))}
      runtimeReady={runtimeReady}
    />
  );
}
