import type { ControlPlaneBranchCatalogItem, ControlPlaneInventorySnapshotRecord } from '@store/types';
import type {
  StoreRuntimeOfflineSaleLineRecord,
  StoreRuntimeOfflineSaleRecord,
  StoreRuntimeOfflineSaleTaxLineRecord,
} from './storeRuntimeContinuityStore';

type OfflineSaleLineInput = {
  product_id: string;
  quantity: number;
};

type PrepareOfflineSaleContinuityDraftArgs = {
  tenantId: string;
  branchId: string;
  branchCode: string;
  cashierSessionId: string;
  hubDeviceId: string;
  staffActorId: string;
  branchGstin?: string | null;
  customerName: string;
  customerGstin?: string | null;
  paymentMethod: string;
  lineInputs: OfflineSaleLineInput[];
  branchCatalogItems: ControlPlaneBranchCatalogItem[];
  inventorySnapshot: ControlPlaneInventorySnapshotRecord[];
  nextContinuityInvoiceSequence: number;
  issuedAt: string;
};

type OfflineSaleComputation = {
  continuityInvoiceNumber: string;
  nextContinuityInvoiceSequence: number;
  updatedInventory: ControlPlaneInventorySnapshotRecord[];
  sale: StoreRuntimeOfflineSaleRecord;
};

type OfflineSaleContinuityReadinessArgs = {
  runtimeProfile: string | null;
  branchCode?: string | null;
  branchGstin?: string | null;
  hubDeviceId?: string | null;
  staffActorId?: string | null;
  branchCatalogItems: ControlPlaneBranchCatalogItem[];
  inventorySnapshot: ControlPlaneInventorySnapshotRecord[];
};

