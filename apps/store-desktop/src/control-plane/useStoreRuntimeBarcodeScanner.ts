import { parseHidBuffer } from '@store/barcode';
import { useEffect, useEffectEvent, useRef, useState } from 'react';

const SCANNER_INTER_KEY_TIMEOUT_MS = 80;

function isScannerCaptureActive(args: {
  runtimeShellKind: string | null;
  isSessionLive: boolean;
  isLocalUnlocked: boolean;
}) {
  return args.runtimeShellKind === 'packaged_desktop' && args.isSessionLive && args.isLocalUnlocked;
}

function isIgnoredKeyboardKey(key: string) {
  return key === 'Shift' || key === 'CapsLock' || key === 'Tab';
}

function buildScannerDiagnostics(args: {
  runtimeShellKind: string | null;
  isSessionLive: boolean;
  isLocalUnlocked: boolean;
  hardwareScannerCaptureState?: 'ready' | 'unavailable' | 'browser_fallback' | 'attention_required';
  hardwareScannerTransport?: 'keyboard_wedge' | 'usb_hid' | 'bluetooth_hid' | 'unknown';
  hardwareScannerStatusMessage?: string | null;
  hardwareScannerSetupHint?: string | null;
  lastScanAt: string | null;
  lastScanBarcodePreview: string | null;
}) {
  if (args.runtimeShellKind !== 'packaged_desktop') {
    return {
      scannerCaptureState: 'browser_fallback' as const,
      scannerTransport: 'unknown' as const,
      scannerStatusMessage: 'Scanner capture diagnostics require the packaged desktop runtime.',
      scannerSetupHint: 'Open the packaged desktop runtime for wedge-scanner capture.',
      lastScanAt: args.lastScanAt,
      lastScanBarcodePreview: args.lastScanBarcodePreview,
    };
  }

  if (!args.isSessionLive || !args.isLocalUnlocked) {
    return {
      scannerCaptureState: 'unavailable' as const,
      scannerTransport: 'keyboard_wedge' as const,
      scannerStatusMessage: 'Scanner capture is unavailable until the packaged desktop is live and locally unlocked.',
      scannerSetupHint: 'Unlock the packaged terminal and keep the cashier session live before scanning.',
      lastScanAt: args.lastScanAt,
      lastScanBarcodePreview: args.lastScanBarcodePreview,
    };
  }

  if (args.hardwareScannerCaptureState && args.hardwareScannerCaptureState !== 'browser_fallback') {
    return {
      scannerCaptureState: args.hardwareScannerCaptureState,
      scannerTransport: args.hardwareScannerTransport ?? 'unknown',
      scannerStatusMessage: args.hardwareScannerStatusMessage ?? 'No scanner diagnostics available',
      scannerSetupHint: args.hardwareScannerSetupHint ?? 'No scanner setup guidance available',
      lastScanAt: args.lastScanAt,
      lastScanBarcodePreview: args.lastScanBarcodePreview,
    };
  }

  return {
    scannerCaptureState: 'ready' as const,
    scannerTransport: 'keyboard_wedge' as const,
    scannerStatusMessage: 'Ready for external scanner input',
    scannerSetupHint: 'Connect a keyboard-wedge scanner and scan into the active packaged terminal.',
    lastScanAt: args.lastScanAt,
    lastScanBarcodePreview: args.lastScanBarcodePreview,
  };
}

export function useStoreRuntimeBarcodeScanner(args: {
  runtimeShellKind: string | null;
  isSessionLive: boolean;
  isLocalUnlocked: boolean;
  hardwareScannerCaptureState?: 'ready' | 'unavailable' | 'browser_fallback' | 'attention_required';
  hardwareScannerTransport?: 'keyboard_wedge' | 'usb_hid' | 'bluetooth_hid' | 'unknown';
  hardwareScannerStatusMessage?: string | null;
  hardwareScannerSetupHint?: string | null;
  onScannerActivityRecorded?: (activity: {
    barcode_preview: string;
    scanner_transport: 'keyboard_wedge' | 'usb_hid' | 'bluetooth_hid' | 'unknown' | null;
  }) => void;
  onBarcodeDetected: (barcode: string) => void;
}) {
  const [lastScanAt, setLastScanAt] = useState<string | null>(null);
  const [lastScanBarcodePreview, setLastScanBarcodePreview] = useState<string | null>(null);
  const bufferRef = useRef<string[]>([]);
  const clearBufferTimeoutRef = useRef<number | null>(null);
  const applyBarcodeDetected = useEffectEvent(args.onBarcodeDetected);
  const applyScannerActivityRecorded = useEffectEvent(args.onScannerActivityRecorded ?? (() => {}));

  useEffect(() => {
    if (!isScannerCaptureActive(args)) {
      return;
    }

    const clearBuffer = () => {
      bufferRef.current = [];
      if (clearBufferTimeoutRef.current !== null) {
        window.clearTimeout(clearBufferTimeoutRef.current);
        clearBufferTimeoutRef.current = null;
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) {
        return;
      }
      if (isIgnoredKeyboardKey(event.key)) {
        return;
      }

      if (event.key === 'Enter') {
        if (bufferRef.current.length === 0) {
          return;
        }
        const barcode = parseHidBuffer([...bufferRef.current, 'Enter']);
        clearBuffer();
        if (!barcode) {
          return;
        }
        const detectedAt = new Date().toISOString();
        setLastScanAt(detectedAt);
        setLastScanBarcodePreview(barcode.slice(0, 16));
        applyScannerActivityRecorded({
          barcode_preview: barcode.slice(0, 16),
          scanner_transport: args.hardwareScannerTransport ?? 'keyboard_wedge',
        });
        applyBarcodeDetected(barcode);
        return;
      }

      if (event.key.length !== 1) {
        clearBuffer();
        return;
      }

      bufferRef.current.push(event.key);
      if (clearBufferTimeoutRef.current !== null) {
        window.clearTimeout(clearBufferTimeoutRef.current);
      }
      clearBufferTimeoutRef.current = window.setTimeout(() => {
        bufferRef.current = [];
        clearBufferTimeoutRef.current = null;
      }, SCANNER_INTER_KEY_TIMEOUT_MS);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearBuffer();
    };
  }, [args, applyBarcodeDetected]);

  const diagnostics = buildScannerDiagnostics({
    runtimeShellKind: args.runtimeShellKind,
    isSessionLive: args.isSessionLive,
    isLocalUnlocked: args.isLocalUnlocked,
    hardwareScannerCaptureState: args.hardwareScannerCaptureState,
    hardwareScannerTransport: args.hardwareScannerTransport,
    hardwareScannerStatusMessage: args.hardwareScannerStatusMessage,
    hardwareScannerSetupHint: args.hardwareScannerSetupHint,
    lastScanAt,
    lastScanBarcodePreview,
  });

  return {
    scannerCaptureState: diagnostics.scannerCaptureState,
    scannerTransport: diagnostics.scannerTransport,
    scannerStatusMessage: diagnostics.scannerStatusMessage,
    scannerSetupHint: diagnostics.scannerSetupHint,
    lastScanAt: diagnostics.lastScanAt,
    lastScanBarcodePreview: diagnostics.lastScanBarcodePreview,
  };
}
