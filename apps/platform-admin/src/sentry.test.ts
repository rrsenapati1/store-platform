import { describe, expect, test, vi } from 'vitest';
import { initializeSentry } from './sentry';


function buildEnv(overrides: Record<string, unknown> = {}) {
  return {
    DEV: false,
    MODE: 'production',
    VITE_SENTRY_DSN: 'https://public@example.ingest.sentry.io/1',
    VITE_DEPLOYMENT_ENVIRONMENT: 'prod',
    VITE_RELEASE_VERSION: '2026.04.15-1',
    VITE_SENTRY_TRACES_SAMPLE_RATE: '0.25',
    ...overrides,
  };
}


describe('platform-admin sentry bootstrap', () => {
  test('skips initialization without a DSN or in dev mode', () => {
    const fakeSentry = { init: vi.fn() };

    expect(initializeSentry(buildEnv({ VITE_SENTRY_DSN: '' }), fakeSentry)).toBe(false);
    expect(initializeSentry(buildEnv({ DEV: true, MODE: 'development' }), fakeSentry)).toBe(false);
    expect(fakeSentry.init).not.toHaveBeenCalled();
  });

  test('initializes sentry in production with release metadata', () => {
    const fakeSentry = { init: vi.fn() };

    expect(initializeSentry(buildEnv(), fakeSentry)).toBe(true);

    expect(fakeSentry.init).toHaveBeenCalledWith(
      expect.objectContaining({
        dsn: 'https://public@example.ingest.sentry.io/1',
        environment: 'prod',
        release: '2026.04.15-1',
        tracesSampleRate: 0.25,
      }),
    );
  });
});
