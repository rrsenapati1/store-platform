import os from 'node:os';
import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const vitestLocalStoragePath = path.join(os.tmpdir(), 'store-desktop-vitest-localstorage');
const controlPlaneOrigin = process.env.STORE_CONTROL_PLANE_ORIGIN ?? 'http://127.0.0.1:18000';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/v1': controlPlaneOrigin,
    },
  },
  test: {
    testTimeout: 20_000,
    poolOptions: {
      forks: {
        execArgv: [`--localstorage-file=${vitestLocalStoragePath}`],
      } as unknown as Record<string, unknown>,
    },
    setupFiles: './src/test/setup.ts',
  },
});
