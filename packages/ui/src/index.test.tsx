/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import { ActionButton, AppShell, DetailList, FormField, MetricGrid, SectionCard, StatusBadge } from './index';

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
});
