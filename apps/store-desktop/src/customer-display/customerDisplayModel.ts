export type CustomerDisplayState = 'idle' | 'active_cart' | 'payment_in_progress' | 'sale_complete' | 'unavailable';

export interface CustomerDisplayLineItem {
  label: string;
  quantity: number;
  amount: number;
}

export interface CustomerDisplayPayload {
  state: CustomerDisplayState;
  title: string;
  message: string;
  currency_code: string;
  line_items: CustomerDisplayLineItem[];
  subtotal: number | null;
  discount_total: number | null;
  tax_total: number | null;
  grand_total: number | null;
  cash_received: number | null;
  change_due: number | null;
  updated_at: string | null;
}

export interface CustomerDisplayPreviewItem {
  product_name: string;
  effective_selling_price: number;
  gst_rate: number;
}

export interface CustomerDisplayCompletedSale {
  customer_name: string;
  invoice_number: string;
  issued_on?: string | null;
  subtotal: number;
  cgst_total: number;
  sgst_total: number;
  igst_total: number;
  grand_total: number;
  payment: {
    payment_method: string;
    amount: number;
  };
  lines: Array<{
    product_name: string;
    quantity: number;
    line_total: number;
  }>;
}

export interface BuildCustomerDisplayPayloadArgs {
  branchName: string | null;
  selectedItem: CustomerDisplayPreviewItem | null;
  saleQuantity: string;
  paymentMethod: string;
  latestSale: CustomerDisplayCompletedSale | null;
  isBusy: boolean;
}

const CUSTOMER_DISPLAY_STORAGE_KEY = 'store.customer-display.payload.v1';
const CUSTOMER_DISPLAY_STORAGE_EVENT = 'store:customer-display-payload';

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

