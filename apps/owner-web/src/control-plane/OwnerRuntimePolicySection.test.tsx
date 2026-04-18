/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerRuntimePolicySection } from './OwnerRuntimePolicySection';

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

describe('owner runtime policy section', () => {
  const originalFetch = globalThis.fetch;
  let runtimePolicy = {
    id: 'runtime-policy-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    require_shift_for_attendance: true,
    require_attendance_for_cashier: true,
    require_assigned_staff_for_device: true,
    allow_offline_sales: true,
    max_pending_offline_sales: 25,
    updated_by_user_id: 'owner-user-1',
  };

  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (url.endsWith('/runtime-policy') && method === 'GET') {
        return jsonResponse(runtimePolicy) as never;
      }
      if (url.endsWith('/runtime-policy') && method === 'PUT') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        runtimePolicy = {
          ...runtimePolicy,
          ...payload,
        };
        return jsonResponse(runtimePolicy) as never;
      }

      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    cleanup();
    vi.restoreAllMocks();
  });

  test('loads and saves the branch runtime policy', async () => {
    render(
      <OwnerRuntimePolicySection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    expect(await screen.findByText('Runtime controls')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reload policy' }));
    await waitFor(() => {
      expect(screen.getByLabelText('Require an open shift before attendance')).toBeChecked();
    });

    fireEvent.click(screen.getByLabelText('Allow offline sales continuity'));
    fireEvent.change(screen.getByLabelText('Max pending offline sales'), {
      target: { value: '10' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save runtime policy' }));

    await waitFor(() => {
      const saveCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) => String(url).includes('/runtime-policy') && init?.method === 'PUT',
      );
      expect(saveCall).toBeDefined();
      expect(JSON.parse(String(saveCall?.[1]?.body ?? '{}'))).toMatchObject({
        allow_offline_sales: false,
        max_pending_offline_sales: 10,
      });
    });

    expect(await screen.findByText('BLOCKED')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });
});
