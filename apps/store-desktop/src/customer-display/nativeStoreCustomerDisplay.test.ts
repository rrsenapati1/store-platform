/* @vitest-environment jsdom */
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

const { mockInvoke } = vi.hoisted(() => ({
  mockInvoke: vi.fn(),
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: mockInvoke,
}));

import { createNativeStoreCustomerDisplay, isNativeStoreCustomerDisplayAvailable } from './nativeStoreCustomerDisplay';

describe('native store customer display adapter', () => {
  let originalTauriInternals: object | undefined;
  let originalOpen: typeof window.open;

  beforeEach(() => {
    originalTauriInternals = (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;
    originalOpen = window.open;
    mockInvoke.mockReset();
  });

  afterEach(() => {
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = originalTauriInternals;
    window.open = originalOpen;
    vi.restoreAllMocks();
  });

  test('uses tauri commands when the packaged bridge is available', async () => {
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = {};
    mockInvoke.mockResolvedValue(undefined);
    const adapter = createNativeStoreCustomerDisplay();

    expect(isNativeStoreCustomerDisplayAvailable()).toBe(true);

    await adapter.open();
    await adapter.close();

    expect(mockInvoke).toHaveBeenNthCalledWith(1, 'cmd_open_store_customer_display');
    expect(mockInvoke).toHaveBeenNthCalledWith(2, 'cmd_close_store_customer_display');
  });

  test('falls back to a browser popup when the packaged bridge is unavailable', async () => {
    delete (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;
    const focus = vi.fn();
    const close = vi.fn();
    const browserOpen = vi.fn(() => ({ focus, close, closed: false } as unknown as WindowProxy));
    window.open = browserOpen;
    const adapter = createNativeStoreCustomerDisplay({ browserOpen });

    await adapter.open();
    await adapter.close();

    expect(browserOpen).toHaveBeenCalledWith(
      '/?customer-display=1',
      'store-customer-display',
      expect.stringContaining('popup=yes'),
    );
    expect(focus).toHaveBeenCalled();
    expect(close).toHaveBeenCalled();
    expect(mockInvoke).not.toHaveBeenCalled();
  });
});
