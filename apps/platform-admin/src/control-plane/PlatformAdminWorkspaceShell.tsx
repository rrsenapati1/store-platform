import {
  ActionButton,
  DetailList,
  FormField,
  PlatformCommandHeader,
  PlatformCommandShell,
  PlatformExceptionBoard,
  PlatformNavRail,
  PlatformPanel,
  PlatformSignalRow,
  StatusBadge,
  StoreThemeModeToggle,
} from '@store/ui';
import { type PlatformAdminSection } from './platformAdminOverviewModel';
import type { usePlatformAdminWorkspace } from './usePlatformAdminWorkspace';

type PlatformAdminWorkspaceState = ReturnType<typeof usePlatformAdminWorkspace>;

const navItems: Array<{ id: PlatformAdminSection; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'release', label: 'Release' },
  { id: 'operations', label: 'Operations' },
  { id: 'tenants', label: 'Tenants' },
  { id: 'commercial', label: 'Commercial' },
  { id: 'settings', label: 'Settings' },
];

function titleForSection(section: PlatformAdminSection) {
  switch (section) {
    case 'release':
      return {
        title: 'Release posture',
        subtitle: 'Certification, security, rollback, and evidence posture for the current control-plane release.',
      };
    case 'operations':
      return {
        title: 'Operations',
        subtitle: 'Queue health, branch runtime degradation, backup freshness, and active failure posture.',
      };
    case 'tenants':
      return {
        title: 'Tenant governance',
        subtitle: 'Tenant lifecycle, owner binding, and top tenant exceptions across the platform.',
      };
    case 'commercial':
      return {
        title: 'Commercial policy',
        subtitle: 'Platform billing-plan catalog and tenant commercial lifecycle posture.',
      };
    case 'settings':
      return {
        title: 'Settings',
        subtitle: 'Operator session, environment identity, and platform contract details.',
      };
    default:
      return {
        title: 'Overview',
        subtitle: 'Platform health, release posture, and the operator exceptions that need attention right now.',
      };
  }
}

