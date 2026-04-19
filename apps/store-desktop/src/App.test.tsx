/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { App } from './App';
import { installRuntimeBootstrapFetchMock } from './control-plane/storeRuntimeTestHelpers';

describe('store runtime workspace', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    installRuntimeBootstrapFetchMock();
  });

  afterEach(() => {
    window.history.replaceState(null, '', '/');
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('auto-starts a runtime session from local bootstrap URL parameters', async () => {
    installRuntimeBootstrapFetchMock();

    window.history.replaceState(
      null,
      '',
      '/#stub_sub=cashier-1&stub_email=cashier@acme.local&stub_name=Counter%20Cashier',
    );

    render(<App />);

    expect(await screen.findByText('Counter Cashier')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Sell' })).toBeInTheDocument();
    expect(screen.getByText('Current cart')).toBeInTheDocument();
  });

  test('starts a runtime session and loads checkout posture', async () => {
    render(<App />);

    await screen.findByText('Browser local storage');

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start runtime session' }));

    expect(await screen.findByRole('heading', { name: 'Sell' })).toBeInTheDocument();
    expect(screen.getByText('Current cart')).toBeInTheDocument();
    expect(screen.getByText('Customer and totals')).toBeInTheDocument();
    expect(screen.getByText('Payment and session')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText('Live').length).toBeGreaterThan(0);
    });
  });
});
