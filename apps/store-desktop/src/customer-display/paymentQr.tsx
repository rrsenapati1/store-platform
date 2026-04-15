import { useEffect, useMemo, useState } from 'react';
import * as QRCode from 'qrcode';

function buildQrImageSource(value: string) {
  let svgMarkup = '';

  QRCode.toString(
    value,
    {
      errorCorrectionLevel: 'M',
      margin: 1,
      type: 'svg',
      width: 320,
      color: {
        dark: '#0f172a',
        light: '#ffffff',
      },
    },
    (error, output) => {
      if (error) {
        throw error;
      }
      svgMarkup = output;
    },
  );

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgMarkup)}`;
}

function formatDurationParts(totalSeconds: number) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}

export function formatPaymentQrExpiry(expiresAt: string | null, now: Date = new Date()) {
  if (!expiresAt) {
    return 'Expiry unavailable';
  }

  const expiresAtDate = new Date(expiresAt);
  if (Number.isNaN(expiresAtDate.getTime())) {
    return 'Expiry unavailable';
  }

  const deltaSeconds = Math.ceil((expiresAtDate.getTime() - now.getTime()) / 1000);
  if (deltaSeconds <= 0) {
    return 'Expired';
  }

  return `Expires in ${formatDurationParts(deltaSeconds)}`;
}

export function usePaymentQrExpiry(expiresAt: string | null) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    if (!expiresAt) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setNow(new Date());
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [expiresAt]);

  return formatPaymentQrExpiry(expiresAt, now);
}

export function PaymentQrCode({
  value,
  alt,
  size = 240,
}: {
  value: string;
  alt: string;
  size?: number;
}) {
  const source = useMemo(() => buildQrImageSource(value), [value]);

  return (
    <img
      alt={alt}
      src={source}
      width={size}
      height={size}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '20px',
        background: '#ffffff',
        padding: '14px',
        boxSizing: 'border-box',
        boxShadow: '0 14px 32px rgba(15, 23, 42, 0.16)',
      }}
    />
  );
}
