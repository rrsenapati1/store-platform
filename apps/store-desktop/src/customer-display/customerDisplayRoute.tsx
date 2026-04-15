import { useEffect, useState } from 'react';
import {
  buildIdleCustomerDisplayPayload,
  getCustomerDisplayStorageEventName,
  getCustomerDisplayStorageKey,
  loadCustomerDisplayPayload,
  type CustomerDisplayPayload,
} from './customerDisplayModel';
import { PaymentQrCode, usePaymentQrExpiry } from './paymentQr';

function formatAmount(value: number | null) {
  if (value === null) {
    return '--';
  }
  return value.toFixed(2);
}

function ToneBar({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'grid', gap: '6px' }}>
      <span style={{ fontSize: '12px', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#d1d8f0' }}>{label}</span>
      <strong style={{ fontSize: '22px', color: '#f5f7ff' }}>{value}</strong>
    </div>
  );
}

function useCustomerDisplayPayload() {
  const [payload, setPayload] = useState<CustomerDisplayPayload>(() => (
    loadCustomerDisplayPayload() ?? buildIdleCustomerDisplayPayload(null)
  ));

  useEffect(() => {
    const handleLocalPayload = (event: Event) => {
      const detail = (event as CustomEvent<CustomerDisplayPayload | null>).detail;
      setPayload(detail ?? buildIdleCustomerDisplayPayload(null));
    };
    const handleStorage = (event: StorageEvent) => {
      if (event.key !== getCustomerDisplayStorageKey()) {
        return;
      }
      setPayload(loadCustomerDisplayPayload() ?? buildIdleCustomerDisplayPayload(null));
    };

    window.addEventListener(getCustomerDisplayStorageEventName(), handleLocalPayload as EventListener);
    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener(getCustomerDisplayStorageEventName(), handleLocalPayload as EventListener);
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  return payload;
}

export function isCustomerDisplayRoute() {
  if (typeof window === 'undefined') {
    return false;
  }
  const params = new URLSearchParams(window.location.search);
  return params.get('customer-display') === '1';
}

export function CustomerDisplayRoute() {
  const payload = useCustomerDisplayPayload();
  const paymentQrExpiry = usePaymentQrExpiry(payload.payment_qr?.expires_at ?? null);

  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateRows: 'auto 1fr auto',
        gap: '28px',
        padding: '32px',
        background: 'radial-gradient(circle at top, #1f2b54 0%, #090c16 58%, #05060b 100%)',
        color: '#ffffff',
        fontFamily: '"Segoe UI", "Helvetica Neue", sans-serif',
      }}
    >
      <section style={{ display: 'grid', gap: '10px' }}>
        <span style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.18em', color: '#7ae0ff' }}>
          Store customer display
        </span>
        <h1 style={{ margin: 0, fontSize: '48px', lineHeight: 1.05 }}>{payload.title}</h1>
        <p style={{ margin: 0, fontSize: '20px', color: '#d9def3' }}>{payload.message}</p>
      </section>

      <section
        style={{
          display: 'grid',
          gridTemplateColumns: '1.6fr 1fr',
          gap: '24px',
          alignItems: 'stretch',
        }}
      >
        <div
          style={{
            borderRadius: '28px',
            padding: '24px',
            background: 'rgba(17, 22, 37, 0.84)',
            border: '1px solid rgba(122, 224, 255, 0.16)',
            display: 'grid',
            gap: '18px',
            alignContent: 'start',
          }}
        >
          {payload.line_items.length ? payload.line_items.map((item) => (
            <div
              key={`${item.label}:${item.quantity}:${item.amount}`}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto',
                gap: '12px',
                paddingBottom: '14px',
                borderBottom: '1px solid rgba(209, 216, 240, 0.12)',
              }}
            >
              <div style={{ display: 'grid', gap: '6px' }}>
                <strong style={{ fontSize: '28px', color: '#f8fbff' }}>{item.label}</strong>
                <span style={{ fontSize: '16px', color: '#b6c1e0' }}>Qty {item.quantity}</span>
              </div>
              <strong style={{ fontSize: '30px', color: '#7ae0ff' }}>{formatAmount(item.amount)}</strong>
            </div>
          )) : (
            <div
              style={{
                alignSelf: 'center',
                padding: '36px 20px',
                borderRadius: '24px',
                background: 'rgba(122, 224, 255, 0.08)',
                color: '#dbe3ff',
                fontSize: '24px',
                textAlign: 'center',
              }}
            >
              Waiting for the cashier terminal to start the next checkout.
            </div>
          )}
        </div>

        <div
          style={{
            borderRadius: '28px',
            padding: '24px',
            background: 'linear-gradient(180deg, rgba(52, 73, 133, 0.9) 0%, rgba(17, 22, 37, 0.92) 100%)',
            border: '1px solid rgba(122, 224, 255, 0.18)',
            display: 'grid',
            gap: '22px',
            alignContent: 'space-between',
          }}
        >
          <ToneBar label="State" value={payload.state.replaceAll('_', ' ')} />
          <ToneBar label="Subtotal" value={formatAmount(payload.subtotal)} />
          <ToneBar label="Tax" value={formatAmount(payload.tax_total)} />
          <ToneBar label="Total" value={formatAmount(payload.grand_total)} />
          {payload.payment_qr ? (
            <div
              style={{
                display: 'grid',
                gap: '16px',
                padding: '18px',
                borderRadius: '24px',
                background: 'rgba(122, 224, 255, 0.12)',
                border: '1px solid rgba(122, 224, 255, 0.2)',
                justifyItems: 'center',
              }}
            >
              <span style={{ fontSize: '12px', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#d1d8f0' }}>
                Dynamic UPI QR
              </span>
              <PaymentQrCode
                alt="Customer payment QR code"
                size={260}
                value={payload.payment_qr.value}
              />
              <strong style={{ fontSize: '18px', lineHeight: 1.4, textAlign: 'center', color: '#f5f7ff' }}>
                Scan with any UPI app
              </strong>
              <span style={{ fontSize: '16px', color: '#dbe3ff' }}>
                {paymentQrExpiry}
              </span>
              <strong style={{ fontSize: '14px', lineHeight: 1.6, wordBreak: 'break-all', textAlign: 'center', color: '#dbe3ff' }}>
                {payload.payment_qr.value}
              </strong>
            </div>
          ) : null}
          {payload.cash_received !== null ? <ToneBar label="Cash received" value={formatAmount(payload.cash_received)} /> : null}
          {payload.change_due !== null ? <ToneBar label="Change due" value={formatAmount(payload.change_due)} /> : null}
        </div>
      </section>
    </main>
  );
}
