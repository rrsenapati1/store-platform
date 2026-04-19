/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';

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

describe('owner billing lifecycle section', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads tenant billing posture and starts recurring subscription recovery', async () => {
    const responses = [
      jsonResponse({ access_token: 'session-owner', token_type: 'Bearer', expires_at: '2026-04-14T11:00:00Z' }),
      jsonResponse({
        user_id: 'user-owner',
        email: 'owner@acme.local',
        full_name: 'Acme Owner',
        is_platform_admin: false,
        tenant_memberships: [{ tenant_id: 'tenant-acme', role_name: 'tenant_owner', status: 'ACTIVE' }],
        branch_memberships: [],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'ACTIVE',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({
        records: [
          {
            branch_id: 'branch-1',
            tenant_id: 'tenant-acme',
            name: 'Bengaluru Flagship',
            code: 'blr-flagship',
            status: 'ACTIVE',
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        tenant_id: 'tenant-acme',
        subscription: {
          id: 'sub-1',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          provider_name: null,
          provider_customer_id: null,
          provider_subscription_id: null,
          lifecycle_status: 'TRIALING',
          mandate_status: null,
          trial_started_at: '2026-04-14T00:00:00Z',
          trial_ends_at: '2026-04-28T00:00:00Z',
          current_period_started_at: null,
          current_period_ends_at: null,
          grace_until: null,
          canceled_at: null,
        },
        entitlement: {
          id: 'ent-1',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          active_plan_code: 'launch-starter',
          lifecycle_status: 'TRIALING',
          branch_limit: 2,
          device_limit: 4,
          offline_runtime_hours: 48,
          grace_until: null,
          suspend_at: '2026-05-03T00:00:00Z',
          feature_flags: { offline_continuity: true, desktop_runtime: true },
          policy_source: 'subscription',
          policy_metadata: { reason: 'trial_issued' },
        },
        active_override: null,
      }),
      jsonResponse({
        provider_name: 'cashfree',
        provider_customer_id: 'cf_customer_tenant-acme',
        provider_subscription_id: 'cf_subscription_launch-starter',
        checkout_url: 'https://payments.cashfree.test/tenant-acme/launch-starter',
        mandate_status: 'PENDING_SETUP',
      }),
    ];

    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Commercial' }));

    fireEvent.click(screen.getByRole('button', { name: 'Load billing status' }));

    expect(await screen.findByText('Launch Starter')).toBeInTheDocument();
    expect(screen.getAllByText('TRIALING').length).toBeGreaterThan(0);
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Recurring provider'), { target: { value: 'cashfree' } });
    fireEvent.click(screen.getByRole('button', { name: 'Start recurring subscription' }));

    expect(await screen.findByText('Latest checkout session')).toBeInTheDocument();
    expect(screen.getAllByText('cashfree').length).toBeGreaterThan(0);
    expect(screen.getAllByText('PENDING_SETUP').length).toBeGreaterThan(0);
    expect(screen.getByText('https://payments.cashfree.test/tenant-acme/launch-starter')).toBeInTheDocument();
  });

  test('shows grace and suspension posture with billing recovery guidance', async () => {
    const responses = [
      jsonResponse({ access_token: 'session-owner', token_type: 'Bearer', expires_at: '2026-04-14T11:00:00Z' }),
      jsonResponse({
        user_id: 'user-owner',
        email: 'owner@acme.local',
        full_name: 'Acme Owner',
        is_platform_admin: false,
        tenant_memberships: [{ tenant_id: 'tenant-acme', role_name: 'tenant_owner', status: 'ACTIVE' }],
        branch_memberships: [],
      }),
      jsonResponse({
        id: 'tenant-acme',
        name: 'Acme Retail',
        slug: 'acme-retail',
        status: 'SUSPENDED',
        onboarding_status: 'BRANCH_READY',
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        tenant_id: 'tenant-acme',
        subscription: {
          id: 'sub-1',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          provider_name: 'razorpay',
          provider_customer_id: 'rp_customer_tenant-acme',
          provider_subscription_id: 'rp_subscription_launch-starter',
          lifecycle_status: 'GRACE',
          mandate_status: 'PAYMENT_RETRY_PENDING',
          trial_started_at: '2026-03-01T00:00:00Z',
          trial_ends_at: '2026-03-15T00:00:00Z',
          current_period_started_at: '2026-03-15T00:00:00Z',
          current_period_ends_at: '2026-04-14T00:00:00Z',
          grace_until: '2026-04-19T00:00:00Z',
          canceled_at: null,
        },
        entitlement: {
          id: 'ent-1',
          tenant_id: 'tenant-acme',
          billing_plan_id: 'plan-launch',
          active_plan_code: 'launch-starter',
          lifecycle_status: 'SUSPENDED',
          branch_limit: 2,
          device_limit: 4,
          offline_runtime_hours: 48,
          grace_until: '2026-04-19T00:00:00Z',
          suspend_at: '2026-04-19T00:00:00Z',
          feature_flags: { offline_continuity: true, desktop_runtime: true },
          policy_source: 'subscription',
          policy_metadata: { subscription_status: 'GRACE' },
        },
        active_override: null,
      }),
    ];

    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));
    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Commercial' }));

    fireEvent.click(screen.getByRole('button', { name: 'Load billing status' }));

    expect(await screen.findByText(/Commercial access suspended/)).toBeInTheDocument();
    expect(screen.getByText(/Renew the subscription mandate or complete a recovery payment/)).toBeInTheDocument();
    expect(screen.getAllByText('SUSPENDED').length).toBeGreaterThan(0);
    expect(screen.getByText('PAYMENT_RETRY_PENDING')).toBeInTheDocument();
    expect(screen.getByText('2026-04-19T00:00:00Z')).toBeInTheDocument();
  });
});
