import React, { createContext, type PropsWithChildren, useContext, useEffect, useMemo, useState } from 'react';

export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

const DEFAULT_STORAGE_KEY = 'store.theme.mode';
const SYSTEM_DARK_QUERY = '(prefers-color-scheme: dark)';

const themeTokens: Record<ResolvedTheme, Record<string, string>> = {
  light: {
    '--store-theme-resolved': 'light',
    '--store-surface-app': 'linear-gradient(180deg, #f7f3eb 0%, #ffffff 44%, #eef3fb 100%)',
    '--store-surface-raised': 'rgba(255,255,255,0.92)',
    '--store-surface-panel': 'rgba(251,252,255,0.94)',
    '--store-surface-muted': 'rgba(237,241,248,0.96)',
    '--store-text-strong': '#172033',
    '--store-text-default': '#25314f',
    '--store-text-muted': '#5a6477',
    '--store-text-subtle': '#778195',
    '--store-border-soft': 'rgba(23,32,51,0.10)',
    '--store-border-strong': 'rgba(23,32,51,0.18)',
    '--store-accent': '#1f4fbf',
    '--store-accent-strong': '#173a89',
    '--store-accent-soft': 'rgba(31,79,191,0.12)',
    '--store-success': '#13683a',
    '--store-success-soft': '#dcf7e7',
    '--store-warning': '#8a5a00',
    '--store-warning-soft': '#fff0cf',
    '--store-danger': '#9d2b19',
    '--store-danger-soft': '#ffe1db',
    '--store-shadow-soft': '0 20px 48px rgba(23,32,51,0.10)',
    '--store-shadow-strong': '0 28px 68px rgba(23,32,51,0.16)',
    '--store-radius-card': '20px',
    '--store-radius-pill': '999px',
    '--store-radius-control': '14px',
    '--store-transition-fast': '160ms ease',
  },
  dark: {
    '--store-theme-resolved': 'dark',
    '--store-surface-app': 'linear-gradient(180deg, #0f1728 0%, #111b30 44%, #08111f 100%)',
    '--store-surface-raised': 'rgba(17,27,48,0.92)',
    '--store-surface-panel': 'rgba(20,33,59,0.94)',
    '--store-surface-muted': 'rgba(31,46,77,0.96)',
    '--store-text-strong': '#f6f8fc',
    '--store-text-default': '#dde6f7',
    '--store-text-muted': '#b5c1d8',
    '--store-text-subtle': '#8e9bb4',
    '--store-border-soft': 'rgba(191,204,231,0.14)',
    '--store-border-strong': 'rgba(191,204,231,0.22)',
    '--store-accent': '#7ea6ff',
    '--store-accent-strong': '#a9c3ff',
    '--store-accent-soft': 'rgba(126,166,255,0.18)',
    '--store-success': '#7cd8a1',
    '--store-success-soft': 'rgba(124,216,161,0.14)',
    '--store-warning': '#ffca6b',
    '--store-warning-soft': 'rgba(255,202,107,0.14)',
    '--store-danger': '#ff9f90',
    '--store-danger-soft': 'rgba(255,159,144,0.14)',
    '--store-shadow-soft': '0 24px 48px rgba(0,0,0,0.24)',
    '--store-shadow-strong': '0 36px 84px rgba(0,0,0,0.34)',
    '--store-radius-card': '20px',
    '--store-radius-pill': '999px',
    '--store-radius-control': '14px',
    '--store-transition-fast': '160ms ease',
  },
};

type ThemeContextValue = {
  mode: ThemeMode;
  resolvedTheme: ResolvedTheme;
  setMode: (mode: ThemeMode) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function readStoredThemeMode(storageKey: string, defaultMode: ThemeMode) {
  if (typeof window === 'undefined') {
    return defaultMode;
  }
  const storage = window.localStorage as Partial<Storage> | undefined;
  const stored = typeof storage?.getItem === 'function' ? storage.getItem(storageKey) : null;
  return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : defaultMode;
}

function readSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'light';
  }
  return window.matchMedia(SYSTEM_DARK_QUERY).matches ? 'dark' : 'light';
}

export function resolveThemeMode(mode: ThemeMode, systemTheme: ResolvedTheme = readSystemTheme()): ResolvedTheme {
  if (mode === 'system') {
    return systemTheme;
  }
  return mode;
}

export function useStoreTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useStoreTheme must be used within a StoreThemeProvider');
  }
  return context;
}

export function StoreThemeProvider(
  props: PropsWithChildren<{ storageKey?: string; defaultMode?: ThemeMode }>,
) {
  const storageKey = props.storageKey ?? DEFAULT_STORAGE_KEY;
  const [mode, setMode] = useState<ThemeMode>(() => readStoredThemeMode(storageKey, props.defaultMode ?? 'system'));
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(() => readSystemTheme());

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const storage = window.localStorage as Partial<Storage> | undefined;
    if (typeof storage?.setItem === 'function') {
      storage.setItem(storageKey, mode);
    }
  }, [mode, storageKey]);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }

    const mediaQuery = window.matchMedia(SYSTEM_DARK_QUERY);
    const listener = (event: MediaQueryListEvent) => {
      setSystemTheme(event.matches ? 'dark' : 'light');
    };

    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }

    mediaQuery.addListener(listener);
    return () => mediaQuery.removeListener(listener);
  }, []);

  const resolvedTheme = resolveThemeMode(mode, systemTheme);
  const value = useMemo<ThemeContextValue>(() => ({ mode, resolvedTheme, setMode }), [mode, resolvedTheme]);

  return (
    <ThemeContext.Provider value={value}>
      <div
        data-store-theme={resolvedTheme}
        style={themeTokens[resolvedTheme] as React.CSSProperties}
      >
        {props.children}
      </div>
    </ThemeContext.Provider>
  );
}

function modeButtonStyle(active: boolean): React.CSSProperties {
  return {
    border: 0,
    borderRadius: 'var(--store-radius-pill, 999px)',
    padding: '8px 12px',
    background: active ? 'var(--store-accent, #1f4fbf)' : 'transparent',
    color: active ? '#ffffff' : 'var(--store-text-default, #25314f)',
    fontSize: '12px',
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'background var(--store-transition-fast, 160ms ease), color var(--store-transition-fast, 160ms ease)',
  };
}

export function StoreThemeModeToggle() {
  const theme = useStoreTheme();

  return (
    <div
      aria-label="Theme mode"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px',
        borderRadius: 'var(--store-radius-pill, 999px)',
        background: 'var(--store-surface-muted, rgba(237,241,248,0.96))',
        border: '1px solid var(--store-border-soft, rgba(23,32,51,0.10))',
      }}
    >
      <button type="button" onClick={() => theme.setMode('light')} style={modeButtonStyle(theme.mode === 'light')} aria-label="Light theme">
        Light
      </button>
      <button type="button" onClick={() => theme.setMode('dark')} style={modeButtonStyle(theme.mode === 'dark')} aria-label="Dark theme">
        Dark
      </button>
      <button type="button" onClick={() => theme.setMode('system')} style={modeButtonStyle(theme.mode === 'system')} aria-label="System theme">
        System
      </button>
    </div>
  );
}
