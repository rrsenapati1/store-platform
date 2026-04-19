/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import {
  ActionButton,
  AppShell,
  CommerceLineItem,
  CommerceSheet,
  CommerceSummaryRow,
  CommerceTotalsBlock,
  DetailList,
  FormField,
  MetricGrid,
  RuntimeShell,
  RuntimeShellNavRail,
  RuntimeShellStatusStrip,
  SectionCard,
  StatusBadge,
} from './index';

describe('shared ui primitives', () => {
  test('renders a shell, metric grid, and section card', () => {
    let fieldValue = 'stub';
    render(
      <AppShell kicker="Wave 1" title="Store Platform" subtitle="Retail ops">
        <MetricGrid metrics={[{ label: 'Tenants', value: '1' }]} />
        <SectionCard title="Overview">
          <FormField id="token" label="Token" value={fieldValue} onChange={(next) => (fieldValue = next)} />
          <StatusBadge label="READY" />
          <DetailList items={[{ label: 'Tenant', value: 'Acme Retail' }]} />
          <ActionButton>Continue</ActionButton>
        </SectionCard>
      </AppShell>,
    );

    expect(screen.getByText('Store Platform')).toBeInTheDocument();
    expect(screen.getByText('Tenants')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByLabelText('Token')).toBeInTheDocument();
    expect(screen.getByText('READY')).toBeInTheDocument();
    expect(screen.getByText('Acme Retail')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
  });

  test('renders runtime shell primitives with the expected slots', () => {
    render(
      <RuntimeShell
        navRail={(
          <RuntimeShellNavRail label="Navigation" title="Store Desktop" subtitle="Operator controls">
            <button type="button">Transactions</button>
          </RuntimeShellNavRail>
        )}
        statusStrip={<RuntimeShellStatusStrip label="Session" title="Register 04" detail="Connected to local queue" />}
        footer={<ActionButton>Settle</ActionButton>}
      >
        <section>Main workspace</section>
      </RuntimeShell>,
    );

    expect(screen.getByText('Store Desktop')).toBeInTheDocument();
    expect(screen.getByText('Connected to local queue')).toBeInTheDocument();
    expect(screen.getByText('Main workspace')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Settle' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Transactions' })).toBeInTheDocument();
  });

  test('renders commerce primitives and closes the sheet', () => {
    const onClose = vi.fn();

    render(
      <CommerceSheet open title="Checkout" subtitle="Tender and review" onClose={onClose} footer={<ActionButton>Charge</ActionButton>}>
        <CommerceLineItem title="Plain Tee" meta="Size M · Blue" quantity="2" amount="$48.00" />
        <CommerceTotalsBlock title="Totals" footnote="Taxes calculated at tender time">
          <CommerceSummaryRow label="Subtotal" value="$48.00" />
          <CommerceSummaryRow label="Total" value="$48.00" emphasis />
        </CommerceTotalsBlock>
      </CommerceSheet>,
    );

    expect(screen.getByRole('dialog', { name: 'Checkout' })).toBeInTheDocument();
    expect(screen.getByText('Plain Tee')).toBeInTheDocument();
    expect(screen.getByText('Totals')).toBeInTheDocument();
    expect(screen.getByText('Taxes calculated at tender time')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Charge' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Close checkout' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
