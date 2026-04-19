import React, { type PropsWithChildren, type ReactNode, useId } from 'react';

const shellStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: 'var(--store-surface-app, linear-gradient(180deg, #f7f3eb 0%, #ffffff 44%, #eef3fb 100%))',
  color: 'var(--store-text-default, #25314f)',
  fontFamily: '"Segoe UI", "Inter", sans-serif',
};

const navRailStyle: React.CSSProperties = {
  position: 'sticky',
  top: 0,
  alignSelf: 'start',
  minHeight: '100vh',
  borderRight: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
  background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
  padding: '24px 20px',
  boxSizing: 'border-box',
};

const contentStyle: React.CSSProperties = {
  minWidth: 0,
  display: 'grid',
  gridTemplateRows: 'auto minmax(0, 1fr) auto',
};

const statusStripStyle: React.CSSProperties = {
  position: 'sticky',
  top: 0,
  zIndex: 2,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '16px',
  borderBottom: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
  background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
  backdropFilter: 'blur(14px)',
  padding: '14px 24px',
  boxSizing: 'border-box',
};

const bodyStyle: React.CSSProperties = {
  minWidth: 0,
  padding: '24px',
  boxSizing: 'border-box',
};

const footerStyle: React.CSSProperties = {
  position: 'sticky',
  bottom: 0,
  zIndex: 2,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '16px',
  borderTop: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
  background: 'var(--store-surface-raised, rgba(255,255,255,0.92))',
  backdropFilter: 'blur(14px)',
  padding: '16px 24px',
  boxSizing: 'border-box',
};

const railHeaderStyle: React.CSSProperties = {
  display: 'grid',
  gap: '4px',
  marginBottom: '20px',
};

const labelStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '11px',
  letterSpacing: '0.14em',
  textTransform: 'uppercase',
  color: 'var(--store-text-subtle, #778195)',
};

const headingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '18px',
  lineHeight: 1.2,
  fontWeight: 700,
  color: 'var(--store-text-strong, #172033)',
};

const subheadingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '13px',
  lineHeight: 1.5,
  color: 'var(--store-text-muted, #5a6477)',
};

export function RuntimeShell(props: PropsWithChildren<{ navRail?: ReactNode; statusStrip?: ReactNode; footer?: ReactNode }>) {
  return (
    <div
      style={{
        ...shellStyle,
        display: 'grid',
        gridTemplateColumns: props.navRail ? '280px minmax(0, 1fr)' : '1fr',
      }}
    >
      {props.navRail ? <div>{props.navRail}</div> : null}
      <div style={contentStyle}>
        {props.statusStrip}
        <RuntimeShellBody>{props.children}</RuntimeShellBody>
        {props.footer ? <RuntimeShellFooter>{props.footer}</RuntimeShellFooter> : null}
      </div>
    </div>
  );
}

export function RuntimeShellNavRail(props: PropsWithChildren<{ label?: string; title: string; subtitle?: string }>) {
  return (
    <aside style={navRailStyle} aria-label={props.title}>
      <div style={railHeaderStyle}>
        {props.label ? <p style={labelStyle}>{props.label}</p> : null}
        <h2 style={headingStyle}>{props.title}</h2>
        {props.subtitle ? <p style={subheadingStyle}>{props.subtitle}</p> : null}
      </div>
      <nav style={{ display: 'grid', gap: '8px' }}>{props.children}</nav>
    </aside>
  );
}

export function RuntimeShellStatusStrip(
  props: PropsWithChildren<{ label?: string; title: string; detail?: string; actions?: ReactNode }>,
) {
  const titleId = useId();

  return (
    <header style={statusStripStyle} aria-labelledby={titleId}>
      <div style={{ display: 'grid', gap: '4px' }}>
        {props.label ? <p style={labelStyle}>{props.label}</p> : null}
        <h1
          id={titleId}
          style={{ margin: 0, fontSize: '16px', lineHeight: 1.3, fontWeight: 700, color: 'var(--store-text-strong, #172033)' }}
        >
          {props.title}
        </h1>
        {props.detail ? (
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--store-text-muted, #5a6477)' }}>{props.detail}</p>
        ) : null}
        {props.children}
      </div>
      {props.actions ? <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>{props.actions}</div> : null}
    </header>
  );
}

export function RuntimeShellBody(props: PropsWithChildren) {
  return <main style={bodyStyle}>{props.children}</main>;
}

export function RuntimeShellFooter(props: PropsWithChildren) {
  return <footer style={footerStyle}>{props.children}</footer>;
}
