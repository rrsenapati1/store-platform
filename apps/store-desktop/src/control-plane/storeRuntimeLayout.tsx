import {
  ActionButton,
  RuntimeShell,
  RuntimeShellNavRail,
  RuntimeShellStatusStrip,
  StatusBadge,
  StoreThemeModeToggle,
} from '@store/ui';
import type { ReactNode } from 'react';
import { StoreRuntimeEntrySurface } from './storeRuntimeEntrySurface';
import { StoreRuntimeManagerSurface } from './storeRuntimeManagerSurface';
import { StoreRuntimeOperationsSurface } from './storeRuntimeOperationsSurface';
import { StoreRuntimeReturnsSurface } from './storeRuntimeReturnsSurface';
import { StoreRuntimeSellSurface } from './storeRuntimeSellSurface';
import { getStoreRuntimeScreenDefinition, type StoreRuntimeScreenId } from './storeRuntimeScreens';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function resolveSessionTone(isReady: boolean): 'success' | 'warning' {
  return isReady ? 'success' : 'warning';
}

export function StoreRuntimeLayout(props: {
  workspace: StoreRuntimeWorkspaceState;
  activeScreen: StoreRuntimeScreenId;
  visibleScreens: StoreRuntimeScreenId[];
  onSelectScreen: (screenId: StoreRuntimeScreenId) => void;
  runtimeReady: boolean;
}) {
  const screenDefinition = getStoreRuntimeScreenDefinition(props.activeScreen);
  const branchName = props.workspace.branches?.[0]?.name || props.workspace.branchId || 'Branch runtime';
  const isIdentityLocked = props.workspace.runtimeShellKind === 'packaged_desktop'
    && !props.workspace.isSessionLive
    && (props.workspace.requiresLocalUnlock || props.workspace.requiresPinEnrollment);
  const actorName = isIdentityLocked ? 'Locked runtime' : props.workspace.actor?.full_name ?? 'No active actor';

  let content: ReactNode = null;
  if (props.activeScreen === 'entry') {
    content = <StoreRuntimeEntrySurface workspace={props.workspace} onResumeSelling={() => props.onSelectScreen('sell')} />;
  } else if (props.activeScreen === 'sell') {
    content = <StoreRuntimeSellSurface workspace={props.workspace} />;
  } else if (props.activeScreen === 'returns') {
    content = <StoreRuntimeReturnsSurface workspace={props.workspace} />;
  } else if (props.activeScreen === 'operations') {
    content = <StoreRuntimeOperationsSurface workspace={props.workspace} />;
  } else if (props.activeScreen === 'manager') {
    content = <StoreRuntimeManagerSurface workspace={props.workspace} />;
  }

  return (
    <RuntimeShell
      navRail={(
        <RuntimeShellNavRail
          label="Store desktop"
          title={branchName}
          subtitle="Touch-first branch runtime with scanner and keyboard acceleration."
        >
          {props.visibleScreens.map((screenId) => {
            const definition = getStoreRuntimeScreenDefinition(screenId);
            const isActive = screenId === props.activeScreen;
            return (
              <button
                key={screenId}
                type="button"
                aria-current={isActive ? 'page' : undefined}
                aria-label={definition.label}
                onClick={() => props.onSelectScreen(screenId)}
                style={{
                  border: isActive ? '1px solid rgba(15, 58, 140, 0.28)' : '1px solid rgba(23,32,51,0.08)',
                  borderRadius: '16px',
                  background: isActive ? '#eaf1ff' : '#ffffff',
                  color: '#172033',
                  textAlign: 'left',
                  padding: '14px 16px',
                  display: 'grid',
                  gap: '4px',
                  cursor: 'pointer',
                }}
              >
                <strong>{definition.label}</strong>
                <span aria-hidden="true" style={{ fontSize: '12px', color: '#5a6477', lineHeight: 1.45 }}>
                  {definition.description}
                </span>
              </button>
            );
          })}
        </RuntimeShellNavRail>
      )}
      statusStrip={(
        <RuntimeShellStatusStrip
          label="Runtime"
          title={screenDefinition.label}
          detail={`${actorName} :: ${branchName}`}
          actions={(
            <>
              <StatusBadge label={props.runtimeReady ? 'Live' : 'Idle'} tone={resolveSessionTone(props.runtimeReady)} />
              <StoreThemeModeToggle />
              {props.workspace.isSessionLive ? (
                <ActionButton onClick={() => void props.workspace.refreshRuntimeSession()} disabled={props.workspace.isBusy}>
                  Refresh
                </ActionButton>
              ) : null}
            </>
          )}
        />
      )}
      footer={(
        <>
          <div style={{ display: 'grid', gap: '4px' }}>
            <strong>{props.workspace.activeCashierSession?.session_number ?? 'Register not open'}</strong>
            <span style={{ fontSize: '12px', color: '#5a6477' }}>
              {props.workspace.runtimeShellLabel ?? 'Runtime shell'} :: {props.workspace.runtimeHostname ?? 'Browser-managed'}
            </span>
          </div>
          <div style={{ fontSize: '12px', color: '#5a6477' }}>
            {props.workspace.checkoutPaymentSession
              ? `Payment session ${props.workspace.checkoutPaymentSession.lifecycle_status}`
              : 'One active cart at a time'}
          </div>
        </>
      )}
    >
      {content}
    </RuntimeShell>
  );
}
