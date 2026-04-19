/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import {
  ActionButton,
  AppShell,
  OwnerCommandHeader,
  OwnerCommandShell,
  OwnerExceptionBoard,
  OwnerNavRail,
  OwnerPanel,
  OwnerSignalRow,
  PlatformCommandHeader,
  PlatformCommandShell,
  PlatformExceptionBoard,
  PlatformNavRail,
  PlatformPanel,
  PlatformSignalRow,
  CommerceLineItem,
  CommerceSheet,
  CommerceSummaryRow,
  CommerceTotalsBlock,
  DetailList,
  FormField,
  MetricGrid,
  StoreThemeModeToggle,
  StoreThemeProvider,
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

  test('renders runtime shell primitives with tokenized shell surfaces', () => {
    render(
      <StoreThemeProvider storageKey="ui.index.runtime-shell.theme" defaultMode="dark">
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
        </RuntimeShell>
      </StoreThemeProvider>,
    );

    expect(screen.getByText('Store Desktop')).toBeInTheDocument();
    expect(screen.getByText('Connected to local queue')).toBeInTheDocument();
    expect(screen.getByText('Main workspace')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Settle' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Transactions' })).toBeInTheDocument();

    const navigation = screen.getByLabelText('Store Desktop');
    expect(navigation.getAttribute('style')).toContain('var(--store-surface-raised');
    expect(navigation.getAttribute('style')).toContain('var(--store-border-soft');

    const sessionHeading = screen.getByRole('heading', { name: 'Register 04' });
    const sessionStrip = sessionHeading.closest('header');
    expect(sessionStrip?.getAttribute('style')).toContain('var(--store-surface-raised');
    expect(sessionStrip?.getAttribute('style')).toContain('var(--store-border-soft');
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

  test('renders theme and owner shell primitives from the package barrel', () => {
    render(
      <StoreThemeProvider storageKey="ui.index.test.theme">
        <OwnerCommandShell
          navRail={
            <OwnerNavRail
              title="Acme Retail"
              items={[
                { id: 'overview', label: 'Overview' },
                { id: 'commercial', label: 'Commercial' },
              ]}
              activeItemId="overview"
              onSelect={() => undefined}
            />
          }
          commandHeader={
            <OwnerCommandHeader
              title="Overview"
              branchOptions={[{ value: 'all', label: 'All branches' }]}
              selectedBranch="all"
              onBranchChange={() => undefined}
              actions={<StoreThemeModeToggle />}
            />
          }
        >
          <OwnerSignalRow items={[{ label: 'Branches', value: '1' }]} />
          <OwnerPanel title="Exceptions">
            <OwnerExceptionBoard items={[{ id: '1', title: 'Low stock', detail: 'Classic Tea' }]} />
          </OwnerPanel>
        </OwnerCommandShell>
      </StoreThemeProvider>,
    );

    expect(screen.getAllByText('Acme Retail')).toHaveLength(2);
    expect(screen.getByText('Branches')).toBeInTheDocument();
    expect(screen.getByText('Low stock')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Light theme' })).toBeInTheDocument();
  });

  test('renders platform shell primitives from the package barrel', () => {
    render(
      <PlatformCommandShell
        navRail={(
          <PlatformNavRail
            title="Platform Tower"
            items={[
              { id: 'overview', label: 'Overview' },
              { id: 'release', label: 'Release' },
            ]}
            activeItemId="overview"
            onSelect={() => undefined}
          />
        )}
        commandHeader={(
          <PlatformCommandHeader
            title="Overview"
            environmentLabel="staging"
            releaseLabel="2026.04.19"
            statusLabel="Healthy"
            statusTone="success"
          />
        )}
      >
        <PlatformSignalRow items={[{ label: 'Release readiness', value: 'Healthy', tone: 'success' }]} />
        <PlatformPanel title="Exceptions">
          <PlatformExceptionBoard items={[{ id: '1', title: 'Dead-letter jobs', detail: '1 jobs require review.' }]} />
        </PlatformPanel>
      </PlatformCommandShell>,
    );

    expect(screen.getByText('Platform Tower')).toBeInTheDocument();
    expect(screen.getByText('Env: staging')).toBeInTheDocument();
    expect(screen.getByText('Release readiness')).toBeInTheDocument();
    expect(screen.getByText('Dead-letter jobs')).toBeInTheDocument();
  });
});
