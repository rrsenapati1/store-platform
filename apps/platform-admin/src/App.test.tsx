/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from './App';

type MockResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

function jsonResponse(body: unknown, status = 200): MockResponse {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

function observabilitySummaryResponse() {
  return {
    environment: 'staging',
    release_version: '2026.04.15-observability',
    system_health: {
      status: 'ok',
      environment: 'staging',
      public_base_url: 'https://control.staging.store.korsenex.com',
      release_version: '2026.04.15-observability',
      database: { status: 'ok', detail: null },
      operations_worker: { configured: true, poll_seconds: 5, batch_size: 25, lease_seconds: 60 },
    },
    operations: {
      queued_count: 0,
      running_count: 0,
      retryable_count: 0,
      dead_letter_count: 1,
      recent_failure_records: [
        {
          id: 'job-dead-letter-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-acme',
          job_type: 'UNKNOWN_JOB',
          status: 'DEAD_LETTER',
          attempt_count: 1,
          max_attempts: 1,
          last_error: 'Unsupported operations job type: UNKNOWN_JOB',
          dead_lettered_at: '2026-04-15T02:05:00',
          updated_at: '2026-04-15T02:05:00',
        },
      ],
    },
    runtime: {
      tracked_branch_count: 1,
      degraded_branch_count: 1,
      connected_spoke_count: 2,
      open_conflict_count: 1,
      max_local_outbox_depth: 3,
      branches: [
        {
          tenant_id: 'tenant-acme',
          branch_id: 'branch-acme',
          hub_device_id: 'hub-device-1',
          runtime_state: 'DEGRADED',
          connected_spoke_count: 2,
          local_outbox_depth: 3,
          open_conflict_count: 1,
          last_heartbeat_at: '2026-04-15T02:04:00',
          last_local_spoke_sync_at: '2026-04-15T02:03:00',
        },
      ],
    },
    backup: {
      configured: true,
      status: 'ok',
      last_successful_backup_at: '2026-04-15T02:00:00',
      metadata_key: 'control-plane/staging/postgres-backups/20260415T020000Z/metadata.json',
      release_version: '2026.04.15-observability',
      age_hours: 1.5,
      detail: null,
    },
  };
}

function securityControlsResponse() {
  return {
    secure_headers_enabled: true,
    secure_headers_hsts_enabled: true,
    secure_headers_csp: "default-src 'self'",
    rate_limits: {
      window_seconds: 60,
      auth_requests: 8,
      activation_requests: 6,
      webhook_requests: 120,
    },
  };
}

function environmentContractResponse() {
  return {
    deployment_environment: 'staging',
    public_base_url: 'https://control.staging.store.korsenex.com',
    release_version: '2026.04.15-observability',
    log_format: 'json',
    sentry_configured: true,
    sentry_environment: 'staging',
    object_storage_configured: true,
    object_storage_bucket: 'store-staging-evidence',
    object_storage_prefix: 'control-plane/staging',
    operations_worker: {
      configured: true,
      poll_seconds: 5,
      batch_size: 25,
      lease_seconds: 60,
    },
    security_controls: securityControlsResponse(),
  };
}

function tenantLifecycleResponse(tenantId: string, lifecycleStatus = 'TRIALING') {
  return {
    tenant_id: tenantId,
    subscription: {
      id: `sub-${tenantId}`,
      tenant_id: tenantId,
      billing_plan_id: 'plan-launch',
      provider_name: null,
      provider_customer_id: null,
      provider_subscription_id: null,
      lifecycle_status: 'TRIALING',
      mandate_status: null,
      trial_started_at: '2026-04-14T00:00:00',
      trial_ends_at: '2026-04-28T00:00:00',
      current_period_started_at: null,
      current_period_ends_at: null,
      grace_until: null,
      canceled_at: null,
    },
    entitlement: {
      id: `ent-${tenantId}`,
      tenant_id: tenantId,
      billing_plan_id: 'plan-launch',
      active_plan_code: 'launch-starter',
      lifecycle_status: lifecycleStatus,
      branch_limit: 2,
      device_limit: 4,
      offline_runtime_hours: 48,
      grace_until: null,
      suspend_at: '2026-05-03T00:00:00',
      feature_flags: { offline_continuity: true },
      policy_source: lifecycleStatus === 'SUSPENDED' ? 'tenant_status' : 'subscription',
      policy_metadata: { reason: lifecycleStatus === 'SUSPENDED' ? 'Billing review hold' : 'trial_issued' },
    },
    active_override: null,
  };
}

describe('platform admin control tower flow', () => {
  const originalFetch = globalThis.fetch;

  function mockResponses(responses: MockResponse[]) {
    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;
  }

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    window.history.replaceState(null, '', '/');
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('shows the platform sign-in surface instead of a production token gate', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Platform sign-in' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in with Korsenex' })).toBeInTheDocument();
  });

  test('auto-starts a session from local bootstrap URL parameters into the control tower', async () => {
    mockResponses([
      jsonResponse({ access_token: 'session-platform', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-platform',
        email: 'admin@store.local',
        full_name: 'Platform Admin',
        is_platform_admin: true,
        tenant_memberships: [],
        branch_memberships: [],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse(observabilitySummaryResponse()),
      jsonResponse(securityControlsResponse()),
      jsonResponse(environmentContractResponse()),
    ]);

    window.history.replaceState(
      null,
      '',
      '/#stub_sub=platform-1&stub_email=admin@store.local&stub_name=Platform%20Admin',
    );

    render(<App />);

    expect(await screen.findByText('Env: staging')).toBeInTheDocument();
    expect(screen.getByText('Release: 2026.04.15-observability')).toBeInTheDocument();
    expect(screen.queryByLabelText('Korsenex token')).not.toBeInTheDocument();
  });

  test('creates a tenant and sends an owner invite through the tenant surface', async () => {
    mockResponses([
      jsonResponse({ access_token: 'session-platform', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-platform',
        email: 'admin@store.local',
        full_name: 'Platform Admin',
        is_platform_admin: true,
        tenant_memberships: [],
        branch_memberships: [],
      }),
      jsonResponse({
        records: [
          {
            tenant_id: 'tenant-acme',
            name: 'Acme Retail',
            slug: 'acme-retail',
            status: 'ACTIVE',
            onboarding_status: 'OWNER_INVITE_PENDING',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'plan-launch',
            code: 'launch-starter',
            display_name: 'Launch Starter',
            billing_cadence: 'monthly',
            currency_code: 'INR',
            amount_minor: 149900,
            trial_days: 14,
            branch_limit: 2,
            device_limit: 4,
            offline_runtime_hours: 48,
            grace_window_days: 5,
            feature_flags: { offline_continuity: true },
            provider_plan_refs: { cashfree: 'cf_plan_launch_starter', razorpay: 'rp_plan_launch_starter' },
            is_default: true,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse(observabilitySummaryResponse()),
      jsonResponse(securityControlsResponse()),
      jsonResponse(environmentContractResponse()),
      jsonResponse(tenantLifecycleResponse('tenant-acme')),
      jsonResponse({
        id: 'tenant-beta',
        name: 'Beta Retail',
        slug: 'beta-retail',
        status: 'ACTIVE',
        onboarding_status: 'OWNER_INVITE_PENDING',
      }),
      jsonResponse({
        records: [
          {
            tenant_id: 'tenant-beta',
            name: 'Beta Retail',
            slug: 'beta-retail',
            status: 'ACTIVE',
            onboarding_status: 'OWNER_INVITE_PENDING',
          },
          {
            tenant_id: 'tenant-acme',
            name: 'Acme Retail',
            slug: 'acme-retail',
            status: 'ACTIVE',
            onboarding_status: 'OWNER_INVITE_PENDING',
          },
        ],
      }),
      jsonResponse(tenantLifecycleResponse('tenant-beta')),
      jsonResponse({
        id: 'invite-1',
        tenant_id: 'tenant-beta',
        email: 'owner@beta.local',
        full_name: 'Beta Owner',
        status: 'PENDING',
      }),
    ]);

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=platform-1;email=admin@store.local;name=Platform Admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start control plane session' }));

    expect(await screen.findByText('Env: staging')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Tenants' }));
    expect(await screen.findByText('Tenant lifecycle')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Tenant name'), { target: { value: 'Beta Retail' } });
    fireEvent.change(screen.getByLabelText('Tenant slug'), { target: { value: 'beta-retail' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create tenant' }));

    expect(await screen.findByText('Beta Retail')).toBeInTheDocument();
    expect(screen.getByText('Target tenant: tenant-beta')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Owner email'), { target: { value: 'owner@beta.local' } });
    fireEvent.change(screen.getByLabelText('Owner full name'), { target: { value: 'Beta Owner' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send owner invite' }));

    await waitFor(() => {
      expect(screen.getByText('owner@beta.local')).toBeInTheDocument();
      expect(screen.getByText('PENDING')).toBeInTheDocument();
    });
  });

  test('creates a billing plan and suspends the selected tenant through the new IA', async () => {
    mockResponses([
      jsonResponse({ access_token: 'session-platform', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-platform',
        email: 'admin@store.local',
        full_name: 'Platform Admin',
        is_platform_admin: true,
        tenant_memberships: [],
        branch_memberships: [],
      }),
      jsonResponse({
        records: [
          {
            tenant_id: 'tenant-acme',
            name: 'Acme Retail',
            slug: 'acme-retail',
            status: 'ACTIVE',
            onboarding_status: 'OWNER_INVITE_PENDING',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'plan-launch',
            code: 'launch-starter',
            display_name: 'Launch Starter',
            billing_cadence: 'monthly',
            currency_code: 'INR',
            amount_minor: 149900,
            trial_days: 14,
            branch_limit: 2,
            device_limit: 4,
            offline_runtime_hours: 48,
            grace_window_days: 5,
            feature_flags: { offline_continuity: true },
            provider_plan_refs: { cashfree: 'cf_plan_launch_starter', razorpay: 'rp_plan_launch_starter' },
            is_default: true,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse(observabilitySummaryResponse()),
      jsonResponse(securityControlsResponse()),
      jsonResponse(environmentContractResponse()),
      jsonResponse(tenantLifecycleResponse('tenant-acme')),
      jsonResponse({
        id: 'plan-scale',
        code: 'scale-growth',
        display_name: 'Scale Growth',
        billing_cadence: 'monthly',
        currency_code: 'INR',
        amount_minor: 349900,
        trial_days: 14,
        branch_limit: 8,
        device_limit: 20,
        offline_runtime_hours: 72,
        grace_window_days: 7,
        feature_flags: { offline_continuity: true },
        provider_plan_refs: { cashfree: 'cf_plan_scale_growth', razorpay: 'rp_plan_scale_growth' },
        is_default: false,
        status: 'ACTIVE',
      }),
      jsonResponse({
        records: [
          {
            id: 'plan-launch',
            code: 'launch-starter',
            display_name: 'Launch Starter',
            billing_cadence: 'monthly',
            currency_code: 'INR',
            amount_minor: 149900,
            trial_days: 14,
            branch_limit: 2,
            device_limit: 4,
            offline_runtime_hours: 48,
            grace_window_days: 5,
            feature_flags: { offline_continuity: true },
            provider_plan_refs: { cashfree: 'cf_plan_launch_starter', razorpay: 'rp_plan_launch_starter' },
            is_default: true,
            status: 'ACTIVE',
          },
          {
            id: 'plan-scale',
            code: 'scale-growth',
            display_name: 'Scale Growth',
            billing_cadence: 'monthly',
            currency_code: 'INR',
            amount_minor: 349900,
            trial_days: 14,
            branch_limit: 8,
            device_limit: 20,
            offline_runtime_hours: 72,
            grace_window_days: 7,
            feature_flags: { offline_continuity: true },
            provider_plan_refs: { cashfree: 'cf_plan_scale_growth', razorpay: 'rp_plan_scale_growth' },
            is_default: false,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse(tenantLifecycleResponse('tenant-acme', 'SUSPENDED')),
    ]);

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=platform-1;email=admin@store.local;name=Platform Admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start control plane session' }));

    expect(await screen.findByText('Env: staging')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Commercial' }));
    expect(await screen.findByText('Billing plan catalog')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Plan code'), { target: { value: 'scale-growth' } });
    fireEvent.change(screen.getByLabelText('Plan name'), { target: { value: 'Scale Growth' } });
    fireEvent.change(screen.getByLabelText('Plan monthly amount (minor units)'), { target: { value: '349900' } });
    fireEvent.change(screen.getByLabelText('Plan branch limit'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Plan device limit'), { target: { value: '20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create billing plan' }));

    expect(await screen.findByText('Scale Growth')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Tenants' }));
    expect(await screen.findByText('Owner binding and entitlement')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Suspend tenant access' }));

    await waitFor(() => {
      expect(screen.getByText('SUSPENDED')).toBeInTheDocument();
    });
  });

  test('shows the control-tower overview after session bootstrap', async () => {
    mockResponses([
      jsonResponse({ access_token: 'session-platform', token_type: 'Bearer' }),
      jsonResponse({
        user_id: 'user-platform',
        email: 'admin@store.local',
        full_name: 'Platform Admin',
        is_platform_admin: true,
        tenant_memberships: [],
        branch_memberships: [],
      }),
      jsonResponse({
        records: [
          {
            tenant_id: 'tenant-acme',
            name: 'Acme Retail',
            slug: 'acme-retail',
            status: 'ACTIVE',
            onboarding_status: 'OWNER_INVITE_PENDING',
          },
        ],
      }),
      jsonResponse({
        records: [
          {
            id: 'plan-launch',
            code: 'launch-starter',
            display_name: 'Launch Starter',
            billing_cadence: 'monthly',
            currency_code: 'INR',
            amount_minor: 149900,
            trial_days: 14,
            branch_limit: 2,
            device_limit: 4,
            offline_runtime_hours: 48,
            grace_window_days: 5,
            feature_flags: { offline_continuity: true },
            provider_plan_refs: { cashfree: 'cf_plan_launch_starter', razorpay: 'rp_plan_launch_starter' },
            is_default: true,
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse(observabilitySummaryResponse()),
      jsonResponse(securityControlsResponse()),
      jsonResponse(environmentContractResponse()),
      jsonResponse(tenantLifecycleResponse('tenant-acme')),
    ]);

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=platform-1;email=admin@store.local;name=Platform Admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start control plane session' }));

    expect(await screen.findByText('Critical exceptions')).toBeInTheDocument();
    expect(screen.getByText('Dead-letter operations jobs')).toBeInTheDocument();
    expect(screen.getByText('Release evidence')).toBeInTheDocument();
    expect(screen.getByText('https://control.staging.store.korsenex.com')).toBeInTheDocument();
  });
});
