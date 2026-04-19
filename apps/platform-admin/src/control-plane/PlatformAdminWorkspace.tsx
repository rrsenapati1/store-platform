import { useEffect, useRef } from 'react';
import { consumeLocalDevBootstrapFromWindow } from '@store/auth';
import { ActionButton, AppShell, DetailList, FormField, MetricGrid, SectionCard, StatusBadge } from '@store/ui';
import type { WorkspaceMetric } from '@store/types';
import { usePlatformAdminWorkspace } from './usePlatformAdminWorkspace';

function buildMetrics(tenantCount: number, activeTenantId: string, isLive: boolean): WorkspaceMetric[] {
  return [
    { label: 'Tenants', value: String(tenantCount) },
    { label: 'Selected tenant', value: activeTenantId || 'None' },
    { label: 'Session', value: isLive ? 'Live' : 'Not started', tone: isLive ? 'success' : 'warning' },
  ];
}

export function PlatformAdminWorkspace() {
  const workspace = usePlatformAdminWorkspace();
  const bootstrapRef = useRef<ReturnType<typeof consumeLocalDevBootstrapFromWindow> | null>(null);
  const didAutoStartRef = useRef(false);
  const metrics = buildMetrics(workspace.tenants.length, workspace.activeTenantId, Boolean(workspace.actor));

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

  return (
    <AppShell
      kicker="Platform super admin"
      title="Platform Onboarding Control Plane"
      subtitle="Tenant creation, owner binding, and Milestone 1 onboarding state for the enterprise control-plane reset."
    >
      <MetricGrid metrics={metrics} />

      <SectionCard eyebrow="Admin session bootstrap" title="Control-plane session">
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
        {workspace.actor ? (
          <div style={{ marginTop: '16px' }}>
            <DetailList
              items={[
                { label: 'Actor', value: workspace.actor.full_name },
                { label: 'Email', value: workspace.actor.email },
                { label: 'Platform access', value: <StatusBadge label="READY" tone="success" /> },
              ]}
            />
          </div>
        ) : null}
        {workspace.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
      </SectionCard>

      <SectionCard eyebrow="Tenant onboarding pipeline" title="Tenant list and creation">
        <FormField id="tenant-name" label="Tenant name" value={workspace.tenantName} onChange={workspace.setTenantName} />
        <FormField id="tenant-slug" label="Tenant slug" value={workspace.tenantSlug} onChange={workspace.setTenantSlug} />
        <ActionButton
          onClick={() => void workspace.createTenant()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.tenantName || !workspace.tenantSlug}
        >
          Create tenant
        </ActionButton>
        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.tenants.map((tenant) => (
            <li key={tenant.tenant_id}>
              <button
                type="button"
                onClick={() => void workspace.selectTenant(tenant.tenant_id)}
                style={{ border: 0, background: 'transparent', color: '#25314f', cursor: 'pointer', fontWeight: tenant.tenant_id === workspace.activeTenantId ? 700 : 500 }}
              >
                {tenant.name}
              </button>{' '}
              <StatusBadge label={tenant.onboarding_status} tone={tenant.onboarding_status === 'BRANCH_READY' ? 'success' : 'warning'} />
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Owner invite dispatch" title="Owner binding">
        <p style={{ marginTop: 0, color: '#4e5871' }}>Target tenant: {workspace.activeTenantId || 'Select or create a tenant first'}</p>
        <FormField id="owner-email" label="Owner email" value={workspace.ownerEmail} onChange={workspace.setOwnerEmail} />
        <FormField id="owner-full-name" label="Owner full name" value={workspace.ownerFullName} onChange={workspace.setOwnerFullName} />
        <ActionButton
          onClick={() => void workspace.sendOwnerInvite()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.activeTenantId || !workspace.ownerEmail || !workspace.ownerFullName}
        >
          Send owner invite
        </ActionButton>
        {workspace.latestInvite ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest owner invite</h3>
            <DetailList
              items={[
                { label: 'Email', value: workspace.latestInvite.email },
                { label: 'Full name', value: workspace.latestInvite.full_name },
                { label: 'Status', value: <StatusBadge label={workspace.latestInvite.status} tone="warning" /> },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Commercial catalog" title="Billing plan catalog">
        <FormField id="plan-code" label="Plan code" value={workspace.planCode} onChange={workspace.setPlanCode} />
        <FormField id="plan-name" label="Plan name" value={workspace.planName} onChange={workspace.setPlanName} />
        <FormField
          id="plan-amount-minor"
          label="Plan monthly amount (minor units)"
          value={workspace.planAmountMinor}
          onChange={workspace.setPlanAmountMinor}
        />
        <FormField id="plan-branch-limit" label="Plan branch limit" value={workspace.planBranchLimit} onChange={workspace.setPlanBranchLimit} />
        <FormField id="plan-device-limit" label="Plan device limit" value={workspace.planDeviceLimit} onChange={workspace.setPlanDeviceLimit} />
        <ActionButton
          onClick={() => void workspace.createBillingPlan()}
          disabled={
            workspace.isBusy ||
            !workspace.actor ||
            !workspace.planCode ||
            !workspace.planName ||
            !workspace.planAmountMinor ||
            !workspace.planBranchLimit ||
            !workspace.planDeviceLimit
          }
        >
          Create billing plan
        </ActionButton>
        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.billingPlans.map((plan) => (
            <li key={plan.id}>
              {plan.display_name}{' '}
              {plan.is_default ? <StatusBadge label="DEFAULT" tone="success" /> : <StatusBadge label={plan.status} tone="neutral" />}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Tenant commercial posture" title="Commercial lifecycle">
        {workspace.activeTenantLifecycle ? (
          <>
            <DetailList
              items={[
                { label: 'Plan', value: workspace.activeTenantLifecycle.entitlement.active_plan_code },
                {
                  label: 'Subscription',
                  value: (
                    <StatusBadge
                      label={workspace.activeTenantLifecycle.subscription.lifecycle_status}
                      tone={workspace.activeTenantLifecycle.subscription.lifecycle_status === 'ACTIVE' ? 'success' : 'warning'}
                    />
                  ),
                },
                {
                  label: 'Entitlement',
                  value: (
                    <StatusBadge
                      label={workspace.activeTenantLifecycle.entitlement.lifecycle_status}
                      tone={workspace.activeTenantLifecycle.entitlement.lifecycle_status === 'ACTIVE' ? 'success' : 'warning'}
                    />
                  ),
                },
                { label: 'Device limit', value: String(workspace.activeTenantLifecycle.entitlement.device_limit) },
              ]}
            />
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
              <ActionButton
                onClick={() => void workspace.suspendActiveTenantAccess()}
                disabled={workspace.isBusy || workspace.activeTenantLifecycle.entitlement.lifecycle_status === 'SUSPENDED'}
              >
                Suspend tenant access
              </ActionButton>
              <ActionButton
                onClick={() => void workspace.reactivateActiveTenantAccess()}
                disabled={workspace.isBusy || workspace.activeTenantLifecycle.entitlement.lifecycle_status !== 'SUSPENDED'}
              >
                Reactivate tenant access
              </ActionButton>
            </div>
          </>
        ) : (
          <p style={{ margin: 0, color: '#4e5871' }}>Select a tenant to inspect commercial lifecycle.</p>
        )}
      </SectionCard>

      <SectionCard eyebrow="Platform observability" title="Operations queue">
        {workspace.observabilitySummary ? (
          <>
            <DetailList
              items={[
                { label: 'Environment', value: workspace.observabilitySummary.environment },
                { label: 'Release', value: workspace.observabilitySummary.release_version },
                { label: 'Dead-letter jobs', value: String(workspace.observabilitySummary.operations.dead_letter_count) },
                { label: 'Degraded branches', value: String(workspace.observabilitySummary.runtime.degraded_branch_count) },
                {
                  label: 'Backup',
                  value: (
                    <StatusBadge
                      label={workspace.observabilitySummary.backup.status.toUpperCase()}
                      tone={workspace.observabilitySummary.backup.status === 'ok' ? 'success' : 'warning'}
                    />
                  ),
                },
              ]}
            />
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
              <ActionButton onClick={() => void workspace.refreshObservabilitySummary()} disabled={workspace.isBusy || !workspace.actor}>
                Refresh observability
              </ActionButton>
            </div>
            <div style={{ marginTop: '16px' }}>
              <h3 style={{ marginBottom: '10px' }}>Recent failing jobs</h3>
              {workspace.observabilitySummary.operations.recent_failure_records.length ? (
                <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
                  {workspace.observabilitySummary.operations.recent_failure_records.map((record) => (
                    <li key={record.id}>
                      <strong>{record.job_type}</strong> in {record.branch_id} with status{' '}
                      <StatusBadge label={record.status} tone={record.status === 'DEAD_LETTER' ? 'warning' : 'neutral'} />
                      {record.last_error ? `: ${record.last_error}` : ''}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ margin: 0, color: '#4e5871' }}>No retryable or dead-letter jobs.</p>
              )}
            </div>
            <div style={{ marginTop: '16px' }}>
              <h3 style={{ marginBottom: '10px' }}>Degraded branches</h3>
              {workspace.observabilitySummary.runtime.branches.length ? (
                <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
                  {workspace.observabilitySummary.runtime.branches.map((branch) => (
                    <li key={`${branch.tenant_id}:${branch.branch_id}`}>
                      {branch.branch_id} on {branch.hub_device_id}{' '}
                      <StatusBadge label={branch.runtime_state} tone={branch.runtime_state === 'HEALTHY' ? 'success' : 'warning'} />{' '}
                      with {branch.open_conflict_count} open conflicts and outbox depth {branch.local_outbox_depth}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ margin: 0, color: '#4e5871' }}>No tracked branch runtime degradation.</p>
              )}
            </div>
            <div style={{ marginTop: '16px' }}>
              <h3 style={{ marginBottom: '10px' }}>Backup posture</h3>
              <DetailList
                items={[
                  { label: 'Metadata key', value: workspace.observabilitySummary.backup.metadata_key || 'Unavailable' },
                  { label: 'Backup release', value: workspace.observabilitySummary.backup.release_version || 'Unavailable' },
                  {
                    label: 'Last successful backup',
                    value: workspace.observabilitySummary.backup.last_successful_backup_at || 'Unavailable',
                  },
                ]}
              />
            </div>
          </>
        ) : (
          <p style={{ margin: 0, color: '#4e5871' }}>Start a session to load deployment, queue, and runtime observability.</p>
        )}
      </SectionCard>
    </AppShell>
  );
}
