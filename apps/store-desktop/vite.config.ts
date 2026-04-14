import os from 'node:os';
import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const vitestLocalStoragePath = path.join(os.tmpdir(), 'store-desktop-vitest-localstorage');

export default defineConfig({
  plugins: [react()],
  test: {
    poolOptions: {
      forks: {
        execArgv: [`--localstorage-file=${vitestLocalStoragePath}`],
      } as unknown as Record<string, unknown>,
    },
    setupFiles: './src/test/setup.ts',
  },
});
