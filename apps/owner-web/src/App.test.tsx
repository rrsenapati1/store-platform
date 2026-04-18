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

describe('owner onboarding flow', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    const responses = [
      jsonResponse({ access_token: 'session-owner', token_type: 'Bearer' }),
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
        onboarding_status: 'OWNER_INVITE_PENDING',
      }),
      jsonResponse({ records: [] }),
      jsonResponse({
        records: [
          {
            id: 'audit-1',
            action: 'owner_invite.accepted',
            entity_type: 'owner_invite',
            entity_id: 'invite-1',
            tenant_id: 'tenant-acme',
            branch_id: null,
            created_at: '2026-04-13T08:00:00',
            payload: { email: 'owner@acme.local' },
          },
        ],
      }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({ records: [] }),
      jsonResponse({
        id: 'branch-1',
        tenant_id: 'tenant-acme',
        name: 'Bengaluru Flagship',
        code: 'blr-flagship',
        gstin: '29ABCDE1234F1Z5',
        timezone: 'Asia/Kolkata',
        status: 'ACTIVE',
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
      jsonResponse({
        id: 'staff-profile-1',
        tenant_id: 'tenant-acme',
        user_id: null,
        email: 'cashier@acme.local',
        full_name: 'Cash Counter One',
        phone_number: '9876543210',
        primary_branch_id: 'branch-1',
        status: 'ACTIVE',
      }),
      jsonResponse({
        records: [
          {
            id: 'staff-profile-1',
            tenant_id: 'tenant-acme',
            user_id: null,
            email: 'cashier@acme.local',
            full_name: 'Cash Counter One',
            phone_number: '9876543210',
            primary_branch_id: 'branch-1',
            status: 'ACTIVE',
            role_names: [],
            branch_ids: [],
          },
        ],
      }),
      jsonResponse({
        id: 'tenant-membership-1',
        tenant_id: 'tenant-acme',
        email: 'ops@acme.local',
        full_name: 'Operations Lead',
        role_name: 'inventory_admin',
        status: 'PENDING',
      }),
      jsonResponse({
        records: [
          {
            id: 'staff-profile-1',
            tenant_id: 'tenant-acme',
            user_id: null,
            email: 'cashier@acme.local',
            full_name: 'Cash Counter One',
            phone_number: '9876543210',
            primary_branch_id: 'branch-1',
            status: 'ACTIVE',
            role_names: [],
            branch_ids: [],
          },
          {
            id: 'staff-profile-2',
            tenant_id: 'tenant-acme',
            user_id: null,
            email: 'ops@acme.local',
            full_name: 'Operations Lead',
            phone_number: null,
            primary_branch_id: null,
            status: 'ACTIVE',
            role_names: ['inventory_admin'],
            branch_ids: [],
          },
        ],
      }),
      jsonResponse({
        id: 'branch-membership-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        email: 'cashier@acme.local',
        full_name: 'Cash Counter One',
        role_name: 'cashier',
        status: 'PENDING',
      }),
      jsonResponse({
        records: [
          {
            id: 'staff-profile-1',
            tenant_id: 'tenant-acme',
            user_id: null,
            email: 'cashier@acme.local',
            full_name: 'Cash Counter One',
            phone_number: '9876543210',
            primary_branch_id: 'branch-1',
            status: 'ACTIVE',
            role_names: ['cashier'],
            branch_ids: ['branch-1'],
          },
          {
            id: 'staff-profile-2',
            tenant_id: 'tenant-acme',
            user_id: null,
            email: 'ops@acme.local',
            full_name: 'Operations Lead',
            phone_number: null,
            primary_branch_id: null,
            status: 'ACTIVE',
            role_names: ['inventory_admin'],
            branch_ids: [],
          },
        ],
      }),
      jsonResponse({
        id: 'device-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_name: 'Counter Desktop 1',
        device_code: 'BLR-POS-01',
        session_surface: 'store_desktop',
        status: 'ACTIVE',
        assigned_staff_profile_id: 'staff-profile-1',
      }),
      jsonResponse({
        records: [
          {
            id: 'device-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_name: 'Counter Desktop 1',
            device_code: 'BLR-POS-01',
            session_surface: 'store_desktop',
            status: 'ACTIVE',
            assigned_staff_profile_id: 'staff-profile-1',
            assigned_staff_full_name: 'Cash Counter One',
          },
        ],
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

  test('loads owner onboarding state and bootstraps staff and branch devices', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(await screen.findByText('Acme Owner', {}, { timeout: 10_000 })).toBeInTheDocument();
    expect((await screen.findAllByText('Acme Retail')).length).toBeGreaterThan(0);
    expect(await screen.findByText('owner_invite.accepted')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Branch name'), { target: { value: 'Bengaluru Flagship' } });
    fireEvent.change(screen.getByLabelText('Branch code'), { target: { value: 'blr-flagship' } });
    fireEvent.change(screen.getByLabelText('Branch GSTIN'), { target: { value: '29ABCDE1234F1Z5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create first branch' }));

    expect(await screen.findByText('Bengaluru Flagship')).toBeInTheDocument();
    expect((await screen.findAllByText('BRANCH_READY')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Staff profile email'), { target: { value: 'cashier@acme.local' } });
    fireEvent.change(screen.getByLabelText('Staff profile full name'), { target: { value: 'Cash Counter One' } });
    fireEvent.change(screen.getByLabelText('Staff profile phone'), { target: { value: '9876543210' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create staff profile' }));

    expect(await screen.findByText('Latest staff profile')).toBeInTheDocument();
    expect((await screen.findAllByText('Cash Counter One')).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText('Tenant staff email'), { target: { value: 'ops@acme.local' } });
    fireEvent.change(screen.getByLabelText('Tenant staff full name'), { target: { value: 'Operations Lead' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign tenant role' }));

    expect(await screen.findByText('Latest tenant membership')).toBeInTheDocument();
    expect(screen.getByText('ops@acme.local')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Branch staff email'), { target: { value: 'cashier@acme.local' } });
    fireEvent.change(screen.getByLabelText('Branch staff full name'), { target: { value: 'Cash Counter One' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign branch role' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch membership')).toBeInTheDocument();
      expect(screen.getAllByText('cashier@acme.local').length).toBeGreaterThan(0);
    });

    fireEvent.change(screen.getByLabelText('Device name'), { target: { value: 'Counter Desktop 1' } });
    fireEvent.change(screen.getByLabelText('Device code'), { target: { value: 'BLR-POS-01' } });
    fireEvent.click(screen.getByRole('button', { name: 'Register branch device' }));

    await waitFor(() => {
      expect(screen.getByText('Latest branch device')).toBeInTheDocument();
      expect(screen.getByText('Counter Desktop 1 -> Cash Counter One')).toBeInTheDocument();
    });

    expect(screen.getByText('Catalog barcode operations')).toBeInTheDocument();
    expect(screen.getByText('Batch expiry and lot control')).toBeInTheDocument();
    expect(screen.getByText('IRP submission queue')).toBeInTheDocument();
    expect(screen.getByText('Customer insights')).toBeInTheDocument();
  });
});
