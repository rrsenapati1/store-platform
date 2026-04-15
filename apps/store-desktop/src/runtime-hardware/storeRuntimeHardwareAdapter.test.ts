import { describe, expect, test, vi } from 'vitest';
import { createResolvedStoreRuntimeHardware } from './storeRuntimeHardware';

describe('resolved store runtime hardware adapter', () => {
  test('uses native hardware bridge when packaged runtime is available', async () => {
    const invoke = vi.fn(async (command: string, payload?: Record<string, unknown>) => {
      if (command === 'cmd_get_store_runtime_hardware_status') {
        return {
          bridge_state: 'ready',
          scales: [
            {
              id: 'scale-com3',
              label: 'Serial scale (COM3)',
              transport: 'serial_com',
              port_name: 'COM3',
              is_connected: true,
            },
          ],
          scanners: [
            {
              id: 'scanner-zebra-1',
              label: 'Zebra DS2208',
              transport: 'usb_hid',
              vendor_name: 'Zebra',
              product_name: 'DS2208',
              serial_number: 'ZB-001',
              is_connected: true,
            },
          ],
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
            cash_drawer_printer_name: 'Thermal-01',
            preferred_scale_id: 'scale-com3',
            preferred_scanner_id: 'scanner-zebra-1',
            updated_at: '2026-04-14T16:00:00.000Z',
          },
          diagnostics: {
            scale_capture_state: 'ready',
            scanner_capture_state: 'ready',
            scanner_transport: 'usb_hid',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_cash_drawer_status: null,
            last_cash_drawer_message: null,
            last_cash_drawer_opened_at: null,
            last_weight_value: 0.5,
            last_weight_unit: 'kg',
            last_weight_status: 'captured',
            last_weight_message: 'Captured 0.500 kg from Serial scale (COM3)',
            last_weight_read_at: '2026-04-15T12:00:00.000Z',
            last_scan_at: null,
            last_scan_barcode_preview: null,
            scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
            scale_setup_hint: 'Use the hardware desk to refresh the live weight before weighing a loose item.',
            cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
            cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
            scanner_status_message: 'Ready for external scanner input',
            scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
          },
        };
      }
      if (command === 'cmd_save_store_runtime_hardware_profile') {
        return {
          bridge_state: 'ready',
          scales: [
            {
              id: payload?.preferred_scale_id === 'scale-com4' ? 'scale-com4' : 'scale-com3',
              label: payload?.preferred_scale_id === 'scale-com4' ? 'Serial scale (COM4)' : 'Serial scale (COM3)',
              transport: 'serial_com',
              port_name: payload?.preferred_scale_id === 'scale-com4' ? 'COM4' : 'COM3',
              is_connected: true,
            },
          ],
          scanners: [
            {
              id: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'scanner-blue-1' : 'scanner-zebra-1',
              label: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'Socket Mobile S740' : 'Zebra DS2208',
              transport: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'bluetooth_hid' : 'usb_hid',
              vendor_name: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'Socket Mobile' : 'Zebra',
              product_name: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'S740' : 'DS2208',
              serial_number: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'SO-001' : 'ZB-001',
              is_connected: true,
            },
          ],
          printers: [],
          profile: {
            receipt_printer_name: payload?.receipt_printer_name ?? null,
            label_printer_name: payload?.label_printer_name ?? null,
            cash_drawer_printer_name: payload?.cash_drawer_printer_name ?? null,
            preferred_scale_id: payload?.preferred_scale_id ?? null,
            preferred_scanner_id: payload?.preferred_scanner_id ?? null,
            updated_at: '2026-04-14T16:05:00.000Z',
          },
          diagnostics: {
            scale_capture_state: 'ready',
            scanner_capture_state: 'ready',
            scanner_transport: payload?.preferred_scanner_id === 'scanner-blue-1' ? 'bluetooth_hid' : 'usb_hid',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_cash_drawer_status: null,
            last_cash_drawer_message: null,
            last_cash_drawer_opened_at: null,
            last_weight_value: payload?.preferred_scale_id === 'scale-com4' ? 1.25 : 0.5,
            last_weight_unit: 'kg',
            last_weight_status: 'captured',
            last_weight_message: payload?.preferred_scale_id === 'scale-com4'
              ? 'Captured 1.250 kg from Serial scale (COM4)'
              : 'Captured 0.500 kg from Serial scale (COM3)',
            last_weight_read_at: '2026-04-15T12:05:00.000Z',
            last_scan_at: null,
            last_scan_barcode_preview: null,
            scale_status_message: payload?.preferred_scale_id
              ? `Preferred scale ready: ${payload.preferred_scale_id === 'scale-com4' ? 'Serial scale (COM4)' : 'Serial scale (COM3)'}.`
              : 'Assign a serial scale to read live weights.',
            scale_setup_hint: 'Connect a local serial/COM scale and assign it before requesting a live read.',
            cash_drawer_status_message: payload?.cash_drawer_printer_name
              ? `Cash drawer is assigned to ${payload.cash_drawer_printer_name}.`
              : 'Assign a local receipt printer to enable cash drawer pulses.',
            cash_drawer_setup_hint: 'Use a receipt printer with a connected RJ11 cash drawer.',
            scanner_status_message: 'Ready for external scanner input',
            scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
          },
        };
      }
      if (command === 'cmd_open_store_runtime_cash_drawer') {
        return {
          bridge_state: 'ready',
          scales: [
            {
              id: 'scale-com3',
              label: 'Serial scale (COM3)',
              transport: 'serial_com',
              port_name: 'COM3',
              is_connected: true,
            },
          ],
          scanners: [],
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
            cash_drawer_printer_name: 'Thermal-01',
            preferred_scale_id: 'scale-com3',
            preferred_scanner_id: 'scanner-zebra-1',
            updated_at: '2026-04-14T16:05:00.000Z',
          },
          diagnostics: {
            scale_capture_state: 'ready',
            scanner_capture_state: 'ready',
            scanner_transport: 'usb_hid',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_cash_drawer_status: 'opened',
            last_cash_drawer_message: 'Opened cash drawer through Thermal-01',
            last_cash_drawer_opened_at: '2026-04-15T12:05:00.000Z',
            last_weight_value: 0.5,
            last_weight_unit: 'kg',
            last_weight_status: 'captured',
            last_weight_message: 'Captured 0.500 kg from Serial scale (COM3)',
            last_weight_read_at: '2026-04-15T12:00:00.000Z',
            last_scan_at: null,
            last_scan_barcode_preview: null,
            scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
            scale_setup_hint: 'Use the hardware desk to refresh the live weight before weighing a loose item.',
            cash_drawer_status_message: 'Cash drawer pulse sent to Thermal-01.',
            cash_drawer_setup_hint: 'Close the drawer fully before the next manual open action.',
            scanner_status_message: 'Ready for external scanner input',
            scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
          },
        };
      }
      if (command === 'cmd_read_store_runtime_scale_weight') {
        return {
          bridge_state: 'ready',
          scales: [
            {
              id: 'scale-com3',
              label: 'Serial scale (COM3)',
              transport: 'serial_com',
              port_name: 'COM3',
              is_connected: true,
            },
          ],
          scanners: [],
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
            cash_drawer_printer_name: 'Thermal-01',
            preferred_scale_id: 'scale-com3',
            preferred_scanner_id: 'scanner-zebra-1',
            updated_at: '2026-04-14T16:05:00.000Z',
          },
          diagnostics: {
            scale_capture_state: 'ready',
            scanner_capture_state: 'ready',
            scanner_transport: 'usb_hid',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_cash_drawer_status: null,
            last_cash_drawer_message: null,
            last_cash_drawer_opened_at: null,
            last_weight_value: 1.245,
            last_weight_unit: 'kg',
            last_weight_status: 'captured',
            last_weight_message: 'Captured 1.245 kg from Serial scale (COM3)',
            last_weight_read_at: '2026-04-15T12:10:00.000Z',
            last_scan_at: null,
            last_scan_barcode_preview: null,
            scale_status_message: 'Latest weight ready from Serial scale (COM3).',
            scale_setup_hint: 'Use the refreshed live weight in the counter workflow if the item is sold loose.',
            cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
            cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
            scanner_status_message: 'Ready for external scanner input',
            scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
          },
        };
      }
      if (command === 'cmd_record_store_runtime_scanner_activity') {
        return {
          bridge_state: 'ready',
          scales: [
            {
              id: 'scale-com3',
              label: 'Serial scale (COM3)',
              transport: 'serial_com',
              port_name: 'COM3',
              is_connected: true,
            },
          ],
          scanners: [
            {
              id: 'scanner-zebra-1',
              label: 'Zebra DS2208',
              transport: 'usb_hid',
              vendor_name: 'Zebra',
              product_name: 'DS2208',
              serial_number: 'ZB-001',
              is_connected: true,
            },
          ],
          printers: [],
          profile: {
            receipt_printer_name: 'Thermal-01',
            label_printer_name: null,
            cash_drawer_printer_name: 'Thermal-01',
            preferred_scale_id: 'scale-com3',
            preferred_scanner_id: 'scanner-zebra-1',
            updated_at: '2026-04-14T16:05:00.000Z',
          },
          diagnostics: {
            scale_capture_state: 'ready',
            scanner_capture_state: 'ready',
            scanner_transport: payload?.scanner_transport ?? 'usb_hid',
            last_print_status: null,
            last_print_message: null,
            last_printed_at: null,
            last_cash_drawer_status: null,
            last_cash_drawer_message: null,
            last_cash_drawer_opened_at: null,
            last_weight_value: 0.5,
            last_weight_unit: 'kg',
            last_weight_status: 'captured',
            last_weight_message: 'Captured 0.500 kg from Serial scale (COM3)',
            last_weight_read_at: '2026-04-15T12:00:00.000Z',
            last_scan_at: '2026-04-15T12:00:00.000Z',
            last_scan_barcode_preview: payload?.barcode_preview ?? null,
            scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
            scale_setup_hint: 'Use the hardware desk to refresh the live weight before weighing a loose item.',
            cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
            cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
            scanner_status_message: 'Preferred HID scanner connected: Zebra DS2208',
            scanner_setup_hint: 'Scan into the active packaged terminal to keep HID activity diagnostics current.',
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
      scales: [
        {
          id: 'scale-com3',
          label: 'Serial scale (COM3)',
          transport: 'serial_com',
          port_name: 'COM3',
          is_connected: true,
        },
      ],
      scanners: [
        {
          id: 'scanner-zebra-1',
          label: 'Zebra DS2208',
          transport: 'usb_hid',
          vendor_name: 'Zebra',
          product_name: 'DS2208',
          serial_number: 'ZB-001',
          is_connected: true,
        },
      ],
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
        cash_drawer_printer_name: 'Thermal-01',
        preferred_scale_id: 'scale-com3',
        preferred_scanner_id: 'scanner-zebra-1',
        updated_at: '2026-04-14T16:00:00.000Z',
      },
      diagnostics: {
        scale_capture_state: 'ready',
        scanner_capture_state: 'ready',
        scanner_transport: 'usb_hid',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: null,
        last_cash_drawer_message: null,
        last_cash_drawer_opened_at: null,
        last_weight_value: 0.5,
        last_weight_unit: 'kg',
        last_weight_status: 'captured',
        last_weight_message: 'Captured 0.500 kg from Serial scale (COM3)',
        last_weight_read_at: '2026-04-15T12:00:00.000Z',
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
        scale_setup_hint: 'Use the hardware desk to refresh the live weight before weighing a loose item.',
        cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
        cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
        scanner_status_message: 'Ready for external scanner input',
        scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
      },
    });

    await expect(
      adapter.saveProfile({
        receipt_printer_name: 'Thermal-02',
        label_printer_name: 'Label-01',
        cash_drawer_printer_name: 'Thermal-02',
        preferred_scale_id: 'scale-com4',
        preferred_scanner_id: 'scanner-blue-1',
      }),
    ).resolves.toEqual({
      bridge_state: 'ready',
      scales: [
        {
          id: 'scale-com4',
          label: 'Serial scale (COM4)',
          transport: 'serial_com',
          port_name: 'COM4',
          is_connected: true,
        },
      ],
      scanners: [
        {
          id: 'scanner-blue-1',
          label: 'Socket Mobile S740',
          transport: 'bluetooth_hid',
          vendor_name: 'Socket Mobile',
          product_name: 'S740',
          serial_number: 'SO-001',
          is_connected: true,
        },
      ],
      printers: [],
      profile: {
        receipt_printer_name: 'Thermal-02',
        label_printer_name: 'Label-01',
        cash_drawer_printer_name: 'Thermal-02',
        preferred_scale_id: 'scale-com4',
        preferred_scanner_id: 'scanner-blue-1',
        updated_at: '2026-04-14T16:05:00.000Z',
      },
      diagnostics: {
        scale_capture_state: 'ready',
        scanner_capture_state: 'ready',
        scanner_transport: 'bluetooth_hid',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: null,
        last_cash_drawer_message: null,
        last_cash_drawer_opened_at: null,
        last_weight_value: 1.25,
        last_weight_unit: 'kg',
        last_weight_status: 'captured',
        last_weight_message: 'Captured 1.250 kg from Serial scale (COM4)',
        last_weight_read_at: '2026-04-15T12:05:00.000Z',
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Preferred scale ready: Serial scale (COM4).',
        scale_setup_hint: 'Connect a local serial/COM scale and assign it before requesting a live read.',
        cash_drawer_status_message: 'Cash drawer is assigned to Thermal-02.',
        cash_drawer_setup_hint: 'Use a receipt printer with a connected RJ11 cash drawer.',
        scanner_status_message: 'Ready for external scanner input',
        scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
      },
    });

    expect(invoke).toHaveBeenNthCalledWith(1, 'cmd_get_store_runtime_hardware_status');
    expect(invoke).toHaveBeenNthCalledWith(2, 'cmd_save_store_runtime_hardware_profile', {
      receipt_printer_name: 'Thermal-02',
      label_printer_name: 'Label-01',
      cash_drawer_printer_name: 'Thermal-02',
      preferred_scale_id: 'scale-com4',
      preferred_scanner_id: 'scanner-blue-1',
    });

    await expect(adapter.openCashDrawer()).resolves.toEqual({
      bridge_state: 'ready',
      scales: [
        {
          id: 'scale-com3',
          label: 'Serial scale (COM3)',
          transport: 'serial_com',
          port_name: 'COM3',
          is_connected: true,
        },
      ],
      scanners: [],
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
        cash_drawer_printer_name: 'Thermal-01',
        preferred_scale_id: 'scale-com3',
        preferred_scanner_id: 'scanner-zebra-1',
        updated_at: '2026-04-14T16:05:00.000Z',
      },
      diagnostics: {
        scale_capture_state: 'ready',
        scanner_capture_state: 'ready',
        scanner_transport: 'usb_hid',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: 'opened',
        last_cash_drawer_message: 'Opened cash drawer through Thermal-01',
        last_cash_drawer_opened_at: '2026-04-15T12:05:00.000Z',
        last_weight_value: 0.5,
        last_weight_unit: 'kg',
        last_weight_status: 'captured',
        last_weight_message: 'Captured 0.500 kg from Serial scale (COM3)',
        last_weight_read_at: '2026-04-15T12:00:00.000Z',
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
        scale_setup_hint: 'Use the hardware desk to refresh the live weight before weighing a loose item.',
        cash_drawer_status_message: 'Cash drawer pulse sent to Thermal-01.',
        cash_drawer_setup_hint: 'Close the drawer fully before the next manual open action.',
        scanner_status_message: 'Ready for external scanner input',
        scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
      },
    });

    expect(invoke).toHaveBeenNthCalledWith(3, 'cmd_open_store_runtime_cash_drawer');

    await expect(adapter.readScaleWeight()).resolves.toEqual({
      bridge_state: 'ready',
      scales: [
        {
          id: 'scale-com3',
          label: 'Serial scale (COM3)',
          transport: 'serial_com',
          port_name: 'COM3',
          is_connected: true,
        },
      ],
      scanners: [],
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
        cash_drawer_printer_name: 'Thermal-01',
        preferred_scale_id: 'scale-com3',
        preferred_scanner_id: 'scanner-zebra-1',
        updated_at: '2026-04-14T16:05:00.000Z',
      },
      diagnostics: {
        scale_capture_state: 'ready',
        scanner_capture_state: 'ready',
        scanner_transport: 'usb_hid',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: null,
        last_cash_drawer_message: null,
        last_cash_drawer_opened_at: null,
        last_weight_value: 1.245,
        last_weight_unit: 'kg',
        last_weight_status: 'captured',
        last_weight_message: 'Captured 1.245 kg from Serial scale (COM3)',
        last_weight_read_at: '2026-04-15T12:10:00.000Z',
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Latest weight ready from Serial scale (COM3).',
        scale_setup_hint: 'Use the refreshed live weight in the counter workflow if the item is sold loose.',
        cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
        cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
        scanner_status_message: 'Ready for external scanner input',
        scanner_setup_hint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
      },
    });

    expect(invoke).toHaveBeenNthCalledWith(4, 'cmd_read_store_runtime_scale_weight');

    await expect(
      adapter.recordScannerActivity({
        barcode_preview: 'ACMETEA',
        scanner_transport: 'usb_hid',
      }),
    ).resolves.toEqual({
      bridge_state: 'ready',
      scales: [
        {
          id: 'scale-com3',
          label: 'Serial scale (COM3)',
          transport: 'serial_com',
          port_name: 'COM3',
          is_connected: true,
        },
      ],
      scanners: [
        {
          id: 'scanner-zebra-1',
          label: 'Zebra DS2208',
          transport: 'usb_hid',
          vendor_name: 'Zebra',
          product_name: 'DS2208',
          serial_number: 'ZB-001',
          is_connected: true,
        },
      ],
      printers: [],
      profile: {
        receipt_printer_name: 'Thermal-01',
        label_printer_name: null,
        cash_drawer_printer_name: 'Thermal-01',
        preferred_scale_id: 'scale-com3',
        preferred_scanner_id: 'scanner-zebra-1',
        updated_at: '2026-04-14T16:05:00.000Z',
      },
      diagnostics: {
        scale_capture_state: 'ready',
        scanner_capture_state: 'ready',
        scanner_transport: 'usb_hid',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: null,
        last_cash_drawer_message: null,
        last_cash_drawer_opened_at: null,
        last_weight_value: 0.5,
        last_weight_unit: 'kg',
        last_weight_status: 'captured',
        last_weight_message: 'Captured 0.500 kg from Serial scale (COM3)',
        last_weight_read_at: '2026-04-15T12:00:00.000Z',
        last_scan_at: '2026-04-15T12:00:00.000Z',
        last_scan_barcode_preview: 'ACMETEA',
        scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
        scale_setup_hint: 'Use the hardware desk to refresh the live weight before weighing a loose item.',
        cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
        cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
        scanner_status_message: 'Preferred HID scanner connected: Zebra DS2208',
        scanner_setup_hint: 'Scan into the active packaged terminal to keep HID activity diagnostics current.',
      },
    });

    expect(invoke).toHaveBeenNthCalledWith(5, 'cmd_record_store_runtime_scanner_activity', {
      barcode_preview: 'ACMETEA',
      scanner_transport: 'usb_hid',
    });
  });

  test('falls back to unavailable hardware status in the web shell', async () => {
    const adapter = createResolvedStoreRuntimeHardware({
      isNativeRuntime: () => false,
    });

    await expect(adapter.getStatus()).resolves.toEqual({
      bridge_state: 'browser_fallback',
      scales: [],
      scanners: [],
      printers: [],
      profile: {
        receipt_printer_name: null,
        label_printer_name: null,
        cash_drawer_printer_name: null,
        preferred_scale_id: null,
        preferred_scanner_id: null,
        updated_at: null,
      },
      diagnostics: {
        scale_capture_state: 'browser_fallback',
        scanner_capture_state: 'browser_fallback',
        scanner_transport: 'unknown',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: null,
        last_cash_drawer_message: null,
        last_cash_drawer_opened_at: null,
        last_weight_value: null,
        last_weight_unit: null,
        last_weight_status: null,
        last_weight_message: null,
        last_weight_read_at: null,
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Weighing scale support requires the packaged desktop runtime.',
        scale_setup_hint: 'Open the packaged desktop runtime to assign and read a local serial scale.',
        cash_drawer_status_message: 'Cash drawer controls require the packaged desktop runtime.',
        cash_drawer_setup_hint: 'Open the packaged desktop runtime to assign a local printer-backed cash drawer.',
        scanner_status_message: 'Scanner capture diagnostics require the packaged desktop runtime.',
        scanner_setup_hint: 'Open the packaged desktop runtime for wedge-scanner capture.',
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
      scales: [],
      scanners: [],
      printers: [],
      profile: {
        receipt_printer_name: null,
        label_printer_name: null,
        cash_drawer_printer_name: null,
        preferred_scale_id: null,
        preferred_scanner_id: null,
        updated_at: null,
      },
      diagnostics: {
        scale_capture_state: 'browser_fallback',
        scanner_capture_state: 'browser_fallback',
        scanner_transport: 'unknown',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_cash_drawer_status: null,
        last_cash_drawer_message: null,
        last_cash_drawer_opened_at: null,
        last_weight_value: null,
        last_weight_unit: null,
        last_weight_status: null,
        last_weight_message: null,
        last_weight_read_at: null,
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Weighing scale support requires the packaged desktop runtime.',
        scale_setup_hint: 'Open the packaged desktop runtime to assign and read a local serial scale.',
        cash_drawer_status_message: 'Cash drawer controls require the packaged desktop runtime.',
        cash_drawer_setup_hint: 'Open the packaged desktop runtime to assign a local printer-backed cash drawer.',
        scanner_status_message: 'Scanner capture diagnostics require the packaged desktop runtime.',
        scanner_setup_hint: 'Open the packaged desktop runtime for wedge-scanner capture.',
      },
    });
  });
});
