import React, { type PropsWithChildren } from 'react';
import type { WorkspaceMetric } from '@store/types';

const shellStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: 'linear-gradient(180deg, #f4f1e8 0%, #ffffff 45%, #f0f5ff 100%)',
  color: '#172033',
  fontFamily: '"Segoe UI", sans-serif',
  padding: '32px',
};

const cardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.88)',
  border: '1px solid rgba(23,32,51,0.08)',
  borderRadius: '18px',
  boxShadow: '0 24px 48px rgba(23,32,51,0.08)',
  padding: '20px',
};

export function AppShell(props: PropsWithChildren<{ title: string; subtitle: string; kicker: string }>) {
  return (
    <main style={shellStyle}>
      <section style={{ ...cardStyle, marginBottom: '24px' }}>
        <p style={{ margin: 0, fontSize: '12px', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#7a5c1b' }}>
          {props.kicker}
        </p>
        <h1 style={{ margin: '12px 0 8px', fontSize: '40px', lineHeight: 1.1 }}>{props.title}</h1>
        <p style={{ margin: 0, fontSize: '18px', color: '#4e5871', maxWidth: '760px' }}>{props.subtitle}</p>
      </section>
      {props.children}
    </main>
  );
}

export function MetricGrid(props: { metrics: WorkspaceMetric[] }) {
  return (
    <section
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px',
        marginBottom: '24px',
      }}
    >
      {props.metrics.map((metric) => (
        <article key={metric.label} style={cardStyle}>
          <p style={{ margin: 0, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#75809b' }}>
            {metric.label}
          </p>
          <strong style={{ display: 'block', marginTop: '10px', fontSize: '28px' }}>{metric.value}</strong>
        </article>
      ))}
    </section>
  );
}

export function SectionCard(props: PropsWithChildren<{ title: string; eyebrow?: string }>) {
  return (
    <section style={{ ...cardStyle, marginBottom: '20px' }}>
      {props.eyebrow ? (
        <p style={{ margin: 0, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#75809b' }}>
          {props.eyebrow}
        </p>
      ) : null}
      <h2 style={{ margin: '10px 0 14px', fontSize: '24px' }}>{props.title}</h2>
      {props.children}
    </section>
  );
}

export function BulletList(props: { items: string[] }) {
  return (
    <ul style={{ margin: 0, paddingLeft: '20px', color: '#4e5871', lineHeight: 1.7 }}>
      {props.items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function FormField(
  props: PropsWithChildren<{
    label: string;
    id: string;
    value: string;
    placeholder?: string;
    onChange: (value: string) => void;
    multiline?: boolean;
  }>,
) {
  const inputStyle: React.CSSProperties = {
    width: '100%',
    borderRadius: '12px',
    border: '1px solid rgba(23,32,51,0.14)',
    padding: props.multiline ? '12px' : '10px 12px',
    fontSize: '14px',
    color: '#172033',
    background: 'rgba(255,255,255,0.98)',
    boxSizing: 'border-box',
  };

  return (
    <label htmlFor={props.id} style={{ display: 'grid', gap: '8px', marginBottom: '14px', color: '#25314f' }}>
      <span style={{ fontSize: '13px', fontWeight: 600 }}>{props.label}</span>
      {props.multiline ? (
        <textarea
          id={props.id}
          value={props.value}
          placeholder={props.placeholder}
          rows={4}
          onChange={(event) => props.onChange(event.target.value)}
          style={{ ...inputStyle, resize: 'vertical' }}
        />
      ) : (
        <input
          id={props.id}
          value={props.value}
          placeholder={props.placeholder}
          onChange={(event) => props.onChange(event.target.value)}
          style={inputStyle}
        />
      )}
      {props.children}
    </label>
  );
}

export function ActionButton(props: PropsWithChildren<{ onClick?: () => void; type?: 'button' | 'submit'; disabled?: boolean }>) {
  return (
    <button
      type={props.type ?? 'button'}
      onClick={props.onClick}
      disabled={props.disabled}
      style={{
        border: 0,
        borderRadius: '999px',
        padding: '11px 18px',
        fontSize: '14px',
        fontWeight: 700,
        background: props.disabled ? '#c5cad7' : '#172033',
        color: '#ffffff',
        cursor: props.disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {props.children}
    </button>
  );
}

export function StatusBadge(props: { label: string; tone?: 'neutral' | 'warning' | 'success' }) {
  const toneMap = {
    neutral: { background: '#eef2f9', color: '#25314f' },
    warning: { background: '#fff0cf', color: '#8a5a00' },
    success: { background: '#dcf7e7', color: '#13683a' },
  } as const;
  const tone = toneMap[props.tone ?? 'neutral'];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        borderRadius: '999px',
        padding: '6px 10px',
        fontSize: '12px',
        fontWeight: 700,
        background: tone.background,
        color: tone.color,
      }}
    >
      {props.label}
    </span>
  );
}

export function DetailList(props: { items: Array<{ label: string; value: React.ReactNode }> }) {
  return (
    <dl
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px 16px',
        margin: 0,
      }}
    >
      {props.items.map((item) => (
        <div key={item.label} style={{ display: 'grid', gap: '4px' }}>
          <dt style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.12em', color: '#75809b' }}>{item.label}</dt>
          <dd style={{ margin: 0, color: '#25314f', fontWeight: 600 }}>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
