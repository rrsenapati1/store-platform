/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { useState } from 'react';
import type { ControlPlanePrintJob } from '@store/types';
import type { StoreRuntimeHardwareStatus } from '../runtime-hardware/storeRuntimeHardware';

const { tauriState, dispatches, mockInvoke } = vi.hoisted(() => ({
  tauriState: {
    hardwareStatus: {
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
        label_printer_name: 'Label-01',
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
        last_weight_read_at: '2026-04-15T12:10:00.000Z',
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
        scale_setup_hint: 'Connect a local serial/COM scale and assign it before requesting a live read.',
        cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
        cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
        scanner_status_message: 'Preferred HID scanner connected: Zebra DS2208',
        scanner_setup_hint: 'Scan into the active packaged terminal to keep HID activity diagnostics current.',
      },
    } as StoreRuntimeHardwareStatus,
  },
  dispatches: [] as Array<Record<string, unknown>>,
  mockInvoke: vi.fn(async (command: string, payload?: Record<string, unknown>) => {
    if (command === 'cmd_get_store_runtime_hardware_status') {
      return tauriState.hardwareStatus;
    }
    if (command === 'cmd_dispatch_store_runtime_print_job') {
      dispatches.push(payload ?? {});
      tauriState.hardwareStatus = {
        ...tauriState.hardwareStatus,
        diagnostics: {
          ...tauriState.hardwareStatus.diagnostics,
          last_print_status: 'completed',
          last_print_message: 'Printed SALES_INVOICE on Thermal-01',
          last_printed_at: '2026-04-14T16:05:00.000Z',
        },
      };
      return tauriState.hardwareStatus;
    }
    throw new Error(`Unexpected command: ${command}`);
  }),
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: mockInvoke,
}));

import { useStoreRuntimeHardwareIntegration } from './useStoreRuntimeHardwareIntegration';

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

function HardwareHarness() {
  const [printJobs, setPrintJobs] = useState<ControlPlanePrintJob[]>([]);
  const [latestPrintJob, setLatestPrintJob] = useState<ControlPlanePrintJob | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const hardware = useStoreRuntimeHardwareIntegration({
    runtimeShellKind: 'packaged_desktop',
    accessToken: 'session-cashier',
    tenantId: 'tenant-acme',
    branchId: 'branch-1',
    selectedRuntimeDeviceId: 'device-1',
    isSessionLive: true,
    isLocalUnlocked: true,
    pollIntervalMs: 20,
    onPrintJobsChange: setPrintJobs,
    onLatestPrintJobChange: setLatestPrintJob,
    onErrorMessage: setErrorMessage,
  });

  return (
    <>
      <div data-testid="bridge-state">{hardware.hardwareStatus?.bridge_state ?? 'missing'}</div>
      <div data-testid="print-count">{String(printJobs.length)}</div>
      <div data-testid="latest-status">{latestPrintJob?.status ?? 'none'}</div>
      <div data-testid="last-print-message">{hardware.hardwareStatus?.diagnostics.last_print_message ?? 'none'}</div>
      <div data-testid="scanner-transport">{hardware.hardwareStatus?.diagnostics.scanner_transport ?? 'none'}</div>
      <div data-testid="scanner-status-message">{hardware.hardwareStatus?.diagnostics.scanner_status_message ?? 'none'}</div>
      <div data-testid="error-message">{errorMessage || 'none'}</div>
    </>
  );
}

describe('packaged runtime hardware integration', () => {
  const originalFetch = globalThis.fetch;
  const originalTauriInternals = (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__;

  beforeEach(() => {
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = {};
    dispatches.length = 0;
    tauriState.hardwareStatus = {
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
        label_printer_name: 'Label-01',
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
        last_weight_read_at: '2026-04-15T12:10:00.000Z',
        last_scan_at: null,
        last_scan_barcode_preview: null,
        scale_status_message: 'Preferred scale ready: Serial scale (COM3).',
        scale_setup_hint: 'Connect a local serial/COM scale and assign it before requesting a live read.',
        cash_drawer_status_message: 'Cash drawer is assigned to Thermal-01.',
        cash_drawer_setup_hint: 'Open the assigned cash drawer only after a cashier confirms the sale state.',
        scanner_status_message: 'Preferred HID scanner connected: Zebra DS2208',
        scanner_setup_hint: 'Scan into the active packaged terminal to keep HID activity diagnostics current.',
      },
    };

    let isQueueCleared = false;

    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/runtime/devices/device-1/print-jobs') && (!init?.method || init.method === 'GET')) {
        return jsonResponse(
          isQueueCleared
            ? { records: [] }
            : {
                records: [
                  {
                    id: 'print-job-1',
                    tenant_id: 'tenant-acme',
                    branch_id: 'branch-1',
                    device_id: 'device-1',
                    job_type: 'SALES_INVOICE',
                    copies: 1,
                    status: 'QUEUED',
                    failure_reason: null,
                    payload: {
                      document_number: 'SINV-0001',
                      receipt_lines: ['STORE TAX INVOICE', 'Grand Total: 388.50'],
                    },
                  },
                ],
              },
        ) as never;
      }
      if (url.includes('/runtime/devices/device-1/print-jobs/print-job-1/complete')) {
        isQueueCleared = true;
        return jsonResponse({
          id: 'print-job-1',
          tenant_id: 'tenant-acme',
          branch_id: 'branch-1',
          device_id: 'device-1',
          job_type: 'SALES_INVOICE',
          copies: 1,
          status: 'COMPLETED',
          failure_reason: null,
          payload: {
            document_number: 'SINV-0001',
            receipt_lines: ['STORE TAX INVOICE', 'Grand Total: 388.50'],
          },
        }) as never;
      }
      throw new Error(`Unexpected fetch call: ${url}`);
    }) as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    (window as Window & { __TAURI_INTERNALS__?: object }).__TAURI_INTERNALS__ = originalTauriInternals;
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('polls queued print jobs and auto-completes them through the native bridge', async () => {
    render(<HardwareHarness />);

    expect(await screen.findByTestId('bridge-state')).toHaveTextContent('ready');

    await waitFor(() => {
      expect(screen.getByTestId('latest-status')).toHaveTextContent('COMPLETED');
      expect(screen.getByTestId('last-print-message')).toHaveTextContent('Printed SALES_INVOICE on Thermal-01');
    });

    expect(screen.getByTestId('scanner-transport')).toHaveTextContent('usb_hid');
    expect(screen.getByTestId('scanner-status-message')).toHaveTextContent('Preferred HID scanner connected: Zebra DS2208');
    expect(screen.getByTestId('error-message')).toHaveTextContent('none');
    expect(dispatches).toHaveLength(1);
  });
});
