/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { StoreThemeModeToggle, StoreThemeProvider, useStoreTheme } from './theme';

const originalMatchMedia = window.matchMedia;
const originalLocalStorage = window.localStorage;

function createMemoryStorage(): Storage {
  const data = new Map<string, string>();
  return {
    get length() {
      return data.size;
    },
    clear() {
      data.clear();
    },
    getItem(key: string) {
      return data.has(key) ? data.get(key)! : null;
    },
    key(index: number) {
      return Array.from(data.keys())[index] ?? null;
    },
    removeItem(key: string) {
      data.delete(key);
    },
    setItem(key: string, value: string) {
      data.set(key, value);
    },
  };
}

function ThemeProbe() {
  const theme = useStoreTheme();
  return (
    <div>
      <span>mode:{theme.mode}</span>
      <span>resolved:{theme.resolvedTheme}</span>
      <StoreThemeModeToggle />
    </div>
  );
}

describe('store theme provider', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: createMemoryStorage(),
    });
    window.localStorage.clear();
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes('dark'),
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as typeof window.matchMedia;
  });

  afterEach(() => {
    cleanup();
    window.localStorage.clear();
    window.matchMedia = originalMatchMedia;
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: originalLocalStorage,
    });
    vi.restoreAllMocks();
  });

  test('resolves system mode from the active color scheme preference', () => {
    render(
      <StoreThemeProvider storageKey="test.theme.mode">
        <ThemeProbe />
      </StoreThemeProvider>,
    );

    expect(screen.getByText('mode:system')).toBeInTheDocument();
    expect(screen.getByText('resolved:dark')).toBeInTheDocument();
  });

  test('persists explicit theme mode changes', () => {
    render(
      <StoreThemeProvider storageKey="test.theme.mode">
        <ThemeProbe />
      </StoreThemeProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Light theme' }));

    expect(screen.getByText('mode:light')).toBeInTheDocument();
    expect(screen.getByText('resolved:light')).toBeInTheDocument();
    expect(localStorage.getItem('test.theme.mode')).toBe('light');
  });
});
