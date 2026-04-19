import { useEffect, useRef } from 'react';
import { consumeLocalDevBootstrapFromWindow } from '@store/auth';
import { ActionButton, AppShell, DetailList, FormField, StatusBadge, StoreThemeModeToggle } from '@store/ui';
import { PlatformAdminWorkspaceShell } from './PlatformAdminWorkspaceShell';
import { usePlatformAdminWorkspace } from './usePlatformAdminWorkspace';

export function PlatformAdminWorkspace() {
  const workspace = usePlatformAdminWorkspace();
  const bootstrapRef = useRef<ReturnType<typeof consumeLocalDevBootstrapFromWindow> | null>(null);
  const didAutoStartRef = useRef(false);

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
    if (workspace.actor || workspace.isBusy || workspace.korsenexToken !== bootstrap.korsenexToken) {
      return;
    }
    didAutoStartRef.current = true;
    void workspace.startSession();
  }, [workspace.actor, workspace.isBusy, workspace.korsenexToken, workspace.startSession]);

  if (workspace.actor) {
    return <PlatformAdminWorkspaceShell workspace={workspace} />;
  }

  return (
    <AppShell
      kicker="Platform super admin"
      title="Platform Control Tower"
      subtitle="Bootstrap a control-plane session to inspect release posture, tenant governance, and platform operations."
      actions={<StoreThemeModeToggle />}
    >
      <section style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'minmax(0, 1.1fr) minmax(320px, 0.9fr)' }}>
        <section style={{ display: 'grid', gap: '20px' }}>
          <div
            style={{
              background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
              border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
              borderRadius: 'var(--store-radius-card, 20px)',
              boxShadow: 'var(--store-shadow-soft, 0 20px 48px rgba(23,32,51,0.10))',
              padding: '20px',
            }}
          >
            <p style={{ margin: 0, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--store-text-subtle, #75809b)' }}>
              Platform session bootstrap
            </p>
            <h2 style={{ margin: '10px 0 14px', fontSize: '24px', color: 'var(--store-text-strong, #172033)' }}>Start control plane session</h2>
            <FormField
              id="platform-korsenex-token"
              label="Korsenex token"
              value={workspace.korsenexToken}
              onChange={workspace.setKorsenexToken}
              placeholder="stub:sub=platform-1;email=admin@store.local;name=Platform Admin"
            />
            <ActionButton onClick={() => void workspace.startSession()} disabled={workspace.isBusy || !workspace.korsenexToken}>
              Start control plane session
            </ActionButton>
            {workspace.errorMessage ? <p style={{ color: 'var(--store-danger, #9d2b19)', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
          </div>
        </section>

        <div
          style={{
            background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
            border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
            borderRadius: 'var(--store-radius-card, 20px)',
            boxShadow: 'var(--store-shadow-soft, 0 20px 48px rgba(23,32,51,0.10))',
            padding: '20px',
            display: 'grid',
            gap: '16px',
            alignContent: 'start',
          }}
        >
          <div>
            <p style={{ margin: 0, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--store-text-subtle, #75809b)' }}>
              Control-tower posture
            </p>
            <h2 style={{ margin: '10px 0 8px', fontSize: '24px', color: 'var(--store-text-strong, #172033)' }}>What loads after bootstrap</h2>
            <p style={{ margin: 0, color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.6 }}>
              Release posture, security controls, queue degradation, tenant lifecycle exceptions, and commercial policy all move into a single platform shell once the session is live.
            </p>
          </div>
          <DetailList
            items={[
              { label: 'Default landing', value: 'Overview control tower' },
              { label: 'Top-level model', value: 'Release, Operations, Tenants, Commercial, Settings' },
              { label: 'Theme', value: <StatusBadge label="LIGHT / DARK" tone="success" /> },
            ]}
          />
        </div>
      </section>
    </AppShell>
  );
}
