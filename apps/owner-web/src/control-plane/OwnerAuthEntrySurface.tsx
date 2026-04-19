import {
  ActionButton,
  AppShell,
  DetailList,
  FormField,
  MetricGrid,
  SectionCard,
  StatusBadge,
  StoreThemeModeToggle,
} from '@store/ui';
import type { WorkspaceMetric } from '@store/types';
import type { OwnerWorkspaceSessionState } from './ownerWorkspaceSession';

function buildMetrics(input: {
  branchCount: number;
  onboardingStatus?: string;
  hasSession: boolean;
}): WorkspaceMetric[] {
  return [
    { label: 'Branches', value: String(input.branchCount) },
    {
      label: 'Onboarding',
      value: input.onboardingStatus ?? 'Pending',
      tone: input.onboardingStatus === 'BRANCH_READY' ? 'success' : 'warning',
    },
    {
      label: 'Session',
      value: input.hasSession ? 'Live' : 'Sign-in required',
      tone: input.hasSession ? 'success' : 'warning',
    },
  ];
}

function resolveAuthCopy(sessionState: OwnerWorkspaceSessionState) {
  switch (sessionState) {
    case 'restoring':
      return {
        actionLabel: 'Restoring session…',
        body: 'Checking for a valid owner session and restoring tenant context.',
        title: 'Restoring owner session',
      };
    case 'expired':
      return {
        actionLabel: 'Sign in again',
        body: 'Your browser session expired. Start a fresh Korsenex sign-in to resume owner operations.',
        title: 'Owner session expired',
      };
    case 'revoked':
      return {
        actionLabel: 'Start a new session',
        body: 'The previous owner session is no longer valid. Start a fresh Korsenex sign-in to continue.',
        title: 'Owner session requires recovery',
      };
    default:
      return {
        actionLabel: 'Sign in with Korsenex',
        body: 'Use your Korsenex identity to open the owner command center for live operations, commercial controls, and workforce governance.',
        title: 'Owner sign-in',
      };
  }
}

export type OwnerAuthEntrySurfaceProps = {
  branchCount: number;
  errorMessage: string;
  isBusy: boolean;
  korsenexToken: string;
  onboardingStatus?: string;
  onStartSession: () => void | Promise<void>;
  onChangeKorsenexToken: (value: string) => void;
  onSignIn: () => void | Promise<void>;
  sessionState: OwnerWorkspaceSessionState;
  showLocalDeveloperControls: boolean;
};

export function OwnerAuthEntrySurface(props: OwnerAuthEntrySurfaceProps) {
  const metrics = buildMetrics({
    branchCount: props.branchCount,
    hasSession: false,
    onboardingStatus: props.onboardingStatus,
  });
  const authCopy = resolveAuthCopy(props.sessionState);

  return (
    <AppShell
      kicker="Tenant owner"
      title="Owner Command Center"
      subtitle="A multi-branch oversight surface for live operations, commercial controls, catalog authority, and workforce governance."
      actions={<StoreThemeModeToggle />}
    >
      <MetricGrid metrics={metrics} />

      <SectionCard eyebrow="Secure entry" title={authCopy.title}>
        <p style={{ color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.6, marginTop: 0 }}>{authCopy.body}</p>
        <ActionButton onClick={() => void props.onSignIn()} disabled={props.isBusy || props.sessionState === 'restoring'}>
          {authCopy.actionLabel}
        </ActionButton>
        {props.errorMessage ? <p style={{ color: 'var(--store-danger, #9d2b19)', marginBottom: 0 }}>{props.errorMessage}</p> : null}
      </SectionCard>

      {props.showLocalDeveloperControls ? (
        <SectionCard eyebrow="Developer bootstrap" title="Local owner session">
          <FormField
            id="owner-korsenex-token"
            label="Korsenex token"
            value={props.korsenexToken}
            onChange={props.onChangeKorsenexToken}
            placeholder="stub:sub=owner-1;email=owner@acme.local;name=Acme Owner"
          />
          <ActionButton onClick={() => void props.onStartSession()} disabled={props.isBusy || !props.korsenexToken}>
            Start owner session
          </ActionButton>
        </SectionCard>
      ) : null}

      <SectionCard eyebrow="What opens next" title="Command-center layout">
        <DetailList
          items={[
            { label: 'Overview', value: 'Cross-branch posture, exceptions, and drill-down' },
            { label: 'Operations', value: 'Receiving, expiry, replenishment, restock, and approvals' },
            { label: 'Commercial', value: 'Promotions, lifecycle, pricing, and customer signals' },
            { label: 'Catalog', value: 'Products, barcode flows, and branch catalog control' },
            { label: 'Workforce', value: 'Attendance, cashier sessions, shifts, and device governance' },
            {
              label: 'Theme system',
              value: <StatusBadge label="LIGHT / DARK READY" tone="success" />,
            },
          ]}
        />
      </SectionCard>
    </AppShell>
  );
}
