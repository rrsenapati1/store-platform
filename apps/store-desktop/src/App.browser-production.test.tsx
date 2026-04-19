/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

vi.mock('./control-plane/storeRuntimeAuthMode', () => ({
  isStoreRuntimeDeveloperBootstrapEnabled: () => false,
}));

import { App } from './App';

class MemoryStorage implements Storage {
  private readonly data = new Map<string, string>();

  get length() {
    return this.data.size;
  }

  clear(): void {
    this.data.clear();
  }

  getItem(key: string): string | null {
    return this.data.get(key) ?? null;
  }

  key(index: number): string | null {
    return Array.from(this.data.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.data.delete(key);
  }

  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

describe('store runtime browser production posture', () => {
  const originalFetch = globalThis.fetch;
  const originalLocalStorage = globalThis.localStorage;

  beforeEach(() => {
    const storage = new MemoryStorage();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: storage,
    });
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: storage,
    });
    globalThis.fetch = vi.fn(async () => {
      throw new Error('browser production posture should not attempt network bootstrap');
    }) as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: originalLocalStorage,
    });
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: originalLocalStorage,
    });
    vi.restoreAllMocks();
  });

  test('does not offer manual token bootstrap outside developer mode', async () => {
    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Store access' })).toBeInTheDocument();
    expect(screen.queryByLabelText('Korsenex token')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start runtime session' })).not.toBeInTheDocument();
    expect(screen.getAllByText(/Browser preview does not support production sign-in/i).length).toBeGreaterThan(0);
  });
});
