/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { useState } from 'react';
import { useStoreRuntimeBarcodeScanner } from './useStoreRuntimeBarcodeScanner';

function BarcodeScannerHarness(props: {
  hardwareScannerCaptureState?: 'ready' | 'attention_required' | 'unavailable' | 'browser_fallback';
  hardwareScannerTransport?: 'keyboard_wedge' | 'usb_hid' | 'bluetooth_hid' | 'unknown';
  hardwareScannerStatusMessage?: string | null;
  hardwareScannerSetupHint?: string | null;
  onScannerActivityRecorded?: (activity: { barcode_preview: string; scanner_transport: string | null }) => void;
} = {}) {
  const [barcode, setBarcode] = useState('');
  const scanner = useStoreRuntimeBarcodeScanner({
    runtimeShellKind: 'packaged_desktop',
    isSessionLive: true,
    isLocalUnlocked: true,
    hardwareScannerCaptureState: props.hardwareScannerCaptureState ?? 'ready',
    hardwareScannerTransport: props.hardwareScannerTransport ?? 'keyboard_wedge',
    hardwareScannerStatusMessage: props.hardwareScannerStatusMessage ?? 'Ready for external scanner input',
    hardwareScannerSetupHint: props.hardwareScannerSetupHint ?? 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
    onScannerActivityRecorded: props.onScannerActivityRecorded,
    onBarcodeDetected: setBarcode,
  });

  return (
    <>
      <div data-testid="scanner-state">{scanner.scannerCaptureState}</div>
      <div data-testid="scanner-transport">{scanner.scannerTransport ?? 'none'}</div>
      <div data-testid="scanner-status-message">{scanner.scannerStatusMessage ?? 'none'}</div>
      <div data-testid="scanner-setup-hint">{scanner.scannerSetupHint ?? 'none'}</div>
      <div data-testid="barcode-preview">{scanner.lastScanBarcodePreview ?? 'none'}</div>
      <div data-testid="last-scan">{scanner.lastScanAt ?? 'none'}</div>
      <div data-testid="barcode">{barcode || 'none'}</div>
    </>
  );
}

describe('packaged runtime barcode scanner capture', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  test('captures a fast keyboard-wedge scan ending with enter', async () => {
    render(<BarcodeScannerHarness />);

    expect(screen.getByTestId('scanner-state')).toHaveTextContent('ready');

    fireEvent.keyDown(window, { key: 'A' });
    fireEvent.keyDown(window, { key: 'C' });
    fireEvent.keyDown(window, { key: 'M' });
    fireEvent.keyDown(window, { key: 'E' });
    fireEvent.keyDown(window, { key: 'T' });
    fireEvent.keyDown(window, { key: 'E' });
    fireEvent.keyDown(window, { key: 'A' });
    fireEvent.keyDown(window, { key: 'Enter' });

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByTestId('barcode')).toHaveTextContent('ACMETEA');
    expect(screen.getByTestId('last-scan')).not.toHaveTextContent('none');
    expect(screen.getByTestId('scanner-transport')).toHaveTextContent('keyboard_wedge');
    expect(screen.getByTestId('barcode-preview')).toHaveTextContent('ACMETEA');
    expect(screen.getByTestId('scanner-status-message')).toHaveTextContent('Ready for external scanner input');
  });

  test('prefers native hid diagnostics and publishes accepted scan activity', async () => {
    const onScannerActivityRecorded = vi.fn();

    render(
      <BarcodeScannerHarness
        hardwareScannerCaptureState="attention_required"
        hardwareScannerTransport="usb_hid"
        hardwareScannerStatusMessage="Preferred HID scanner not connected"
        hardwareScannerSetupHint="Reconnect the preferred scanner or choose a different local scanner."
        onScannerActivityRecorded={onScannerActivityRecorded}
      />,
    );

    expect(screen.getByTestId('scanner-state')).toHaveTextContent('attention_required');
    expect(screen.getByTestId('scanner-transport')).toHaveTextContent('usb_hid');
    expect(screen.getByTestId('scanner-status-message')).toHaveTextContent('Preferred HID scanner not connected');

    fireEvent.keyDown(window, { key: 'A' });
    fireEvent.keyDown(window, { key: 'C' });
    fireEvent.keyDown(window, { key: 'M' });
    fireEvent.keyDown(window, { key: 'E' });
    fireEvent.keyDown(window, { key: 'Enter' });

    await act(async () => {
      await Promise.resolve();
    });

    expect(onScannerActivityRecorded).toHaveBeenCalledWith({
      barcode_preview: 'ACME',
      scanner_transport: 'usb_hid',
    });
  });

  test('ignores ordinary slow typing cadence', async () => {
    render(<BarcodeScannerHarness />);

    fireEvent.keyDown(window, { key: 'A' });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });
    fireEvent.keyDown(window, { key: 'B' });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });
    fireEvent.keyDown(window, { key: 'Enter' });

    expect(screen.getByTestId('barcode')).toHaveTextContent('none');
  });
});
