/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { useState } from 'react';
import { useStoreRuntimeBarcodeScanner } from './useStoreRuntimeBarcodeScanner';

function BarcodeScannerHarness() {
  const [barcode, setBarcode] = useState('');
  const scanner = useStoreRuntimeBarcodeScanner({
    runtimeShellKind: 'packaged_desktop',
    isSessionLive: true,
    isLocalUnlocked: true,
    onBarcodeDetected: setBarcode,
  });

  return (
    <>
      <div data-testid="scanner-state">{scanner.scannerCaptureState}</div>
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
