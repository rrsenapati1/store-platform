/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { OwnerCustomerInsightsSection } from './OwnerCustomerInsightsSection';

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

describe('owner customer insights section', () => {
  const originalFetch = globalThis.fetch;
  let profileStatus: 'ACTIVE' | 'ARCHIVED';
  let profileName: string;

  beforeEach(() => {
    profileStatus = 'ACTIVE';
    profileName = 'Acme Traders';

    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      if (url.endsWith('/customer-profiles') && method === 'GET') {
        return jsonResponse({
          records: [
            {
              id: 'profile-1',
              tenant_id: 'tenant-acme',
              full_name: profileName,
              phone: '+919999999999',
              email: 'accounts@acme.example',
              gstin: '29AAEPM0111C1Z3',
              default_note: 'Preferred wholesale buyer',
              tags: ['wholesale', 'priority'],
              status: profileStatus,
              created_at: '2026-04-16T09:00:00Z',
              updated_at: '2026-04-16T09:00:00Z',
            },
          ],
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1') && method === 'GET') {
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: '+919999999999',
          email: 'accounts@acme.example',
          gstin: '29AAEPM0111C1Z3',
          default_note: 'Preferred wholesale buyer',
          tags: ['wholesale', 'priority'],
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:00:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1') && method === 'PATCH') {
        const payload = JSON.parse(String(init?.body ?? '{}'));
        profileName = payload.full_name ?? profileName;
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: payload.phone ?? '+919999999999',
          email: payload.email ?? 'accounts@acme.example',
          gstin: payload.gstin ?? '29AAEPM0111C1Z3',
          default_note: payload.default_note ?? 'Preferred wholesale buyer',
          tags: payload.tags ?? ['wholesale', 'priority'],
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:05:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/archive') && method === 'POST') {
        profileStatus = 'ARCHIVED';
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: '+919999999999',
          email: 'accounts@acme.example',
          gstin: '29AAEPM0111C1Z3',
          default_note: 'Preferred wholesale buyer',
          tags: ['wholesale', 'priority'],
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:10:00Z',
        }) as never;
      }
      if (url.endsWith('/customer-profiles/profile-1/reactivate') && method === 'POST') {
        profileStatus = 'ACTIVE';
        return jsonResponse({
          id: 'profile-1',
          tenant_id: 'tenant-acme',
          full_name: profileName,
          phone: '+919999999999',
          email: 'accounts@acme.example',
          gstin: '29AAEPM0111C1Z3',
          default_note: 'Preferred wholesale buyer',
          tags: ['wholesale', 'priority'],
          status: profileStatus,
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-16T09:15:00Z',
        }) as never;
      }
      if (url.includes('/customers') && !url.includes('/history')) {
        return jsonResponse({
          records: [
            {
              customer_id: 'profile-1',
              customer_profile_id: 'profile-1',
              name: profileName,
              phone: '+919999999999',
              email: 'accounts@acme.example',
              gstin: '29AAEPM0111C1Z3',
              visit_count: 2,
              lifetime_value: 582.75,
              last_sale_id: 'sale-2',
              last_invoice_number: 'SINV-BLRFLAGSHIP-0002',
              last_branch_id: 'branch-1',
            },
          ],
        }) as never;
      }
      if (url.includes('/customer-report')) {
        return jsonResponse({
          branch_id: 'branch-1',
          customer_count: 1,
          repeat_customer_count: 1,
          anonymous_sales_count: 1,
          anonymous_sales_total: 97.12,
          top_customers: [
            {
              customer_id: 'profile-1',
              customer_profile_id: 'profile-1',
              customer_name: profileName,
              sales_count: 2,
              sales_total: 582.75,
              last_invoice_number: 'SINV-BLRFLAGSHIP-0002',
            },
          ],
          return_activity: [
            {
              customer_id: 'profile-1',
              customer_profile_id: 'profile-1',
              customer_name: profileName,
              return_count: 1,
              credit_note_total: 97.12,
              exchange_count: 1,
            },
          ],
        }) as never;
      }
      if (url.includes('/customers/profile-1/history')) {
        return jsonResponse({
          customer: {
            customer_id: 'profile-1',
            customer_profile_id: 'profile-1',
            name: profileName,
            phone: '+919999999999',
            email: 'accounts@acme.example',
            gstin: '29AAEPM0111C1Z3',
            visit_count: 2,
            lifetime_value: 582.75,
            last_sale_id: 'sale-2',
          },
          sales_summary: {
            sales_count: 2,
            sales_total: 582.75,
            return_count: 1,
            credit_note_total: 97.12,
            exchange_count: 1,
          },
          sales: [
            {
              sale_id: 'sale-1',
              branch_id: 'branch-1',
              invoice_id: 'invoice-1',
              invoice_number: 'SINV-BLRFLAGSHIP-0001',
              grand_total: 291.38,
              payment_method: 'Cash',
            },
            {
              sale_id: 'sale-2',
              branch_id: 'branch-1',
              invoice_id: 'invoice-2',
              invoice_number: 'SINV-BLRFLAGSHIP-0002',
              grand_total: 291.37,
              payment_method: 'MIXED',
            },
          ],
          returns: [],
          exchanges: [],
        }) as never;
      }
      throw new Error(`Unexpected fetch call: ${method} ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads customer profiles alongside reporting and selected history', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    expect(await screen.findByRole('button', { name: /Acme Traders \(29AAEPM0111C1Z3\) ACTIVE/ })).toBeInTheDocument();
    expect(screen.getByText('Repeat customers')).toBeInTheDocument();
    expect(screen.getByText('Sales history')).toBeInTheDocument();
    expect(screen.getByLabelText('Customer profile search')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Acme Traders')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+919999999999')).toBeInTheDocument();
    expect(screen.getByDisplayValue('accounts@acme.example')).toBeInTheDocument();
    expect(screen.getByDisplayValue('wholesale, priority')).toBeInTheDocument();
  });

  test('updates and archives or reactivates the selected customer profile', async () => {
    render(
      <OwnerCustomerInsightsSection
        accessToken="session-owner"
        tenantId="tenant-acme"
        branchId="branch-1"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Load customer insights' }));

    const nameField = await screen.findByLabelText('Profile full name');
    fireEvent.change(nameField, { target: { value: 'Acme Traders LLP' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save customer profile' }));

    await waitFor(() => {
      const updateCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([url, init]) =>
          String(url).includes('/v1/tenants/tenant-acme/customer-profiles/profile-1') &&
          init?.method === 'PATCH',
      );
      expect(updateCall).toBeDefined();
      expect(JSON.parse(String(updateCall?.[1]?.body ?? '{}')).full_name).toBe('Acme Traders LLP');
    });

    fireEvent.click(screen.getByRole('button', { name: 'Archive customer profile' }));
    expect(await screen.findByText('ARCHIVED')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reactivate customer profile' }));
    expect(await screen.findByText('ACTIVE')).toBeInTheDocument();
  });
});
