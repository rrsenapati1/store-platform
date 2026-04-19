import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const controlPlaneOrigin = process.env.STORE_CONTROL_PLANE_ORIGIN ?? 'http://127.0.0.1:18000';
const workspaceRoot = path.resolve(__dirname, '../..');
const storeAliases = {
  '@store/auth': path.join(workspaceRoot, 'packages/auth/src/index.ts'),
  '@store/barcode': path.join(workspaceRoot, 'packages/barcode/src/index.ts'),
  '@store/printing': path.join(workspaceRoot, 'packages/printing/src/index.ts'),
  '@store/sync': path.join(workspaceRoot, 'packages/sync/src/index.ts'),
  '@store/types': path.join(workspaceRoot, 'packages/types/src/index.ts'),
  '@store/ui': path.join(workspaceRoot, 'packages/ui/src/index.tsx'),
};

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: storeAliases,
  },
  server: {
    proxy: {
      '/v1': controlPlaneOrigin,
    },
  },
});
