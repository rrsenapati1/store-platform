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

export function useStoreRuntimeBarcodeScanner(args: {
  runtimeShellKind: string | null;
  isSessionLive: boolean;
  isLocalUnlocked: boolean;
  onBarcodeDetected: (barcode: string) => void;
}) {
  const [lastScanAt, setLastScanAt] = useState<string | null>(null);
  const bufferRef = useRef<string[]>([]);
  const clearBufferTimeoutRef = useRef<number | null>(null);
  const applyBarcodeDetected = useEffectEvent(args.onBarcodeDetected);

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

  return {
    scannerCaptureState: isScannerCaptureActive(args)
      ? 'ready'
      : args.runtimeShellKind === 'packaged_desktop'
        ? 'unavailable'
        : 'browser_fallback',
    lastScanAt,
  };
}