function money(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

function normalizeGstin(value?: string | null): string | null {
  const normalized = value?.trim().toUpperCase() ?? '';
  return normalized ? normalized : null;
}

function stateCode(gstin?: string | null): string | null {
  const normalized = normalizeGstin(gstin);
  if (!normalized || normalized.length < 2) {
    return null;
  }
  return normalized.slice(0, 2);
}

function randomId(prefix: string) {
  const randomPart = globalThis.crypto?.randomUUID?.() ?? Math.random().toString(16).slice(2);
  return `${prefix}-${randomPart}`;
}

function buildContinuityInvoiceNumber(branchCode: string, sequence: number) {
  const branchSegment = branchCode.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
  return `OFF-${branchSegment}-${String(sequence).padStart(4, '0')}`;
}

function ensureOfflineStockAvailable(requestedQuantity: number, availableQuantity: number) {
  if (money(requestedQuantity) <= 0) {
    throw new Error('Sale quantity must be greater than zero');
  }
  if (money(requestedQuantity) > money(availableQuantity)) {
    throw new Error('Insufficient stock for offline sale');
  }
}

export function isOfflineSaleContinuityReady(args: OfflineSaleContinuityReadinessArgs) {
  return args.runtimeProfile === 'branch_hub'
    && Boolean(args.branchCode?.trim())
    && Boolean(args.branchGstin?.trim())
    && Boolean(args.hubDeviceId?.trim())
    && Boolean(args.staffActorId?.trim())
    && args.branchCatalogItems.length > 0
    && args.inventorySnapshot.length > 0;
}

export function prepareOfflineSaleContinuityDraft(
  args: PrepareOfflineSaleContinuityDraftArgs,
): OfflineSaleComputation {
  const branchCatalogByProductId = new Map(
    args.branchCatalogItems.map((item) => [item.product_id, item]),
  );
  const inventoryByProductId = new Map(
    args.inventorySnapshot.map((record) => [record.product_id, record]),
  );
  const normalizedCustomerGstin = normalizeGstin(args.customerGstin);
  const invoiceKind = normalizedCustomerGstin ? 'B2B' : 'B2C';
  const irnStatus = normalizedCustomerGstin ? 'IRN_PENDING' : 'NOT_REQUIRED';
  const isInterState = normalizedCustomerGstin !== null
    && stateCode(args.branchGstin) !== null
    && stateCode(args.branchGstin) !== stateCode(normalizedCustomerGstin);

  const lines: StoreRuntimeOfflineSaleLineRecord[] = [];
  const taxGroups = new Map<string, StoreRuntimeOfflineSaleTaxLineRecord>();
  let subtotal = 0;
  let taxTotal = 0;

  for (const lineInput of args.lineInputs) {
    const catalogItem = branchCatalogByProductId.get(lineInput.product_id);
    if (!catalogItem) {
      throw new Error('Catalog product not found for offline sale');
    }
    if (catalogItem.availability_status.toUpperCase() !== 'ACTIVE') {
      throw new Error('Branch catalog item is not active');
    }
    const inventoryRecord = inventoryByProductId.get(lineInput.product_id);
    if (!inventoryRecord) {
      throw new Error('Inventory snapshot not found for offline sale');
    }
    ensureOfflineStockAvailable(lineInput.quantity, inventoryRecord.stock_on_hand);

    const quantity = money(lineInput.quantity);
    const unitPrice = money(catalogItem.effective_selling_price);
    const gstRate = money(catalogItem.gst_rate);
    const lineSubtotal = money(quantity * unitPrice);
    const lineTaxTotal = money(lineSubtotal * gstRate / 100);
    const lineTotal = money(lineSubtotal + lineTaxTotal);

    lines.push({
      product_id: catalogItem.product_id,
      product_name: catalogItem.product_name,
      sku_code: catalogItem.sku_code,
      hsn_sac_code: catalogItem.hsn_sac_code,
      quantity,
      unit_price: unitPrice,
      gst_rate: gstRate,
      line_subtotal: lineSubtotal,
      tax_total: lineTaxTotal,
      line_total: lineTotal,
    });

    subtotal = money(subtotal + lineSubtotal);
    taxTotal = money(taxTotal + lineTaxTotal);

    if (isInterState) {
      const key = `IGST:${gstRate}`;
      const current = taxGroups.get(key) ?? {
        tax_type: 'IGST',
        tax_rate: gstRate,
        taxable_amount: 0,
        tax_amount: 0,
      };
      current.taxable_amount = money(current.taxable_amount + lineSubtotal);
      current.tax_amount = money(current.tax_amount + lineTaxTotal);
      taxGroups.set(key, current);
    } else {
      const splitRate = money(gstRate / 2);
      const cgstAmount = money(lineTaxTotal / 2);
      const sgstAmount = money(lineTaxTotal - cgstAmount);
      for (const [taxType, amount] of [['CGST', cgstAmount], ['SGST', sgstAmount]] as const) {
        const key = `${taxType}:${splitRate}`;
        const current = taxGroups.get(key) ?? {
          tax_type: taxType,
          tax_rate: splitRate,
          taxable_amount: 0,
          tax_amount: 0,
        };
        current.taxable_amount = money(current.taxable_amount + lineSubtotal);
        current.tax_amount = money(current.tax_amount + amount);
        taxGroups.set(key, current);
      }
    }
  }

  const taxLines = Array.from(taxGroups.values()).sort((left, right) => {
    const leftKey = `${left.tax_type}:${left.tax_rate}`;
    const rightKey = `${right.tax_type}:${right.tax_rate}`;
    return leftKey.localeCompare(rightKey);
  });
  const cgstTotal = money(
    taxLines.filter((line) => line.tax_type === 'CGST').reduce((sum, line) => sum + line.tax_amount, 0),
  );
  const sgstTotal = money(
    taxLines.filter((line) => line.tax_type === 'SGST').reduce((sum, line) => sum + line.tax_amount, 0),
  );
  const igstTotal = money(
    taxLines.filter((line) => line.tax_type === 'IGST').reduce((sum, line) => sum + line.tax_amount, 0),
  );

  const updatedInventory = args.inventorySnapshot.map((record) => {
    const matchingLine = args.lineInputs.find((line) => line.product_id === record.product_id);
    if (!matchingLine) {
      return record;
    }
    return {
      ...record,
      stock_on_hand: money(record.stock_on_hand - matchingLine.quantity),
      last_entry_type: 'OFFLINE_SALE',
    };
  });

  const continuityInvoiceNumber = buildContinuityInvoiceNumber(
    args.branchCode,
    args.nextContinuityInvoiceSequence,
  );
  const continuitySaleId = randomId('offline-sale');

  return {
    continuityInvoiceNumber,
    nextContinuityInvoiceSequence: args.nextContinuityInvoiceSequence + 1,
    updatedInventory,
    sale: {
      continuity_sale_id: continuitySaleId,
      continuity_invoice_number: continuityInvoiceNumber,
      tenant_id: args.tenantId,
      branch_id: args.branchId,
      cashier_session_id: args.cashierSessionId,
      hub_device_id: args.hubDeviceId,
      staff_actor_id: args.staffActorId,
      customer_name: args.customerName.trim(),
      customer_gstin: normalizedCustomerGstin,
      invoice_kind: invoiceKind,
      irn_status: irnStatus,
      payment_method: args.paymentMethod,
      subtotal,
      cgst_total: cgstTotal,
      sgst_total: sgstTotal,
      igst_total: igstTotal,
      grand_total: money(subtotal + taxTotal),
      issued_offline_at: args.issuedAt,
      idempotency_key: `offline-replay-${continuitySaleId}`,
      reconciliation_state: 'PENDING_REPLAY',
      lines,
      tax_lines: taxLines,
      replayed_sale_id: null,
      replayed_invoice_number: null,
      replay_error: null,
    },
  };
}
