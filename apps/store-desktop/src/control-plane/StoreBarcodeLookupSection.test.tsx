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
    runtimeScannerCaptureState: 'ready',
    runtimeScannerLastScanAt: '2026-04-15T12:00:00.000Z',
    runtimeScannerTransport: 'keyboard_wedge',
    runtimeScannerStatusMessage: 'Ready for external scanner input',
    runtimeScannerSetupHint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
    runtimeScannerLastScanPreview: 'ACMETEA',
    latestScanLookup: null,
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('store barcode lookup section', () => {
  test('renders compact scanner diagnostics for packaged runtime', () => {
    render(<StoreBarcodeLookupSection workspace={buildWorkspace()} />);

    expect(screen.getByText('Scanner diagnostics')).toBeInTheDocument();
    expect(screen.getByText('keyboard_wedge')).toBeInTheDocument();
    expect(screen.getByText('ACMETEA')).toBeInTheDocument();
    expect(screen.getByText('Ready for external scanner input')).toBeInTheDocument();
  });
});
