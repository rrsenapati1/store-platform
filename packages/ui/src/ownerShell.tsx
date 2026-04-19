import React, { type PropsWithChildren, type ReactNode } from 'react';

type OwnerNavItem = {
  id: string;
  label: string;
};

type OwnerSignalItem = {
  label: string;
  value: ReactNode;
  tone?: 'neutral' | 'warning' | 'success' | 'danger';
};

type OwnerExceptionItem = {
  id: string;
  title: string;
  detail: string;
  ctaLabel?: string;
  onSelect?: () => void;
};

function toneChip(tone: OwnerSignalItem['tone']): React.CSSProperties {
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
        background: 'var(--store-accent-soft, rgba(31,79,191,0.12))',
        color: 'var(--store-accent, #1f4fbf)',
      };
  }
}

export function OwnerCommandShell(props: PropsWithChildren<{ navRail: ReactNode; commandHeader: ReactNode }>) {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--store-surface-app, linear-gradient(180deg, #f7f3eb 0%, #ffffff 44%, #eef3fb 100%))',
        color: 'var(--store-text-default, #25314f)',
        display: 'grid',
        gridTemplateColumns: '280px minmax(0, 1fr)',
      }}
    >
      <aside style={{ borderRight: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))', minHeight: '100vh' }}>{props.navRail}</aside>
      <div style={{ minWidth: 0, display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)' }}>
        {props.commandHeader}
        <main style={{ minWidth: 0, padding: '24px', display: 'grid', gap: '20px' }}>{props.children}</main>
      </div>
    </div>
  );
}

export function OwnerNavRail(props: { title: string; subtitle?: string; items: OwnerNavItem[]; activeItemId: string; onSelect: (id: string) => void }) {
  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        padding: '28px 20px',
        minHeight: '100vh',
        background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
      }}
    >
      <div style={{ display: 'grid', gap: '6px', marginBottom: '24px' }}>
        <p style={{ margin: 0, fontSize: '11px', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--store-text-subtle, #778195)' }}>
          Owner console
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

export function OwnerCommandHeader(props: {
  title: string;
  subtitle?: string;
  branchOptions: Array<{ value: string; label: string }>;
  selectedBranch: string;
  onBranchChange: (value: string) => void;
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
      <div style={{ display: 'grid', gap: '8px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '28px', lineHeight: 1.15, color: 'var(--store-text-strong, #172033)' }}>{props.title}</h2>
          {props.subtitle ? <p style={{ margin: '6px 0 0', fontSize: '14px', color: 'var(--store-text-muted, #5a6477)' }}>{props.subtitle}</p> : null}
        </div>
        <label style={{ display: 'grid', gap: '6px', width: 'min(280px, 100%)' }}>
          <span style={{ fontSize: '12px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--store-text-subtle, #778195)' }}>
            Branch filter
          </span>
          <select
            aria-label="Branch filter"
            value={props.selectedBranch}
            onChange={(event) => props.onBranchChange(event.target.value)}
            style={{
              borderRadius: 'var(--store-radius-control, 14px)',
              border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
              background: 'var(--store-surface-panel, rgba(251,252,255,0.94))',
              color: 'var(--store-text-default, #25314f)',
              padding: '11px 12px',
              fontSize: '14px',
            }}
          >
            {props.branchOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {props.actions ? <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>{props.actions}</div> : null}
    </header>
  );
}

export function OwnerSignalRow(props: { items: OwnerSignalItem[] }) {
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

export function OwnerPanel(props: PropsWithChildren<{ title: string; subtitle?: string; actions?: ReactNode }>) {
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

export function OwnerExceptionBoard(props: { items: OwnerExceptionItem[]; emptyState?: string }) {
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
            <strong style={{ fontSize: '15px', color: 'var(--store-text-strong, #172033)' }}>{item.title}</strong>
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
