import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const controlPlaneOrigin = process.env.STORE_CONTROL_PLANE_ORIGIN ?? 'http://127.0.0.1:18000';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/v1': controlPlaneOrigin,
    },
  },
});
