/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerDeviceClaimSection } from './OwnerDeviceClaimSection';

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

describe('owner device claim section', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({
        records: [
          {
            id: 'claim-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            claim_code: 'STORE-1234ABCD',
            runtime_kind: 'packaged_desktop',
            hostname: 'COUNTER-01',
            operating_system: 'windows',
            architecture: 'x86_64',
            app_version: '0.1.0',
            status: 'PENDING',
            approved_device_id: null,
            approved_device_code: null,
            created_at: '2026-04-14T07:00:00',
            last_seen_at: '2026-04-14T07:05:00',
          },
        ],
      }),
      jsonResponse({
        claim: {
          id: 'claim-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          claim_code: 'STORE-1234ABCD',
          runtime_kind: 'packaged_desktop',
          hostname: 'COUNTER-01',
          operating_system: 'windows',
          architecture: 'x86_64',
          app_version: '0.1.0',
          status: 'APPROVED',
          approved_device_id: 'device-1',
          approved_device_code: 'BLR-POS-01',
          created_at: '2026-04-14T07:00:00',
          last_seen_at: '2026-04-14T07:05:00',
        },
        device: {
          id: 'device-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_name: 'Counter Desktop 1',
          device_code: 'BLR-POS-01',
          session_surface: 'store_desktop',
          is_branch_hub: true,
          status: 'ACTIVE',
          assigned_staff_profile_id: 'staff-1',
          sync_access_secret: 'hub-secret-1',
        },
      }),
      jsonResponse({
        device_id: 'device-1',
        staff_profile_id: 'staff-1',
        activation_code: 'ACTV-1234-5678',
        status: 'ISSUED',
        expires_at: '2026-04-14T07:30:00',
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

  test('loads a pending packaged-runtime claim, approves it into a branch device, and issues a desktop activation', async () => {
    const onApproved = vi.fn();

    render(
      <OwnerDeviceClaimSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
        onApproved={onApproved}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load device claims' }));

    expect(await screen.findByText('STORE-1234ABCD')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Approved device name'), { target: { value: 'Counter Desktop 1' } });
    fireEvent.change(screen.getByLabelText('Approved device code'), { target: { value: 'BLR-POS-01' } });
    fireEvent.click(screen.getByLabelText('Designate as branch hub'));
    fireEvent.click(screen.getByRole('button', { name: 'Approve selected claim' }));

    expect(await screen.findByText('Approved runtime device')).toBeInTheDocument();
    expect(screen.getByText('BLR-POS-01')).toBeInTheDocument();
    expect(screen.getByText('Branch hub')).toBeInTheDocument();
    expect(screen.getByText('hub-secret-1')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Issue desktop activation' }));
    expect(await screen.findByText('ACTV-1234-5678')).toBeInTheDocument();
    expect(onApproved).toHaveBeenCalledTimes(1);
  });
});