function renderOverview(workspace: PlatformAdminWorkspaceState) {
  return (
    <>
      <PlatformSignalRow items={workspace.overviewModel.postureSignals} />

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(320px, 0.8fr)' }}>
        <PlatformPanel title="Critical exceptions" subtitle="These are the platform issues to review first.">
          <PlatformExceptionBoard
            items={workspace.overviewModel.criticalExceptions}
            emptyState="No platform-wide release or operations exceptions are active."
          />
        </PlatformPanel>
        <PlatformPanel title="Tenant exceptions" subtitle="Cross-tenant lifecycle issues that need operator attention.">
          <PlatformExceptionBoard
            items={workspace.overviewModel.tenantExceptions}
            emptyState="No tenant lifecycle or onboarding exceptions are active."
          />
        </PlatformPanel>
      </div>

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
        <PlatformPanel title="Runtime and operations" subtitle="Queue and branch runtime posture across the platform.">
          <DetailList items={workspace.overviewModel.runtimeHighlights} />
          {workspace.observabilitySummary?.operations.recent_failure_records.length ? (
            <div style={{ display: 'grid', gap: '10px' }}>
              {workspace.observabilitySummary.operations.recent_failure_records.slice(0, 3).map((record) => (
                <div
                  key={record.id}
                  style={{
                    border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
                    borderRadius: 'var(--store-radius-control, 14px)',
                    background: 'var(--store-surface-panel, rgba(251,252,255,0.94))',
                    padding: '12px 14px',
                  }}
                >
                  <strong style={{ display: 'block', color: 'var(--store-text-strong, #172033)' }}>{record.job_type}</strong>
                  <span style={{ color: 'var(--store-text-muted, #5a6477)', fontSize: '14px' }}>
                    {record.branch_id} · {record.status}
                    {record.last_error ? ` · ${record.last_error}` : ''}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
        </PlatformPanel>
        <PlatformPanel title="Release evidence" subtitle="Current release, security, and retention posture from live control-plane reads.">
          <DetailList items={workspace.overviewModel.releaseHighlights} />
        </PlatformPanel>
      </div>
    </>
  );
}

function renderRelease(workspace: PlatformAdminWorkspaceState) {
  return (
    <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
      <PlatformPanel title="Release context" subtitle="Environment and deployment identity for the current control plane.">
        <DetailList
          items={[
            { label: 'Environment', value: workspace.environmentContract?.deployment_environment ?? 'Unavailable' },
            { label: 'Release version', value: workspace.environmentContract?.release_version ?? 'Unavailable' },
            { label: 'Public base URL', value: workspace.environmentContract?.public_base_url ?? 'Unavailable' },
            { label: 'Log format', value: workspace.environmentContract?.log_format ?? 'Unavailable' },
          ]}
        />
      </PlatformPanel>
      <PlatformPanel title="Security controls" subtitle="Secure header and rate-limit posture exposed by the live system contract.">
        <DetailList
          items={[
            {
              label: 'Secure headers',
              value: workspace.securityControls?.secure_headers_enabled ? <StatusBadge label="ENABLED" tone="success" /> : <StatusBadge label="DISABLED" tone="warning" />,
            },
            {
              label: 'HSTS',
              value: workspace.securityControls?.secure_headers_hsts_enabled ? <StatusBadge label="ENABLED" tone="success" /> : <StatusBadge label="DISABLED" tone="warning" />,
            },
            { label: 'CSP', value: workspace.securityControls?.secure_headers_csp ?? 'Unavailable' },
            { label: 'Rate-limit window', value: workspace.securityControls ? `${workspace.securityControls.rate_limits.window_seconds}s` : 'Unavailable' },
          ]}
        />
      </PlatformPanel>
      <PlatformPanel title="Release-critical exceptions" subtitle="Failing release signals visible from the current deployment.">
        <PlatformExceptionBoard
          items={workspace.overviewModel.criticalExceptions}
          emptyState="No release-critical posture issues are currently surfaced by the live control-plane reads."
        />
      </PlatformPanel>
      <PlatformPanel title="Retention and storage posture" subtitle="Evidence and backup durability prerequisites.">
        <DetailList
          items={[
            {
              label: 'Object storage',
              value: workspace.environmentContract?.object_storage_configured ? <StatusBadge label="CONFIGURED" tone="success" /> : <StatusBadge label="NOT CONFIGURED" tone="warning" />,
            },
            { label: 'Bucket', value: workspace.environmentContract?.object_storage_bucket ?? 'Unavailable' },
            { label: 'Prefix', value: workspace.environmentContract?.object_storage_prefix ?? 'Unavailable' },
            { label: 'Backup release', value: workspace.observabilitySummary?.backup.release_version ?? 'Unavailable' },
          ]}
        />
      </PlatformPanel>
    </div>
  );
}

function renderOperations(workspace: PlatformAdminWorkspaceState) {
  return (
    <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
      <PlatformPanel title="Operations queue" subtitle="Live failure and retry posture for asynchronous control-plane work.">
        <DetailList
          items={[
            { label: 'Queued jobs', value: String(workspace.observabilitySummary?.operations.queued_count ?? 0) },
            { label: 'Running jobs', value: String(workspace.observabilitySummary?.operations.running_count ?? 0) },
            { label: 'Retryable jobs', value: String(workspace.observabilitySummary?.operations.retryable_count ?? 0) },
            { label: 'Dead-letter jobs', value: String(workspace.observabilitySummary?.operations.dead_letter_count ?? 0) },
          ]}
        />
        {workspace.observabilitySummary?.operations.recent_failure_records.length ? (
          <PlatformExceptionBoard
            items={workspace.observabilitySummary.operations.recent_failure_records.map((record) => ({
              id: record.id,
              title: `${record.job_type} in ${record.branch_id}`,
              detail: `${record.status} after ${record.attempt_count}/${record.max_attempts} attempts${record.last_error ? ` · ${record.last_error}` : ''}`,
              tone: record.status === 'DEAD_LETTER' ? 'danger' : 'warning',
            }))}
          />
        ) : null}
      </PlatformPanel>
      <PlatformPanel title="Branch runtime posture" subtitle="Degraded branch runtime state and conflict depth across the platform.">
        <DetailList
          items={[
            { label: 'Tracked branches', value: String(workspace.observabilitySummary?.runtime.tracked_branch_count ?? 0) },
            { label: 'Degraded branches', value: String(workspace.observabilitySummary?.runtime.degraded_branch_count ?? 0) },
            { label: 'Open conflicts', value: String(workspace.observabilitySummary?.runtime.open_conflict_count ?? 0) },
            { label: 'Max outbox depth', value: String(workspace.observabilitySummary?.runtime.max_local_outbox_depth ?? 0) },
          ]}
        />
        {workspace.observabilitySummary?.runtime.branches.length ? (
          <PlatformExceptionBoard
            items={workspace.observabilitySummary.runtime.branches.map((branch) => ({
              id: `${branch.tenant_id}:${branch.branch_id}`,
              title: `${branch.branch_id} on ${branch.hub_device_id}`,
              detail: `${branch.runtime_state} · ${branch.open_conflict_count} conflicts · outbox ${branch.local_outbox_depth}`,
              tone: branch.runtime_state === 'HEALTHY' ? 'success' : 'warning',
            }))}
          />
        ) : null}
      </PlatformPanel>
    </div>
  );
}

function renderTenants(workspace: PlatformAdminWorkspaceState) {
  return (
    <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'minmax(0, 1fr) minmax(320px, 0.9fr)' }}>
      <PlatformPanel title="Tenant lifecycle" subtitle="Create tenants, inspect tenant posture, and route tenant exceptions.">
        <FormField id="tenant-name" label="Tenant name" value={workspace.tenantName} onChange={workspace.setTenantName} />
        <FormField id="tenant-slug" label="Tenant slug" value={workspace.tenantSlug} onChange={workspace.setTenantSlug} />
        <ActionButton
          onClick={() => void workspace.createTenant()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.tenantName || !workspace.tenantSlug}
        >
          Create tenant
        </ActionButton>
        <div style={{ display: 'grid', gap: '12px', marginTop: '18px' }}>
          {workspace.tenants.map((tenant) => {
            const active = tenant.tenant_id === workspace.activeTenantId;
            return (
              <button
                key={tenant.tenant_id}
                type="button"
                onClick={() => void workspace.selectTenant(tenant.tenant_id)}
                style={{
                  border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
                  borderRadius: 'var(--store-radius-control, 14px)',
                  background: active ? 'var(--store-accent-soft, rgba(31,79,191,0.12))' : 'var(--store-surface-panel, rgba(251,252,255,0.94))',
                  padding: '14px',
                  textAlign: 'left',
                  cursor: 'pointer',
                }}
              >
                <strong style={{ display: 'block', color: 'var(--store-text-strong, #172033)' }}>{tenant.name}</strong>
                <span style={{ color: 'var(--store-text-muted, #5a6477)', fontSize: '14px' }}>
                  {tenant.slug} · {tenant.status} · {tenant.onboarding_status}
                </span>
              </button>
            );
          })}
        </div>
      </PlatformPanel>
      <PlatformPanel title="Owner binding and entitlement" subtitle="Current owner invite posture and tenant lifecycle actions.">
        <p style={{ margin: 0, color: 'var(--store-text-muted, #5a6477)' }}>
          Target tenant: {workspace.activeTenantId || 'Select or create a tenant first'}
        </p>
        <FormField id="owner-email" label="Owner email" value={workspace.ownerEmail} onChange={workspace.setOwnerEmail} />
        <FormField id="owner-full-name" label="Owner full name" value={workspace.ownerFullName} onChange={workspace.setOwnerFullName} />
        <ActionButton
          onClick={() => void workspace.sendOwnerInvite()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.activeTenantId || !workspace.ownerEmail || !workspace.ownerFullName}
        >
          Send owner invite
        </ActionButton>
        {workspace.latestInvite ? (
          <DetailList
            items={[
              { label: 'Latest invite', value: workspace.latestInvite.email },
              { label: 'Invite status', value: workspace.latestInvite.status },
            ]}
          />
        ) : null}
        {workspace.activeTenantLifecycle ? (
          <>
            <DetailList
              items={[
                { label: 'Plan', value: workspace.activeTenantLifecycle.entitlement.active_plan_code },
                { label: 'Subscription', value: workspace.activeTenantLifecycle.subscription.lifecycle_status },
                { label: 'Entitlement', value: workspace.activeTenantLifecycle.entitlement.lifecycle_status },
                { label: 'Device limit', value: String(workspace.activeTenantLifecycle.entitlement.device_limit) },
              ]}
            />
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
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
        ) : null}
      </PlatformPanel>
    </div>
  );
}

function renderCommercial(workspace: PlatformAdminWorkspaceState) {
  return (
    <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'minmax(0, 1fr) minmax(320px, 0.9fr)' }}>
      <PlatformPanel title="Billing plan catalog" subtitle="Platform-level commercial policy and default plan posture.">
        <FormField id="plan-code" label="Plan code" value={workspace.planCode} onChange={workspace.setPlanCode} />
        <FormField id="plan-name" label="Plan name" value={workspace.planName} onChange={workspace.setPlanName} />
        <FormField id="plan-amount-minor" label="Plan monthly amount (minor units)" value={workspace.planAmountMinor} onChange={workspace.setPlanAmountMinor} />
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
      </PlatformPanel>
      <PlatformPanel title="Current plan catalog" subtitle="Read-only visibility into active platform billing plans.">
        <div style={{ display: 'grid', gap: '12px' }}>
          {workspace.billingPlans.map((plan) => (
            <div
              key={plan.id}
              style={{
                border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
                borderRadius: 'var(--store-radius-control, 14px)',
                background: 'var(--store-surface-panel, rgba(251,252,255,0.94))',
                padding: '14px',
              }}
            >
              <strong style={{ display: 'block', color: 'var(--store-text-strong, #172033)' }}>{plan.display_name}</strong>
              <span style={{ color: 'var(--store-text-muted, #5a6477)', fontSize: '14px' }}>
                {plan.code} · {plan.branch_limit} branches · {plan.device_limit} devices · {plan.amount_minor} minor units
              </span>
            </div>
          ))}
        </div>
      </PlatformPanel>
    </div>
  );
}

function renderSettings(workspace: PlatformAdminWorkspaceState) {
  return (
    <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
      <PlatformPanel title="Platform session" subtitle="Operator identity and control-plane session posture.">
        <DetailList
          items={[
            { label: 'Actor', value: workspace.actor?.full_name ?? 'Signed out' },
            { label: 'Email', value: workspace.actor?.email ?? 'Unavailable' },
            {
              label: 'Session',
              value: workspace.actor ? <StatusBadge label="LIVE" tone="success" /> : <StatusBadge label="NOT STARTED" tone="warning" />,
            },
          ]}
        />
      </PlatformPanel>
      <PlatformPanel title="Environment contract" subtitle="Read-only platform settings exposed by the deployed control plane.">
        <DetailList
          items={[
            { label: 'Environment', value: workspace.environmentContract?.deployment_environment ?? 'Unavailable' },
            { label: 'Sentry', value: workspace.environmentContract?.sentry_configured ? `Configured (${workspace.environmentContract.sentry_environment})` : 'Not configured' },
            { label: 'Object storage', value: workspace.environmentContract?.object_storage_configured ? 'Configured' : 'Not configured' },
            { label: 'Log format', value: workspace.environmentContract?.log_format ?? 'Unavailable' },
          ]}
        />
      </PlatformPanel>
    </div>
  );
}

export function PlatformAdminWorkspaceShell(props: { workspace: PlatformAdminWorkspaceState }) {
  const { workspace } = props;
  const sectionMeta = titleForSection(workspace.activeSection);

  return (
    <PlatformCommandShell
      navRail={(
        <PlatformNavRail
          title="Korsenex Platform"
          subtitle="Cross-tenant control tower"
          items={navItems}
          activeItemId={workspace.activeSection}
          onSelect={(id) => workspace.setActiveSection(id as PlatformAdminSection)}
        />
      )}
      commandHeader={(
        <PlatformCommandHeader
          title={sectionMeta.title}
          subtitle={sectionMeta.subtitle}
          environmentLabel={workspace.overviewModel.commandContext.environmentLabel}
          releaseLabel={workspace.overviewModel.commandContext.releaseLabel}
          statusLabel={workspace.overviewModel.commandContext.healthLabel}
          statusTone={workspace.overviewModel.commandContext.healthTone}
          actions={(
            <>
              <ActionButton onClick={() => void workspace.refreshPlatformPosture()} disabled={workspace.isBusy || !workspace.actor}>
                Refresh posture
              </ActionButton>
              <StoreThemeModeToggle />
            </>
          )}
        />
      )}
    >
      {workspace.activeSection === 'overview' ? renderOverview(workspace) : null}
      {workspace.activeSection === 'release' ? renderRelease(workspace) : null}
      {workspace.activeSection === 'operations' ? renderOperations(workspace) : null}
      {workspace.activeSection === 'tenants' ? renderTenants(workspace) : null}
      {workspace.activeSection === 'commercial' ? renderCommercial(workspace) : null}
      {workspace.activeSection === 'settings' ? renderSettings(workspace) : null}
    </PlatformCommandShell>
  );
}
