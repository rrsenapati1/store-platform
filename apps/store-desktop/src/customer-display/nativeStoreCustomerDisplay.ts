import { invoke as tauriInvoke } from '@tauri-apps/api/core';

let browserPopupRef: WindowProxy | null = null;

export interface StoreCustomerDisplayInvoke {
  (command: string, payload?: Record<string, unknown>): Promise<unknown>;
}

export interface StoreCustomerDisplayAdapter {
  open(): Promise<void>;
  close(): Promise<void>;
}

export interface NativeStoreCustomerDisplayOptions {
  invoke?: StoreCustomerDisplayInvoke;
  browserOpen?: typeof window.open;
}

export function isNativeStoreCustomerDisplayAvailable(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

function resolveCustomerDisplayUrl(): string {
  if (typeof window === 'undefined') {
    return '/?customer-display=1';
  }
  const pathname = window.location.pathname || '/';
  return `${pathname}?customer-display=1`;
}

export function createNativeStoreCustomerDisplay(
  options: NativeStoreCustomerDisplayOptions = {},
): StoreCustomerDisplayAdapter {
  const invoke = options.invoke ?? tauriInvoke;
  const browserOpen = options.browserOpen ?? window.open.bind(window);

  return {
    async open() {
      if (isNativeStoreCustomerDisplayAvailable()) {
        await invoke('cmd_open_store_customer_display');
        return;
      }

      if (!browserPopupRef || browserPopupRef.closed) {
        browserPopupRef = browserOpen(
          resolveCustomerDisplayUrl(),
          'store-customer-display',
          'popup=yes,width=1280,height=720,resizable=yes',
        );
      }
      if (!browserPopupRef) {
        throw new Error('Unable to open the customer display window.');
      }
      browserPopupRef.focus?.();
    },

    async close() {
      if (isNativeStoreCustomerDisplayAvailable()) {
        await invoke('cmd_close_store_customer_display');
        return;
      }

      browserPopupRef?.close?.();
      browserPopupRef = null;
    },
  };
}
