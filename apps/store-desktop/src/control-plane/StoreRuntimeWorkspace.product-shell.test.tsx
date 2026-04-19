/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from '../App';
import { installRuntimeBootstrapFetchMock } from './storeRuntimeTestHelpers';

describe('store runtime product shell', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    installRuntimeBootstrapFetchMock();
  });

  afterEach(() => {
    window.history.replaceState(null, '', '/');
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('defaults cashier-capable actors to the sell screen with a persistent navigation rail', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByRole('heading', { name: 'Sell' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entry' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sell' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('button', { name: 'Returns' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Operations' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Manager' })).not.toBeInTheDocument();
  });

  test('shows secondary operations and manager screens only when the actor posture allows them', async () => {
    installRuntimeBootstrapFetchMock({
      branchRoleNames: ['cashier', 'stock_clerk', 'store_manager'],
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=manager-1;email=manager@acme.local;name=Branch Manager' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByRole('button', { name: 'Operations' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Manager' })).toBeInTheDocument();
  });
});
