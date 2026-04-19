import { useEffect, useRef } from 'react';
import { consumeLocalDevBootstrapFromWindow } from '@store/auth';
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
import { OwnerWorkspaceShell } from './OwnerWorkspaceShell';
import { useOwnerWorkspace } from './useOwnerWorkspace';

function buildMetrics(branchCount: number, onboardingStatus: string | undefined, hasActor: boolean): WorkspaceMetric[] {
  return [
    { label: 'Branches', value: String(branchCount) },
    { label: 'Onboarding', value: onboardingStatus ?? 'Pending', tone: onboardingStatus === 'BRANCH_READY' ? 'success' : 'warning' },
    { label: 'Session', value: hasActor ? 'Live' : 'Not started', tone: hasActor ? 'success' : 'warning' },
  ];
}

export function OwnerWorkspace() {
  const workspace = useOwnerWorkspace();
  const bootstrapRef = useRef<ReturnType<typeof consumeLocalDevBootstrapFromWindow> | null>(null);
  const didAutoStartRef = useRef(false);
  const metrics = buildMetrics(workspace.branches.length, workspace.tenant?.onboarding_status, Boolean(workspace.actor));

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
    return <OwnerWorkspaceShell workspace={workspace} />;
  }

  return (
    <AppShell
      kicker="Tenant owner"
      title="Owner Command Center"
      subtitle="A multi-branch oversight surface for live operations, commercial controls, catalog authority, and workforce governance."
      actions={<StoreThemeModeToggle />}
    >
      <MetricGrid metrics={metrics} />

      <SectionCard eyebrow="Secure entry" title="Owner session">
        <FormField
          id="owner-korsenex-token"
          label="Korsenex token"
          value={workspace.korsenexToken}
          onChange={workspace.setKorsenexToken}
          placeholder="stub:sub=owner-1;email=owner@acme.local;name=Acme Owner"
        />
        <ActionButton onClick={() => void workspace.startSession()} disabled={workspace.isBusy || !workspace.korsenexToken}>
          Start owner session
        </ActionButton>
        {workspace.errorMessage ? <p style={{ color: 'var(--store-danger, #9d2b19)', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
      </SectionCard>

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
              value: (
                <StatusBadge label="LIGHT / DARK READY" tone="success" />
              ),
            },
          ]}
        />
      </SectionCard>
    </AppShell>
  );
}
