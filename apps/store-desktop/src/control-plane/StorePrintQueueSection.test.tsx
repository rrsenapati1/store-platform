/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StorePrintQueueSection } from './StorePrintQueueSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    selectedRuntimeDeviceId: 'device-1',
    setSelectedRuntimeDeviceId: vi.fn(),
    runtimeDevices: [
      {
        id: 'device-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_code: 'STORE-DEVICE-1',
        device_name: 'Counter 1',
        status: 'ONLINE',
        last_seen_at: null,
        last_heartbeat_at: null,
        metadata: {},
      },
    ],
    queueLatestInvoicePrint: vi.fn(async () => {}),
    queueLatestCreditNotePrint: vi.fn(async () => {}),
    heartbeatRuntimeDevice: vi.fn(async () => {}),
    refreshPrintQueue: vi.fn(async () => {}),
    completeFirstPrintJob: vi.fn(async () => {}),
    assignRuntimeReceiptPrinter: vi.fn(async () => {}),
    assignRuntimeLabelPrinter: vi.fn(async () => {}),
    assignRuntimeCashDrawerPrinter: vi.fn(async () => {}),
    assignRuntimePreferredScale: vi.fn(async () => {}),
    openRuntimeCashDrawer: vi.fn(async () => {}),
    readRuntimeScaleWeight: vi.fn(async () => {}),
    runtimeShellKind: 'packaged_desktop',
    runtimeHardwareBridgeState: 'ready',
    runtimeReceiptPrinterName: 'Thermal-01',
    runtimeLabelPrinterName: 'Label-01',
    runtimeCashDrawerPrinterName: 'Thermal-01',
    runtimePreferredScaleId: 'scale-com3',
    runtimeScaleCaptureState: 'ready',
    runtimeScaleStatusMessage: 'Preferred scale ready: Serial scale (COM3).',
    runtimeScaleSetupHint: 'Connect a local serial/COM scale and assign it before requesting a live read.',
    runtimeScaleLastWeightValue: 0.5,
    runtimeScaleLastWeightUnit: 'kg',
    runtimeScaleLastWeightReadAt: '2026-04-15T12:10:00.000Z',
    runtimeCashDrawerStatusMessage: 'Cash drawer is assigned to Thermal-01.',
    runtimeCashDrawerSetupHint: 'Use a receipt printer with a connected RJ11 cash drawer.',
    runtimeHardwareLastCashDrawerMessage: 'Opened cash drawer through Thermal-01',
    runtimeHardwareLastCashDrawerOpenedAt: '2026-04-15T12:05:00.000Z',
    runtimeHardwareLastPrintMessage: 'Printed SALES_INVOICE on Thermal-01',
    runtimeHardwarePrinters: [
      {
        name: 'Thermal-01',
        label: 'Thermal-01',
        is_default: true,
        is_online: true,
      },
      {
        name: 'Thermal-02',
        label: 'Thermal-02',
        is_default: false,
        is_online: true,
      },
    ],
    runtimeHardwareScales: [
      {
        id: 'scale-com3',
        label: 'Serial scale (COM3)',
        transport: 'serial_com',
        port_name: 'COM3',
        is_connected: true,
      },
      {
        id: 'scale-com4',
        label: 'Serial scale (COM4)',
        transport: 'serial_com',
        port_name: 'COM4',
        is_connected: true,
      },
    ],
    runtimeHardwareError: null,
    runtimeHeartbeat: null,
    latestPrintJob: null,
    printJobs: [],
    isBusy: false,
    isSessionLive: true,
    latestSale: { id: 'sale-1' },
    latestSaleReturn: null,
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store print queue section', () => {
  test('renders cash drawer and scale controls for packaged runtime', () => {
    render(<StorePrintQueueSection workspace={buildWorkspace()} />);

    expect(screen.getByText('Cash drawer')).toBeInTheDocument();
    expect(screen.getAllByText('Thermal-01').length).toBeGreaterThan(0);
    expect(screen.getByText('Cash drawer is assigned to Thermal-01.')).toBeInTheDocument();
    expect(screen.getByText('Opened cash drawer through Thermal-01')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open assigned cash drawer' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Use for cash drawer' })).toHaveLength(2);
    expect(screen.getByText('Weighing scale')).toBeInTheDocument();
    expect(screen.getByText('Preferred scale ready: Serial scale (COM3).')).toBeInTheDocument();
    expect(screen.getByText('0.5 kg')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Read current weight' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Use for weighing scale' })).toHaveLength(2);
  });
});
