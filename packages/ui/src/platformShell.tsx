import React, { type PropsWithChildren, type ReactNode } from 'react';

type PlatformNavItem = {
  id: string;
  label: string;
};

type PlatformSignalItem = {
  label: string;
  value: ReactNode;
  tone?: 'neutral' | 'warning' | 'success' | 'danger';
};

type PlatformExceptionItem = {
  id: string;
  title: string;
  detail: string;
  tone?: 'neutral' | 'warning' | 'success' | 'danger';
  ctaLabel?: string;
  onSelect?: () => void;
};

function toneChip(tone: PlatformSignalItem['tone']): React.CSSProperties {
  switch (tone) {
    case 'success':
      return {
        background: 'var(--store-success-soft, #dcf7e7)',
        color: 'var(--store-success, #13683a)',
      };
    case 'warning':
      return {
        background: 'var(--store-warning-soft, #fff0cf)',
        color: 'var(--store-warning, #8a5a00)',
      };
    case 'danger':
      return {
        background: 'var(--store-danger-soft, #ffe1db)',
        color: 'var(--store-danger, #9d2b19)',
      };
    default:
      return {
        background: 'var(--store-surface-muted, rgba(237,241,248,0.96))',
        color: 'var(--store-text-default, #25314f)',
      };
  }
}

export function PlatformCommandShell(props: PropsWithChildren<{ navRail: ReactNode; commandHeader: ReactNode }>) {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--store-surface-app, linear-gradient(180deg, #f7f3eb 0%, #ffffff 44%, #eef3fb 100%))',
        color: 'var(--store-text-default, #25314f)',
        display: 'grid',
        gridTemplateColumns: '288px minmax(0, 1fr)',
      }}
    >
      <aside
        style={{
          minHeight: '100vh',
          borderRight: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
          background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
        }}
      >
        {props.navRail}
      </aside>
      <div style={{ minWidth: 0, display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)' }}>
        {props.commandHeader}
        <main style={{ minWidth: 0, padding: '24px', display: 'grid', gap: '20px' }}>{props.children}</main>
      </div>
    </div>
  );
}

