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
  const metrics = buildMetrics(workspace.tenants.length, workspace.activeTenantId, Boolean(workspace.actor));

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
                onClick={() => workspace.setActiveTenantId(tenant.tenant_id)}
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
    </AppShell>
  );
}
