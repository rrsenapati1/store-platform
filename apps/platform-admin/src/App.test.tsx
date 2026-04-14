/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

  beforeEach(() => {
    const responses = [
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
        id: 'invite-1',
        tenant_id: 'tenant-beta',
        email: 'owner@beta.local',
        full_name: 'Beta Owner',
        status: 'PENDING',
      }),
    ];

    globalThis.fetch = vi.fn(async () => {
      const next = responses.shift();
      if (!next) {
        throw new Error('Unexpected fetch call');
      }
      return next as never;
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('exchanges session, loads tenants, creates a tenant, and sends an owner invite', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=platform-1;email=admin@store.local;name=Platform Admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start control plane session' }));

    expect(await screen.findByText('Platform Admin')).toBeInTheDocument();
    expect(await screen.findByText('Acme Retail')).toBeInTheDocument();

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
});
