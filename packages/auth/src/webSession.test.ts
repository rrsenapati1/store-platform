/* @vitest-environment jsdom */
import { beforeEach, describe, expect, test, vi } from 'vitest';
import * as auth from './index';

type MutableWindowLike = {
  location: {
    pathname: string;
    search: string;
    hash: string;
  };
  history: {
    replaceState: (state: unknown, title: string, nextUrl?: string | URL | null) => void;
  };
};

function createWindowLike(url: string): MutableWindowLike {
  const parsed = new URL(url, 'https://store.local');
  const targetWindow: MutableWindowLike = {
    location: {
      pathname: parsed.pathname,
      search: parsed.search,
      hash: parsed.hash,
    },
    history: {
      replaceState: (_state: unknown, _title: string, nextUrl?: string | URL | null) => {
        const next = new URL(`${nextUrl ?? parsed.pathname}`, 'https://store.local');
        targetWindow.location.pathname = next.pathname;
        targetWindow.location.search = next.search;
        targetWindow.location.hash = next.hash;
      },
    },
  };
  return targetWindow;
}

describe('shared web session helpers', () => {
  beforeEach(() => {
    const backingStore = new Map<string, string>();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: {
        clear: () => backingStore.clear(),
        getItem: (key: string) => backingStore.get(key) ?? null,
        removeItem: (key: string) => {
          backingStore.delete(key);
        },
        setItem: (key: string, value: string) => {
          backingStore.set(key, value);
        },
      },
    });
  });

  test('parses and consumes korsenex callback params from the browser URL', () => {
    const targetWindow = createWindowLike('/owner/callback?tab=overview&token=oidc-token&state=flow-1');

    const callback = (auth as Record<string, unknown>).readKorsenexCallback as
      | ((windowLike: Window) => { token: string | null; state: string | null; error: string | null })
      | undefined;

    expect(callback?.(targetWindow as never)).toEqual({
      error: null,
      state: 'flow-1',
      token: 'oidc-token',
    });
    expect(targetWindow.location.pathname).toBe('/owner/callback');
    expect(targetWindow.location.search).toBe('?tab=overview');
    expect(targetWindow.location.hash).toBe('');
  });

  test('persists and restores a browser session record', () => {
    localStorage.clear();

    const saveSession = (auth as Record<string, unknown>).saveStoreWebSession as
      | ((storageKey: string, record: { accessToken: string; expiresAt: string }) => void)
      | undefined;
    const loadSession = (auth as Record<string, unknown>).loadStoreWebSession as
      | ((storageKey: string) => { accessToken: string; expiresAt: string } | null)
      | undefined;

    saveSession?.('owner-session', {
      accessToken: 'owner-token',
      expiresAt: '2026-04-19T10:00:00.000Z',
    });

    expect(loadSession?.('owner-session')).toEqual({
      accessToken: 'owner-token',
      expiresAt: '2026-04-19T10:00:00.000Z',
    });
  });

  test('detects expired sessions from the expiry timestamp', () => {
    const isExpired = (auth as Record<string, unknown>).isStoreWebSessionExpired as
      | ((record: { accessToken: string; expiresAt: string }, now?: number) => boolean)
      | undefined;

    expect(
      isExpired?.(
        {
          accessToken: 'owner-token',
          expiresAt: '2026-04-19T09:59:59.000Z',
        },
        Date.parse('2026-04-19T10:00:00.000Z'),
      ),
    ).toBe(true);

    expect(
      isExpired?.(
        {
          accessToken: 'owner-token',
          expiresAt: '2026-04-19T10:05:00.000Z',
        },
        Date.parse('2026-04-19T10:00:00.000Z'),
      ),
    ).toBe(false);
  });

  test('detects when a live session should be refreshed ahead of expiry', () => {
    const shouldRefresh = (auth as Record<string, unknown>).shouldRefreshStoreWebSession as
      | ((record: { accessToken: string; expiresAt: string }, now?: number, leadSeconds?: number) => boolean)
      | undefined;

    expect(
      shouldRefresh?.(
        {
          accessToken: 'owner-token',
          expiresAt: '2026-04-19T10:02:00.000Z',
        },
        Date.parse('2026-04-19T10:00:30.000Z'),
        120,
      ),
    ).toBe(true);

    expect(
      shouldRefresh?.(
        {
          accessToken: 'owner-token',
          expiresAt: '2026-04-19T10:10:00.000Z',
        },
        Date.parse('2026-04-19T10:00:30.000Z'),
        120,
      ),
    ).toBe(false);
  });

  test('clears persisted session state after sign-out', async () => {
    localStorage.setItem(
      'owner-session',
      JSON.stringify({
        accessToken: 'owner-token',
        expiresAt: '2026-04-19T10:00:00.000Z',
      }),
    );
    const signOut = vi.fn(async () => undefined);
    const signOutSession = (auth as Record<string, unknown>).signOutStoreWebSession as
      | ((args: { storageKey: string; accessToken: string; signOut: (accessToken: string) => Promise<void> }) => Promise<void>)
      | undefined;

    await signOutSession?.({
      storageKey: 'owner-session',
      accessToken: 'owner-token',
      signOut,
    });

    expect(signOut).toHaveBeenCalledWith('owner-token');
    expect(localStorage.getItem('owner-session')).toBeNull();
  });

  test('keeps local-dev bootstrap parsing separate from production callback parsing', () => {
    const targetWindow = createWindowLike('/owner#stub_sub=owner-1&stub_email=owner@acme.local&stub_name=Acme%20Owner');
    const callback = (auth as Record<string, unknown>).readKorsenexCallback as
      | ((windowLike: Window) => { token: string | null; state: string | null; error: string | null })
      | undefined;

    expect(
      auth.readLocalDevBootstrap({
        hash: targetWindow.location.hash,
      }),
    ).toEqual({
      autoClockIn: false,
      autoOpenCashier: false,
      autoStart: true,
      korsenexToken: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner',
    });
    expect(callback?.(targetWindow as never)).toEqual({
      error: null,
      state: null,
      token: null,
    });
  });
});