function money(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

function parseQuantity(value: string): number | null {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isCustomerDisplayLineItem(value: unknown): value is CustomerDisplayLineItem {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.label === 'string'
    && typeof value.quantity === 'number'
    && typeof value.amount === 'number';
}

export function isCustomerDisplayPayload(value: unknown): value is CustomerDisplayPayload {
  if (!isObject(value)) {
    return false;
  }
  return (value.state === 'idle'
      || value.state === 'active_cart'
      || value.state === 'payment_in_progress'
      || value.state === 'sale_complete'
      || value.state === 'unavailable')
    && typeof value.title === 'string'
    && typeof value.message === 'string'
    && typeof value.currency_code === 'string'
    && Array.isArray(value.line_items)
    && value.line_items.every(isCustomerDisplayLineItem)
    && (typeof value.subtotal === 'number' || value.subtotal === null)
    && (typeof value.discount_total === 'number' || value.discount_total === null)
    && (typeof value.tax_total === 'number' || value.tax_total === null)
    && (typeof value.grand_total === 'number' || value.grand_total === null)
    && (typeof value.cash_received === 'number' || value.cash_received === null)
    && (typeof value.change_due === 'number' || value.change_due === null)
    && (typeof value.updated_at === 'string' || value.updated_at === null);
}

export function buildIdleCustomerDisplayPayload(branchName: string | null): CustomerDisplayPayload {
  return {
    state: 'idle',
    title: 'Ready for next customer',
    message: branchName
      ? `Waiting for the cashier terminal to start the next checkout at ${branchName}.`
      : 'Waiting for the cashier terminal to start the next checkout.',
    currency_code: 'INR',
    line_items: [],
    subtotal: null,
    discount_total: null,
    tax_total: null,
    grand_total: null,
    cash_received: null,
    change_due: null,
    updated_at: null,
  };
}

export function buildCustomerDisplayPayload(args: BuildCustomerDisplayPayloadArgs): CustomerDisplayPayload {
  if (args.latestSale) {
    const taxTotal = money(args.latestSale.cgst_total + args.latestSale.sgst_total + args.latestSale.igst_total);
    const cashReceived = args.latestSale.payment.payment_method === 'Cash'
      ? args.latestSale.payment.amount
      : null;
    const changeDue = cashReceived === null
      ? null
      : money(Math.max(cashReceived - args.latestSale.grand_total, 0));
    return {
      state: 'sale_complete',
      title: 'Payment complete',
      message: `Invoice ${args.latestSale.invoice_number}`,
      currency_code: 'INR',
      line_items: args.latestSale.lines.map((line) => ({
        label: line.product_name,
        quantity: line.quantity,
        amount: money(line.line_total),
      })),
      subtotal: money(args.latestSale.subtotal),
      discount_total: 0,
      tax_total: taxTotal,
      grand_total: money(args.latestSale.grand_total),
      cash_received: cashReceived,
      change_due: changeDue,
      updated_at: args.latestSale.issued_on ?? null,
    };
  }

  const quantity = parseQuantity(args.saleQuantity);
  if (!args.selectedItem || quantity === null) {
    return buildIdleCustomerDisplayPayload(args.branchName);
  }

  const subtotal = money(quantity * args.selectedItem.effective_selling_price);
  const taxTotal = money(subtotal * args.selectedItem.gst_rate / 100);
  const grandTotal = money(subtotal + taxTotal);
  const paymentLabel = args.paymentMethod || 'payment';

  return {
    state: args.isBusy ? 'payment_in_progress' : 'active_cart',
    title: args.isBusy ? 'Processing payment' : 'Current order',
    message: args.isBusy
      ? `Collecting ${paymentLabel} for this checkout`
      : `Reviewing cart for ${paymentLabel} payment`,
    currency_code: 'INR',
    line_items: [
      {
        label: args.selectedItem.product_name,
        quantity,
        amount: grandTotal,
      },
    ],
    subtotal,
    discount_total: 0,
    tax_total: taxTotal,
    grand_total: grandTotal,
    cash_received: null,
    change_due: null,
    updated_at: null,
  };
}

function resolveCustomerDisplayStorage(): StorageLike | null {
  if (typeof window !== 'undefined') {
    try {
      const storage = window.localStorage;
      if (storage && typeof storage.getItem === 'function') {
        return storage;
      }
    } catch {
      // Browser storage is unavailable for this runtime.
    }
  }

  if (typeof globalThis !== 'undefined' && 'localStorage' in globalThis) {
    try {
      const storage = globalThis.localStorage;
      if (storage && typeof storage.getItem === 'function') {
        return storage;
      }
    } catch {
      // Ignore non-accessible global storage bindings.
    }
  }

  return null;
}

export function loadCustomerDisplayPayload(): CustomerDisplayPayload | null {
  const storage = resolveCustomerDisplayStorage();
  if (!storage) {
    return null;
  }
  const raw = storage.getItem(CUSTOMER_DISPLAY_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    return isCustomerDisplayPayload(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function dispatchCustomerDisplayPayloadEvent(payload: CustomerDisplayPayload | null) {
  if (typeof window === 'undefined') {
    return;
  }
  window.dispatchEvent(new CustomEvent<CustomerDisplayPayload | null>(CUSTOMER_DISPLAY_STORAGE_EVENT, {
    detail: payload,
  }));
}

export function saveCustomerDisplayPayload(payload: CustomerDisplayPayload) {
  const storage = resolveCustomerDisplayStorage();
  if (!storage) {
    return;
  }
  storage.setItem(CUSTOMER_DISPLAY_STORAGE_KEY, JSON.stringify(payload));
  dispatchCustomerDisplayPayloadEvent(payload);
}

export function clearCustomerDisplayPayload() {
  const storage = resolveCustomerDisplayStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(CUSTOMER_DISPLAY_STORAGE_KEY);
  dispatchCustomerDisplayPayloadEvent(null);
}

export function getCustomerDisplayStorageEventName() {
  return CUSTOMER_DISPLAY_STORAGE_EVENT;
}

export function getCustomerDisplayStorageKey() {
  return CUSTOMER_DISPLAY_STORAGE_KEY;
}
