/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { useState } from 'react';
import type { ControlPlanePrintJob } from '@store/types';

const { tauriState, dispatches, mockInvoke } = vi.hoisted(() => ({
  tauriState: {
    hardwareStatus: {
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
        label_printer_name: 'Label-01',
        updated_at: '2026-04-14T16:00:00.000Z',
      },
      diagnostics: {
        scanner_capture_state: 'ready',
        last_print_status: null,
        last_print_message: null,
        last_printed_at: null,
        last_scan_at: null,
      },
    },
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

    expect(screen.getByTestId('error-message')).toHaveTextContent('none');
    expect(dispatches).toHaveLength(1);
  });
});
