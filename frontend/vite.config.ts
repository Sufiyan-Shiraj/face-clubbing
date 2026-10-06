import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@viewer': path.resolve(__dirname, '../viewer/src'),
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/faces': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/thumbs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
    fs: {
      allow: ['..'],
    },
  },
});
