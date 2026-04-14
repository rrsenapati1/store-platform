export type BrowserSentryLike = {
  init: (config: {
    dsn: string;
    environment: string;
    release?: string;
    tracesSampleRate: number;
  }) => void;
};

export type BrowserSentryEnv = {
  DEV: boolean;
  MODE?: string;
  VITE_SENTRY_DSN?: string;
  VITE_DEPLOYMENT_ENVIRONMENT?: string;
  VITE_RELEASE_VERSION?: string;
  VITE_SENTRY_TRACES_SAMPLE_RATE?: string;
};

function trimString(value: string | undefined): string | undefined {
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
}

function parseSampleRate(value: string | undefined): number {
  if (!value) {
    return 0;
  }
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function shouldEnableSentry(env: BrowserSentryEnv): boolean {
  return Boolean(trimString(env.VITE_SENTRY_DSN)) && !env.DEV && env.MODE !== 'test';
}

export function initializeSentry(env: BrowserSentryEnv, sentry: BrowserSentryLike): boolean {
  const dsn = trimString(env.VITE_SENTRY_DSN);
  if (!dsn || !shouldEnableSentry(env)) {
    return false;
  }
  sentry.init({
    dsn,
    environment: trimString(env.VITE_DEPLOYMENT_ENVIRONMENT) || env.MODE || 'production',
    release: trimString(env.VITE_RELEASE_VERSION),
    tracesSampleRate: parseSampleRate(env.VITE_SENTRY_TRACES_SAMPLE_RATE),
  });
  return true;
}
