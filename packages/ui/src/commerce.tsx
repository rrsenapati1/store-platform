import React, { type PropsWithChildren, type ReactNode, useId } from 'react';

const lineItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  justifyContent: 'space-between',
  gap: '16px',
  padding: '14px 0',
  borderBottom: '1px solid rgba(23,32,51,0.08)',
};

const lineItemTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '14px',
  lineHeight: 1.35,
  fontWeight: 600,
  color: '#172033',
};

const lineItemMetaStyle: React.CSSProperties = {
  margin: '4px 0 0',
  fontSize: '12px',
  lineHeight: 1.5,
  color: '#5a6477',
};

const summaryRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'baseline',
  justifyContent: 'space-between',
  gap: '16px',
  padding: '8px 0',
};

const sheetOverlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  display: 'grid',
  gridTemplateColumns: '1fr',
  background: 'rgba(15, 23, 42, 0.42)',
  zIndex: 50,
};

const sheetPanelStyle: React.CSSProperties = {
  width: 'min(460px, 100vw)',
  height: '100%',
  background: '#ffffff',
  boxShadow: '0 24px 72px rgba(15, 23, 42, 0.24)',
  display: 'grid',
  gridTemplateRows: 'auto minmax(0, 1fr) auto',
};

const sheetHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  justifyContent: 'space-between',
  gap: '16px',
  padding: '20px 20px 16px',
  borderBottom: '1px solid rgba(23,32,51,0.08)',
};

const sheetBodyStyle: React.CSSProperties = {
  minHeight: 0,
  padding: '20px',
  overflow: 'auto',
};

const sheetFooterStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '12px',
  padding: '16px 20px 20px',
  borderTop: '1px solid rgba(23,32,51,0.08)',
};

const tonePillStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  borderRadius: '999px',
  padding: '4px 10px',
  fontSize: '12px',
  fontWeight: 700,
  background: '#eef2f9',
  color: '#25314f',
};

export function CommerceLineItem(
  props: PropsWithChildren<{
    title: string;
    meta?: string;
    quantity?: ReactNode;
    amount?: ReactNode;
    secondary?: ReactNode;
  }>,
) {
  return (
    <article style={lineItemStyle}>
      <div style={{ minWidth: 0, display: 'grid', gap: '2px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
          <h3 style={{ ...lineItemTitleStyle, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {props.title}
          </h3>
          {props.quantity ? <span style={tonePillStyle}>{props.quantity}</span> : null}
        </div>
        {props.meta ? <p style={lineItemMetaStyle}>{props.meta}</p> : null}
        {props.secondary}
        {props.children}
      </div>
      {props.amount ? <div style={{ fontSize: '14px', fontWeight: 700, color: '#172033' }}>{props.amount}</div> : null}
    </article>
  );
}

export function CommerceSummaryRow(props: { label: string; value: ReactNode; emphasis?: boolean }) {
  return (
    <div style={summaryRowStyle}>
      <span style={{ fontSize: '13px', color: props.emphasis ? '#172033' : '#5a6477', fontWeight: props.emphasis ? 700 : 500 }}>
        {props.label}
      </span>
      <span style={{ fontSize: props.emphasis ? '16px' : '13px', color: '#172033', fontWeight: props.emphasis ? 700 : 600 }}>
        {props.value}
      </span>
    </div>
  );
}

export function CommerceTotalsBlock(props: PropsWithChildren<{ title?: string; footnote?: string }>) {
  return (
    <section
      style={{
        border: '1px solid rgba(23,32,51,0.08)',
        borderRadius: '16px',
        background: '#fbfcfe',
        padding: '16px',
        display: 'grid',
        gap: '8px',
      }}
    >
      {props.title ? <h2 style={{ margin: 0, fontSize: '13px', letterSpacing: '0.08em', textTransform: 'uppercase', color: '#6b7487' }}>{props.title}</h2> : null}
      <div style={{ display: 'grid' }}>{props.children}</div>
      {props.footnote ? <p style={{ margin: 0, fontSize: '12px', color: '#5a6477' }}>{props.footnote}</p> : null}
    </section>
  );
}

export function CommerceSheet(
  props: PropsWithChildren<{
    open: boolean;
    title: string;
    subtitle?: string;
    onClose?: () => void;
    footer?: ReactNode;
  }>,
) {
  const titleId = useId();

  if (!props.open) {
    return null;
  }

  return (
    <div style={sheetOverlayStyle} onClick={props.onClose} role="presentation">
      <aside
        aria-modal="true"
        aria-labelledby={titleId}
        role="dialog"
        style={sheetPanelStyle}
        onClick={(event) => event.stopPropagation()}
      >
        <header style={sheetHeaderStyle}>
          <div style={{ minWidth: 0, display: 'grid', gap: '4px' }}>
            <h2 id={titleId} style={{ margin: 0, fontSize: '18px', lineHeight: 1.3, fontWeight: 700, color: '#172033' }}>
              {props.title}
            </h2>
            {props.subtitle ? <p style={{ margin: 0, fontSize: '13px', color: '#5a6477' }}>{props.subtitle}</p> : null}
          </div>
          {props.onClose ? (
            <button
              type="button"
              aria-label={`Close ${props.title.toLowerCase()}`}
              onClick={props.onClose}
              style={{
                border: '1px solid rgba(23,32,51,0.12)',
                borderRadius: '999px',
                background: '#ffffff',
                color: '#172033',
                padding: '8px 12px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          ) : null}
        </header>
        <div style={sheetBodyStyle}>{props.children}</div>
        {props.footer ? <footer style={sheetFooterStyle}>{props.footer}</footer> : null}
      </aside>
    </div>
  );
}
