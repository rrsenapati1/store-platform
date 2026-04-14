import { describe, expect, test, vi } from 'vitest';
import { createResolvedStoreRuntimeHardware } from './storeRuntimeHardware';

describe('resolved store runtime hardware adapter', () => {
  test('uses native hardware bridge when packaged runtime is available', async () => {
    const invoke = vi.fn(async (command: string, payload?: Record<string, unknown>) => {
      if (command === 'cmd_get_store_runtime_hardware_status') {
        return {
          bridge_state: 'ready',
          printers: [
            {
              name: 'Thermal-01',
              label: 'Thermal-01',
              is_default: true,
              is_online: true,
            },
          ],
          profile: {
            receipt_printer_name: 'Thermal-01',
            label_printer_name: null,
            updated_at: '2026-04-14T16:00:00.000Z',
          },
          diagnostics: {
            scanner_capture_state: 'ready',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_scan_at: null,
          },
        };
      }
      if (command === 'cmd_save_store_runtime_hardware_profile') {
        return {
          bridge_state: 'ready',
          printers: [],
          profile: {
            receipt_printer_name: payload?.receipt_printer_name ?? null,
            label_printer_name: payload?.label_printer_name ?? null,
            updated_at: '2026-04-14T16:05:00.000Z',
          },
          diagnostics: {
            scanner_capture_state: 'ready',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_scan_at: null,
          },
        };
      }
      throw new Error(`Unexpected command: ${command}`);
    });

    const adapter = createResolvedStoreRuntimeHardware({
      invoke,
      isNativeRuntime: () => true,
    });

    await expect(adapter.getStatus()).resolves.toEqual({
      bridge_state: 'ready',
      printers: [
        {
          name: 'Thermal-01',
          label: 'Thermal-01',
          is_default: true,
          is_online: true,
        },
      ],
      profile: {
        receipt_printer_name: 'Thermal-01',
        label_printer_name: null,
        updated_at: '2026-04-14T16:00:00.000Z',
      },
      diagnostics: {
        scanner_capture_state: 'ready',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_scan_at: null,
      },
    });

    await expect(
      adapter.saveProfile({
        receipt_printer_name: 'Thermal-02',
        label_printer_name: 'Label-01',
      }),
    ).resolves.toEqual({
      bridge_state: 'ready',
      printers: [],
      profile: {
        receipt_printer_name: 'Thermal-02',
        label_printer_name: 'Label-01',
        updated_at: '2026-04-14T16:05:00.000Z',
      },
      diagnostics: {
        scanner_capture_state: 'ready',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_scan_at: null,
      },
    });

    expect(invoke).toHaveBeenNthCalledWith(1, 'cmd_get_store_runtime_hardware_status');
    expect(invoke).toHaveBeenNthCalledWith(2, 'cmd_save_store_runtime_hardware_profile', {
      receipt_printer_name: 'Thermal-02',
      label_printer_name: 'Label-01',
    });
  });

  test('falls back to unavailable hardware status in the web shell', async () => {
    const adapter = createResolvedStoreRuntimeHardware({
      isNativeRuntime: () => false,
    });

    await expect(adapter.getStatus()).resolves.toEqual({
      bridge_state: 'browser_fallback',
      printers: [],
      profile: {
        receipt_printer_name: null,
        label_printer_name: null,
        updated_at: null,
      },
      diagnostics: {
        scanner_capture_state: 'browser_fallback',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_scan_at: null,
      },
    });
  });

  test('falls back to browser hardware status when the native command is unavailable', async () => {
    const adapter = createResolvedStoreRuntimeHardware({
      invoke: vi.fn(async () => {
        throw new Error('Unexpected command: cmd_get_store_runtime_hardware_status');
      }),
      isNativeRuntime: () => true,
    });

    await expect(adapter.getStatus()).resolves.toEqual({
      bridge_state: 'browser_fallback',
      printers: [],
      profile: {
        receipt_printer_name: null,
        label_printer_name: null,
        updated_at: null,
      },
      diagnostics: {
        scanner_capture_state: 'browser_fallback',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_scan_at: null,
      },
    });
  });
});