export function PlatformNavRail(props: { title: string; subtitle?: string; items: PlatformNavItem[]; activeItemId: string; onSelect: (id: string) => void }) {
  return (
    <div style={{ position: 'sticky', top: 0, minHeight: '100vh', padding: '28px 20px', display: 'grid', gap: '24px' }}>
      <div style={{ display: 'grid', gap: '8px' }}>
        <p style={{ margin: 0, fontSize: '11px', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--store-text-subtle, #778195)' }}>
          Platform control
        </p>
        <h1 style={{ margin: 0, fontSize: '24px', lineHeight: 1.15, color: 'var(--store-text-strong, #172033)' }}>{props.title}</h1>
        {props.subtitle ? <p style={{ margin: 0, fontSize: '13px', color: 'var(--store-text-muted, #5a6477)' }}>{props.subtitle}</p> : null}
      </div>
      <nav style={{ display: 'grid', gap: '8px' }}>
        {props.items.map((item) => {
          const active = item.id === props.activeItemId;
          return (
            <button
              key={item.id}
              type="button"
              aria-current={active ? 'page' : undefined}
              onClick={() => props.onSelect(item.id)}
              style={{
                border: '1px solid',
                borderColor: active ? 'var(--store-accent, #1f4fbf)' : 'var(--store-border-soft, rgba(23,32,51,0.10))',
                borderRadius: 'var(--store-radius-control, 14px)',
                background: active ? 'var(--store-accent-soft, rgba(31,79,191,0.12))' : 'transparent',
                color: active ? 'var(--store-text-strong, #172033)' : 'var(--store-text-default, #25314f)',
                padding: '12px 14px',
                textAlign: 'left',
                fontSize: '14px',
                fontWeight: active ? 700 : 600,
                cursor: 'pointer',
              }}
            >
              {item.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

export function PlatformCommandHeader(props: {
  title: string;
  subtitle?: string;
  environmentLabel: string;
  releaseLabel: string;
  statusLabel: string;
  statusTone?: 'neutral' | 'warning' | 'success' | 'danger';
  actions?: ReactNode;
}) {
  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 2,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: '16px',
        padding: '20px 24px 18px',
        borderBottom: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
        background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
        backdropFilter: 'blur(16px)',
      }}
    >
      <div style={{ display: 'grid', gap: '10px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '28px', lineHeight: 1.15, color: 'var(--store-text-strong, #172033)' }}>{props.title}</h2>
          {props.subtitle ? <p style={{ margin: '6px 0 0', fontSize: '14px', color: 'var(--store-text-muted, #5a6477)' }}>{props.subtitle}</p> : null}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          <span style={{ ...toneChip('neutral'), borderRadius: 'var(--store-radius-pill, 999px)', padding: '6px 10px', fontSize: '12px', fontWeight: 700 }}>
            Env: {props.environmentLabel}
          </span>
          <span style={{ ...toneChip('neutral'), borderRadius: 'var(--store-radius-pill, 999px)', padding: '6px 10px', fontSize: '12px', fontWeight: 700 }}>
            Release: {props.releaseLabel}
          </span>
          <span style={{ ...toneChip(props.statusTone ?? 'neutral'), borderRadius: 'var(--store-radius-pill, 999px)', padding: '6px 10px', fontSize: '12px', fontWeight: 700 }}>
            {props.statusLabel}
          </span>
        </div>
      </div>
      {props.actions ? <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>{props.actions}</div> : null}
    </header>
  );
}

export function PlatformSignalRow(props: { items: PlatformSignalItem[] }) {
  return (
    <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
      {props.items.map((item) => (
        <article
          key={item.label}
          style={{
            background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
            border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
            borderRadius: 'var(--store-radius-card, 20px)',
            boxShadow: 'var(--store-shadow-soft, 0 20px 48px rgba(23,32,51,0.10))',
            padding: '18px',
            display: 'grid',
            gap: '10px',
          }}
        >
          <span style={{ fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--store-text-subtle, #778195)', fontWeight: 700 }}>
            {item.label}
          </span>
          <strong style={{ fontSize: '24px', lineHeight: 1.1, color: 'var(--store-text-strong, #172033)' }}>{item.value}</strong>
          {item.tone ? (
            <span
              style={{
                width: 'fit-content',
                borderRadius: 'var(--store-radius-pill, 999px)',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 700,
                ...toneChip(item.tone),
              }}
            >
              {item.tone.toUpperCase()}
            </span>
          ) : null}
        </article>
      ))}
    </section>
  );
}

export function PlatformPanel(props: PropsWithChildren<{ title: string; subtitle?: string; actions?: ReactNode }>) {
  return (
    <section
      style={{
        background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
        border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
        borderRadius: 'var(--store-radius-card, 20px)',
        boxShadow: 'var(--store-shadow-soft, 0 20px 48px rgba(23,32,51,0.10))',
        padding: '20px',
        display: 'grid',
        gap: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'grid', gap: '6px' }}>
          <h3 style={{ margin: 0, fontSize: '22px', lineHeight: 1.15, color: 'var(--store-text-strong, #172033)' }}>{props.title}</h3>
          {props.subtitle ? <p style={{ margin: 0, fontSize: '14px', color: 'var(--store-text-muted, #5a6477)' }}>{props.subtitle}</p> : null}
        </div>
        {props.actions}
      </div>
      {props.children}
    </section>
  );
}

export function PlatformExceptionBoard(props: { items: PlatformExceptionItem[]; emptyState?: string }) {
  if (props.items.length === 0) {
    return <p style={{ margin: 0, color: 'var(--store-text-muted, #5a6477)' }}>{props.emptyState ?? 'No active exceptions.'}</p>;
  }

  return (
    <div style={{ display: 'grid', gap: '12px' }}>
      {props.items.map((item) => (
        <article
          key={item.id}
          style={{
            display: 'grid',
            gap: '8px',
            padding: '16px',
            borderRadius: 'var(--store-radius-control, 14px)',
            background: 'var(--store-surface-panel, rgba(251,252,255,0.94))',
            border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <strong style={{ fontSize: '15px', color: 'var(--store-text-strong, #172033)' }}>{item.title}</strong>
              {item.tone ? (
                <span
                  style={{
                    borderRadius: 'var(--store-radius-pill, 999px)',
                    padding: '4px 8px',
                    fontSize: '11px',
                    fontWeight: 700,
                    ...toneChip(item.tone),
                  }}
                >
                  {item.tone.toUpperCase()}
                </span>
              ) : null}
            </div>
            {item.onSelect ? (
              <button
                type="button"
                onClick={item.onSelect}
                style={{
                  border: 0,
                  background: 'transparent',
                  color: 'var(--store-accent, #1f4fbf)',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                {item.ctaLabel ?? 'Review'}
              </button>
            ) : null}
          </div>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.5 }}>{item.detail}</p>
        </article>
      ))}
    </div>
  );
}
