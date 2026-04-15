/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreBarcodeLookupSection } from './StoreBarcodeLookupSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    scannedBarcode: '',
    setScannedBarcode: vi.fn(),
    lookupScannedBarcode: vi.fn(async () => {}),
    isBusy: false,
    isSessionLive: true,
    runtimeShellKind: 'packaged_desktop',
    runtimeScaleCaptureState: 'ready',
    runtimeScaleStatusMessage: 'Preferred scale ready: Serial scale (COM3).',
    runtimeScaleSetupHint: 'Connect a local serial/COM scale and assign it before requesting a live read.',
    runtimeScaleLastWeightValue: 0.5,
    runtimeScaleLastWeightUnit: 'kg',
    runtimeScaleLastWeightReadAt: '2026-04-15T12:10:00.000Z',
    runtimeScannerCaptureState: 'ready',
    runtimeScannerLastScanAt: '2026-04-15T12:00:00.000Z',
    runtimeScannerTransport: 'keyboard_wedge',
    runtimeScannerStatusMessage: 'Ready for external scanner input',
    runtimeScannerSetupHint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
    runtimeScannerLastScanPreview: 'ACMETEA',
    runtimePreferredScannerId: 'scanner-zebra-1',
    runtimeHardwareScanners: [
      {
        id: 'scanner-zebra-1',
        label: 'Zebra DS2208',
        transport: 'usb_hid',
        vendor_name: 'Zebra',
        product_name: 'DS2208',
        serial_number: 'ZB-001',
        is_connected: true,
      },
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
    runtimePreferredScaleId: 'scale-com3',
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
    assignRuntimePreferredScale: vi.fn(async () => {}),
    readRuntimeScaleWeight: vi.fn(async () => {}),
    assignRuntimePreferredScanner: vi.fn(async () => {}),
    latestScanLookup: null,
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store barcode lookup section', () => {
  test('renders compact scanner and scale diagnostics for packaged runtime', () => {
    render(<StoreBarcodeLookupSection workspace={buildWorkspace()} />);

    expect(screen.getByText('Scale diagnostics')).toBeInTheDocument();
    expect(screen.getByText('Preferred scale ready: Serial scale (COM3).')).toBeInTheDocument();
    expect(screen.getByText('0.5 kg')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Read current weight' })).toBeInTheDocument();
    expect(screen.getByText('Scanner diagnostics')).toBeInTheDocument();
    expect(screen.getByText('keyboard_wedge')).toBeInTheDocument();
    expect(screen.getByText('ACMETEA')).toBeInTheDocument();
    expect(screen.getByText('Ready for external scanner input')).toBeInTheDocument();
    expect(screen.getByText('Discovered local scales')).toBeInTheDocument();
    expect(screen.getAllByText('Serial scale (COM3)').length).toBeGreaterThan(0);
    expect(screen.getByText('Serial scale (COM4)')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Use as preferred scale' })).toHaveLength(2);
    expect(screen.getByRole('button', { name: 'Clear preferred scale' })).toBeInTheDocument();
    expect(screen.getByText('Discovered local scanners')).toBeInTheDocument();
    expect(screen.getByText('Zebra DS2208')).toBeInTheDocument();
    expect(screen.getByText('Socket Mobile S740')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Use as preferred scanner' })).toHaveLength(2);
    expect(screen.getByRole('button', { name: 'Clear preferred scanner' })).toBeInTheDocument();
  });
});
