import {
  ActionButton,
  AppShell,
  DetailList,
  FormField,
  MetricGrid,
  StatusBadge,
  StoreThemeModeToggle,
} from '@store/ui';
import type { WorkspaceMetric } from '@store/types';

export type PlatformAdminSessionState = 'signed_out' | 'restoring' | 'expired' | 'revoked' | 'ready';

function buildMetrics(input: { hasSession: boolean; tenantCount: number; planCount: number }): WorkspaceMetric[] {
  return [
    { label: 'Tenants', value: String(input.tenantCount), tone: input.tenantCount > 0 ? 'success' : 'warning' },
    { label: 'Billing plans', value: String(input.planCount), tone: input.planCount > 0 ? 'success' : 'warning' },
    {
      label: 'Session',
      value: input.hasSession ? 'Live' : 'Sign-in required',
      tone: input.hasSession ? 'success' : 'warning',
    },
  ];
}

function resolveCopy(sessionState: PlatformAdminSessionState) {
  switch (sessionState) {
    case 'restoring':
      return {
        actionLabel: 'Restoring session…',
        body: 'Restoring the platform control tower and validating release, security, and tenant posture.',
        title: 'Restoring control plane session',
      };
    case 'expired':
      return {
        actionLabel: 'Sign in again',
        body: 'Your platform session expired. Start a fresh Korsenex sign-in to regain control-tower access.',
        title: 'Platform session expired',
      };
    case 'revoked':
      return {
        actionLabel: 'Start a new session',
        body: 'The previous platform session is no longer valid. Start a fresh Korsenex sign-in to continue.',
        title: 'Platform session requires recovery',
      };
    default:
      return {
        actionLabel: 'Sign in with Korsenex',
        body: 'Use your Korsenex identity to inspect release posture, tenant lifecycle, and operational exceptions from the platform control tower.',
        title: 'Platform sign-in',
      };
  }
}

export type PlatformAdminAuthEntrySurfaceProps = {
  errorMessage: string;
  isBusy: boolean;
  korsenexToken: string;
  onChangeKorsenexToken: (value: string) => void;
  onSignIn: () => void | Promise<void>;
  onStartSession: () => void | Promise<void>;
  planCount: number;
  sessionState: PlatformAdminSessionState;
  showLocalDeveloperControls: boolean;
  tenantCount: number;
};

export function PlatformAdminAuthEntrySurface(props: PlatformAdminAuthEntrySurfaceProps) {
  const metrics = buildMetrics({
    hasSession: false,
    planCount: props.planCount,
    tenantCount: props.tenantCount,
  });
  const copy = resolveCopy(props.sessionState);

  return (
    <AppShell
      kicker="Platform super admin"
      title="Platform Control Tower"
      subtitle="Inspect release posture, tenant governance, and platform operations from a single command surface."
      actions={<StoreThemeModeToggle />}
    >
      <MetricGrid metrics={metrics} />

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
              Platform sign-in
            </p>
            <h2 style={{ margin: '10px 0 14px', fontSize: '24px', color: 'var(--store-text-strong, #172033)' }}>{copy.title}</h2>
            <p style={{ marginTop: 0, color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.6 }}>{copy.body}</p>
            <ActionButton onClick={() => void props.onSignIn()} disabled={props.isBusy || props.sessionState === 'restoring'}>
              {copy.actionLabel}
            </ActionButton>
            {props.errorMessage ? <p style={{ color: 'var(--store-danger, #9d2b19)', marginBottom: 0 }}>{props.errorMessage}</p> : null}
          </div>

          {props.showLocalDeveloperControls ? (
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
                Developer bootstrap
              </p>
              <h2 style={{ margin: '10px 0 14px', fontSize: '24px', color: 'var(--store-text-strong, #172033)' }}>Local control-plane session</h2>
              <FormField
                id="platform-korsenex-token"
                label="Korsenex token"
                value={props.korsenexToken}
                onChange={props.onChangeKorsenexToken}
                placeholder="stub:sub=platform-1;email=admin@store.local;name=Platform Admin"
              />
              <ActionButton onClick={() => void props.onStartSession()} disabled={props.isBusy || !props.korsenexToken}>
                Start control plane session
              </ActionButton>
            </div>
          ) : null}
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
