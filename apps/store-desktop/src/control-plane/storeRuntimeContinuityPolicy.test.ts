import { describe, expect, test } from 'vitest';
import type { ControlPlaneBranchCatalogItem, ControlPlaneInventorySnapshotRecord } from '@store/types';
import { isOfflineSaleContinuityReady, prepareOfflineSaleContinuityDraft } from './storeRuntimeContinuityPolicy';

function buildCatalogItems(): ControlPlaneBranchCatalogItem[] {
  return [
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
      mrp: 120,
      category_code: 'TEA',
      base_selling_price: 92.5,
      selling_price_override: null,
      effective_selling_price: 92.5,
      availability_status: 'ACTIVE',
    },
  ];
}

function buildInventorySnapshot(): ControlPlaneInventorySnapshotRecord[] {
  return [
    {
      product_id: 'product-1',
      product_name: 'Classic Tea',
      sku_code: 'tea-classic-250g',
      stock_on_hand: 24,
      last_entry_type: 'PURCHASE_RECEIPT',
    },
  ];
}

describe('store runtime continuity policy', () => {
  test('requires branch hub scope and seeded inventory before offline continuity activates', () => {
    expect(
      isOfflineSaleContinuityReady({
        runtimeProfile: 'branch_hub',
        branchCode: 'blrflagship',
        branchGstin: '29ABCDE1234F1Z5',
        hubDeviceId: 'device-hub-1',
        staffActorId: 'user-cashier',
        branchCatalogItems: buildCatalogItems(),
        inventorySnapshot: buildInventorySnapshot(),
      }),
    ).toBe(true);

    expect(
      isOfflineSaleContinuityReady({
        runtimeProfile: 'desktop_spoke',
        branchCode: 'blrflagship',
        branchGstin: '29ABCDE1234F1Z5',
        hubDeviceId: 'device-hub-1',
        staffActorId: 'user-cashier',
        branchCatalogItems: buildCatalogItems(),
        inventorySnapshot: buildInventorySnapshot(),
      }),
    ).toBe(false);
  });

  test('builds an offline sale draft, continuity invoice number, and decremented stock snapshot', () => {
    const result = prepareOfflineSaleContinuityDraft({
      tenantId: 'tenant-acme',
      branchId: 'branch-1',
      branchCode: 'blrflagship',
      hubDeviceId: 'device-hub-1',
      staffActorId: 'user-cashier',
      branchGstin: '29ABCDE1234F1Z5',
      customerName: 'Acme Traders',
      customerGstin: '29AAEPM0111C1Z3',
      paymentMethod: 'UPI',
      lineInputs: [{ product_id: 'product-1', quantity: 4 }],
      branchCatalogItems: buildCatalogItems(),
      inventorySnapshot: buildInventorySnapshot(),
      nextContinuityInvoiceSequence: 1,
      issuedAt: '2026-04-14T18:00:00.000Z',
    });

    expect(result.continuityInvoiceNumber).toBe('OFF-BLRFLAGSHIP-0001');
    expect(result.nextContinuityInvoiceSequence).toBe(2);
    expect(result.updatedInventory[0]?.stock_on_hand).toBe(20);
    expect(result.sale.grand_total).toBe(388.5);
    expect(result.sale.invoice_kind).toBe('B2B');
    expect(result.sale.lines[0]?.line_total).toBe(388.5);
  });
});
