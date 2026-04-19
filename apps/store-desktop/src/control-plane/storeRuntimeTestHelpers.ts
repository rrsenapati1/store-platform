import { vi } from 'vitest';

type MockResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

export function jsonResponse(body: unknown, status = 200): MockResponse {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

export function installRuntimeBootstrapFetchMock(args?: {
  branchRoleNames?: string[];
  tenantRoleNames?: string[];
}) {
  const branchRoleNames = args?.branchRoleNames ?? ['cashier'];
  const tenantRoleNames = args?.tenantRoleNames ?? [];

  const responses = [
    jsonResponse({ access_token: 'session-cashier', token_type: 'Bearer' }),
    jsonResponse({
      user_id: 'user-cashier',
      email: 'cashier@acme.local',
      full_name: 'Counter Cashier',
      is_platform_admin: false,
      tenant_memberships: tenantRoleNames.map((roleName) => ({ tenant_id: 'tenant-acme', role_name: roleName, status: 'ACTIVE' })),
      branch_memberships: branchRoleNames.map((roleName) => ({
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        role_name: roleName,
        status: 'ACTIVE',
      })),
    }),
    jsonResponse({
      id: 'tenant-acme',
      name: 'Acme Retail',
      slug: 'acme-retail',
      status: 'ACTIVE',
      onboarding_status: 'BRANCH_READY',
    }),
    jsonResponse({
      records: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', code: 'blr-flagship', status: 'ACTIVE' }],
    }),
    jsonResponse({
      records: [
        {
          id: 'catalog-item-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          barcode: '8901234567890',
          hsn_sac_code: '0902',
          gst_rate: 5,
          base_selling_price: 92.5,
          selling_price_override: null,
          effective_selling_price: 92.5,
          availability_status: 'ACTIVE',
        },
      ],
    }),
    jsonResponse({
      records: [
        {
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          stock_on_hand: 24,
          last_entry_type: 'PURCHASE_RECEIPT',
        },
      ],
    }),
    jsonResponse({ records: [] }),
    jsonResponse({
      records: [
        {
          id: 'device-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_name: 'Counter Desktop 1',
          device_code: 'counter-1',
          session_surface: 'store_desktop',
          status: 'ACTIVE',
          assigned_staff_profile_id: null,
          assigned_staff_full_name: null,
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
}
