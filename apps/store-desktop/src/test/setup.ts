import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  try {
    globalThis.localStorage?.clear();
  } catch {
    // Some tests replace browser storage with partial stubs; teardown should stay best-effort.
  }
  cleanup();
});
