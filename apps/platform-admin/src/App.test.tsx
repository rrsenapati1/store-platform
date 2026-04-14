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

describe('platform admin onboarding flow', () => {
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
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('exchanges session, loads tenants, creates a tenant, and sends an owner invite', async () => {
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
      jsonResponse({
        tenant_id: 'tenant-acme',
        subscription: {
          id: 'sub-acme',
          tenant_id: 'tenant-acme',
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
          id: 'ent-acme',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          active_plan_code: 'launch-starter',
          lifecycle_status: 'TRIALING',
          branch_limit: 2,
          device_limit: 4,
          offline_runtime_hours: 48,
          grace_until: null,
          suspend_at: '2026-05-03T00:00:00',
          feature_flags: { offline_continuity: true },
          policy_source: 'subscription',
          policy_metadata: { reason: 'trial_issued' },
        },
        active_override: null,
      }),
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
      jsonResponse({
        tenant_id: 'tenant-beta',
        subscription: {
          id: 'sub-beta',
          tenant_id: 'tenant-beta',
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
          id: 'ent-beta',
          tenant_id: 'tenant-beta',
          billing_plan_id: 'plan-launch',
          active_plan_code: 'launch-starter',
          lifecycle_status: 'TRIALING',
          branch_limit: 2,
          device_limit: 4,
          offline_runtime_hours: 48,
          grace_until: null,
          suspend_at: '2026-05-03T00:00:00',
          feature_flags: { offline_continuity: true },
          policy_source: 'subscription',
          policy_metadata: { reason: 'trial_issued' },
        },
        active_override: null,
      }),
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

    expect(await screen.findByText('Platform Admin')).toBeInTheDocument();
    expect(await screen.findByText('Acme Retail')).toBeInTheDocument();
    expect(await screen.findByText('Launch Starter')).toBeInTheDocument();
    expect((await screen.findAllByText('TRIALING')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Tenant name'), { target: { value: 'Beta Retail' } });
    fireEvent.change(screen.getByLabelText('Tenant slug'), { target: { value: 'beta-retail' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create tenant' }));

    expect(await screen.findByText('Beta Retail')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Owner email'), { target: { value: 'owner@beta.local' } });
    fireEvent.change(screen.getByLabelText('Owner full name'), { target: { value: 'Beta Owner' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send owner invite' }));

    await waitFor(() => {
      expect(screen.getByText('Latest owner invite')).toBeInTheDocument();
      expect(screen.getByText('owner@beta.local')).toBeInTheDocument();
      expect(screen.getByText('PENDING')).toBeInTheDocument();
    });
  });

  test('shows billing plans and lets platform admin suspend the selected tenant', async () => {
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
      jsonResponse({
        tenant_id: 'tenant-acme',
        subscription: {
          id: 'sub-acme',
          tenant_id: 'tenant-acme',
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
          id: 'ent-acme',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          active_plan_code: 'launch-starter',
          lifecycle_status: 'TRIALING',
          branch_limit: 2,
          device_limit: 4,
          offline_runtime_hours: 48,
          grace_until: null,
          suspend_at: '2026-05-03T00:00:00',
          feature_flags: { offline_continuity: true },
          policy_source: 'subscription',
          policy_metadata: { reason: 'trial_issued' },
        },
        active_override: null,
      }),
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
      jsonResponse({
        tenant_id: 'tenant-acme',
        subscription: {
          id: 'sub-acme',
          tenant_id: 'tenant-acme',
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
          id: 'ent-acme',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          active_plan_code: 'launch-starter',
          lifecycle_status: 'SUSPENDED',
          branch_limit: 2,
          device_limit: 4,
          offline_runtime_hours: 48,
          grace_until: null,
          suspend_at: '2026-05-03T00:00:00',
          feature_flags: { offline_continuity: true },
          policy_source: 'tenant_status',
          policy_metadata: { reason: 'Billing review hold' },
        },
        active_override: null,
      }),
    ]);

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=platform-1;email=admin@store.local;name=Platform Admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start control plane session' }));

    expect(await screen.findByText('Launch Starter')).toBeInTheDocument();
    expect((await screen.findAllByText('TRIALING')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Plan code'), { target: { value: 'scale-growth' } });
    fireEvent.change(screen.getByLabelText('Plan name'), { target: { value: 'Scale Growth' } });
    fireEvent.change(screen.getByLabelText('Plan monthly amount (minor units)'), { target: { value: '349900' } });
    fireEvent.change(screen.getByLabelText('Plan branch limit'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Plan device limit'), { target: { value: '20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create billing plan' }));

    expect(await screen.findByText('Scale Growth')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Suspend tenant access' }));

    await waitFor(() => {
      expect(screen.getByText('SUSPENDED')).toBeInTheDocument();
    });
  });
});
