/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreThemeProvider } from '@store/ui';
import { PlatformAdminWorkspaceShell } from './PlatformAdminWorkspaceShell';

function createWorkspace(overrides: Record<string, unknown> = {}) {
  return {
    actor: {
      user_id: 'user-platform',
      email: 'admin@store.local',
      full_name: 'Platform Admin',
      is_platform_admin: true,
      tenant_memberships: [],
      branch_memberships: [],
    },
    activeSection: 'overview',
    activeTenantId: 'tenant-acme',
    activeTenantLifecycle: {
      tenant_id: 'tenant-acme',
      subscription: { lifecycle_status: 'TRIALING' },
      entitlement: {
        active_plan_code: 'launch-starter',
        lifecycle_status: 'TRIALING',
        device_limit: 4,
      },
    },
    billingPlans: [],
    environmentContract: {
      deployment_environment: 'staging',
      public_base_url: 'https://control.staging.store.korsenex.com',
      release_version: '2026.04.19',
      log_format: 'json',
      sentry_configured: true,
      sentry_environment: 'staging',
      object_storage_configured: true,
      object_storage_bucket: 'bucket',
      object_storage_prefix: 'prefix',
    },
    errorMessage: '',
    isBusy: false,
    latestInvite: null,
    observabilitySummary: {
      operations: {
        recent_failure_records: [],
      },
      runtime: {
        branches: [],
      },
      backup: {
        release_version: '2026.04.19',
      },
    },
    overviewModel: {
      commandContext: {
        environmentLabel: 'staging',
        releaseLabel: '2026.04.19',
        healthLabel: 'Healthy',
        healthTone: 'success',
      },
      postureSignals: [{ label: 'Release readiness', value: 'Healthy', tone: 'success' }],
      criticalExceptions: [{ id: 'dead-letter-jobs', title: 'Dead-letter jobs', detail: '1 jobs require review.', tone: 'danger' }],
      tenantExceptions: [{ id: 'tenant-acme', title: 'Acme Retail', detail: 'Owner invite pending.', tone: 'warning' }],
      runtimeHighlights: [{ label: 'Queue posture', value: '0 queued / 0 running' }],
      releaseHighlights: [{ label: 'Public base URL', value: 'https://control.staging.store.korsenex.com' }],
    },
    ownerEmail: '',
    ownerFullName: '',
    planAmountMinor: '',
    planBranchLimit: '',
    planCode: '',
    planDeviceLimit: '',
    planName: '',
    securityControls: {
      secure_headers_enabled: true,
      secure_headers_hsts_enabled: true,
      secure_headers_csp: "default-src 'self'",
      rate_limits: { window_seconds: 60, auth_requests: 8, activation_requests: 6, webhook_requests: 120 },
    },
    tenantName: '',
    tenantSlug: '',
    tenants: [
      {
        tenant_id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'OWNER_INVITE_PENDING',
      },
    ],
    createBillingPlan: vi.fn(),
    createTenant: vi.fn(),
    reactivateActiveTenantAccess: vi.fn(),
    refreshObservabilitySummary: vi.fn(),
    refreshPlatformPosture: vi.fn(),
    selectTenant: vi.fn(),
    sendOwnerInvite: vi.fn(),
    setActiveSection: vi.fn(),
    setKorsenexToken: vi.fn(),
    setOwnerEmail: vi.fn(),
    setOwnerFullName: vi.fn(),
    setPlanAmountMinor: vi.fn(),
    setPlanBranchLimit: vi.fn(),
    setPlanCode: vi.fn(),
    setPlanDeviceLimit: vi.fn(),
    setPlanName: vi.fn(),
    setTenantName: vi.fn(),
    setTenantSlug: vi.fn(),
    startSession: vi.fn(),
    suspendActiveTenantAccess: vi.fn(),
    ...overrides,
  };
}

describe('PlatformAdminWorkspaceShell', () => {
  test('defaults to overview and exposes top-level navigation', () => {
    const workspace = createWorkspace();
    render(
      <StoreThemeProvider storageKey="platform-admin.shell.test.theme">
        <PlatformAdminWorkspaceShell workspace={workspace as never} />
      </StoreThemeProvider>,
    );

    expect(screen.getByText('Critical exceptions')).toBeInTheDocument();
    expect(screen.getByText('Dead-letter jobs')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Release' }));
    expect(workspace.setActiveSection).toHaveBeenCalledWith('release');
  });
});
