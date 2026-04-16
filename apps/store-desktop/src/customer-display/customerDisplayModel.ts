export type CustomerDisplayState = 'idle' | 'active_cart' | 'payment_in_progress' | 'sale_complete' | 'unavailable';

export interface CustomerDisplayLineItem {
  label: string;
  quantity: number;
  amount: number;
}

export interface CustomerDisplayPaymentQr {
  format: string;
  value: string;
  expires_at: string | null;
}

export interface CustomerDisplayPaymentAction {
  kind: string;
  value: string;
  label?: string | null;
  description?: string | null;
  handoff_surface?: string | null;
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
  payment_action: CustomerDisplayPaymentAction | null;
  payment_qr: CustomerDisplayPaymentQr | null;
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
  checkoutPaymentSession: {
    payment_method: string;
    handoff_surface: string;
    lifecycle_status: string;
    order_amount: number;
    currency_code: string;
    action_payload: CustomerDisplayPaymentAction;
    action_expires_at?: string | null;
    qr_payload: {
      format: string;
      value: string;
    } | null;
    qr_expires_at?: string | null;
  } | null;
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

function isCustomerDisplayPaymentQr(value: unknown): value is CustomerDisplayPaymentQr {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.format === 'string'
    && typeof value.value === 'string'
    && (typeof value.expires_at === 'string' || value.expires_at === null);
}

function isCustomerDisplayPaymentAction(value: unknown): value is CustomerDisplayPaymentAction {
  if (!isObject(value)) {
    return false;
  }
  return typeof value.kind === 'string'
    && typeof value.value === 'string'
    && (typeof value.label === 'string' || value.label === null || typeof value.label === 'undefined')
    && (typeof value.description === 'string' || value.description === null || typeof value.description === 'undefined')
    && (typeof value.handoff_surface === 'string' || value.handoff_surface === null || typeof value.handoff_surface === 'undefined');
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
    && (value.payment_action === null || isCustomerDisplayPaymentAction(value.payment_action))
    && (value.payment_qr === null || isCustomerDisplayPaymentQr(value.payment_qr))
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
    payment_action: null,
    payment_qr: null,
    updated_at: null,
  };
}

function buildCheckoutPaymentPreview(
  args: BuildCustomerDisplayPayloadArgs,
): CustomerDisplayPayload {
  const quantity = parseQuantity(args.saleQuantity);
  const subtotal = args.selectedItem && quantity !== null
    ? money(quantity * args.selectedItem.effective_selling_price)
    : null;
  const taxTotal = args.selectedItem && quantity !== null
    ? money(subtotal! * args.selectedItem.gst_rate / 100)
    : null;
  const lineItems = args.selectedItem && quantity !== null
    ? [
        {
          label: args.selectedItem.product_name,
          quantity,
          amount: money(args.checkoutPaymentSession!.order_amount),
        },
      ]
    : [];
  const activePaymentState = args.checkoutPaymentSession!.lifecycle_status === 'FAILED'
    || args.checkoutPaymentSession!.lifecycle_status === 'EXPIRED'
    || args.checkoutPaymentSession!.lifecycle_status === 'CANCELED'
    ? 'unavailable'
    : 'payment_in_progress';
  const paymentAction: CustomerDisplayPaymentAction = {
    kind: args.checkoutPaymentSession!.action_payload.kind,
    value: args.checkoutPaymentSession!.action_payload.value,
    label: args.checkoutPaymentSession!.action_payload.label ?? null,
    description: args.checkoutPaymentSession!.action_payload.description ?? null,
    handoff_surface: args.checkoutPaymentSession!.handoff_surface,
  };
  const isPhoneHandoff = args.checkoutPaymentSession!.handoff_surface === 'HOSTED_PHONE';
  const isTerminalHandoff = args.checkoutPaymentSession!.handoff_surface === 'HOSTED_TERMINAL';
  const paymentQr = activePaymentState === 'unavailable'
    ? null
    : args.checkoutPaymentSession!.handoff_surface === 'BRANDED_UPI_QR'
      ? {
          format: args.checkoutPaymentSession!.qr_payload?.format ?? 'upi_qr',
          value: args.checkoutPaymentSession!.qr_payload?.value ?? args.checkoutPaymentSession!.action_payload.value,
          expires_at: args.checkoutPaymentSession!.qr_expires_at ?? args.checkoutPaymentSession!.action_expires_at ?? null,
        }
      : isPhoneHandoff
        ? {
            format: args.checkoutPaymentSession!.qr_payload?.format ?? 'hosted_url',
            value: args.checkoutPaymentSession!.qr_payload?.value ?? args.checkoutPaymentSession!.action_payload.value,
            expires_at: args.checkoutPaymentSession!.qr_expires_at ?? args.checkoutPaymentSession!.action_expires_at ?? null,
          }
        : null;

  return {
    state: activePaymentState,
    title: activePaymentState === 'unavailable'
      ? 'Payment unavailable'
      : isPhoneHandoff
        ? 'Continue on phone'
        : isTerminalHandoff
          ? 'Complete payment on terminal'
          : 'Scan to pay',
    message: activePaymentState === 'unavailable'
      ? 'Ask the cashier to retry or switch to a manual payment method.'
      : args.checkoutPaymentSession!.action_payload.description
        ?? (isTerminalHandoff
          ? 'The cashier is continuing the hosted checkout on this terminal.'
          : isPhoneHandoff
            ? 'Scan this QR on the customer phone to open hosted checkout.'
            : 'Scan to pay with any UPI app.'),
    currency_code: args.checkoutPaymentSession!.currency_code,
    line_items: lineItems,
    subtotal,
    discount_total: 0,
    tax_total: taxTotal,
    grand_total: money(args.checkoutPaymentSession!.order_amount),
    cash_received: null,
    change_due: null,
    payment_action: paymentAction,
    payment_qr: paymentQr,
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
      payment_action: null,
      payment_qr: null,
      updated_at: args.latestSale.issued_on ?? null,
    };
  }

  if (args.checkoutPaymentSession) {
    return buildCheckoutPaymentPreview(args);
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
    payment_action: null,
    payment_qr: null,
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
