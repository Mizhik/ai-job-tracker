import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendTarget = env.VITE_BACKEND_TARGET || 'http://localhost:8000';

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/users': {
          target: backendTarget,
          changeOrigin: true,
        },
        '/jobs': {
          target: backendTarget,
          changeOrigin: true,
        },
        '/applications': {
          target: backendTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
