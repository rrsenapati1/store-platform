import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { initializeSentry, shouldEnableSentry } from './sentry';

const root = ReactDOM.createRoot(document.getElementById('root')!);

async function bootstrap() {
  if (shouldEnableSentry(import.meta.env)) {
    try {
      const Sentry = await import('@sentry/react');
      initializeSentry(import.meta.env, Sentry);
    } catch (error) {
      console.warn('Unable to initialize Sentry for owner-web', error);
    }
  }

  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

void bootstrap();
