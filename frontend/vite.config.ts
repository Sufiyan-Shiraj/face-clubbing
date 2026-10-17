import { createLogger, defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Suppress noisy terminal stack dumps when proxy target is connecting or restarting
const customLogger = createLogger();
const originalLoggerError = customLogger.error;
customLogger.error = (msg, options) => {
  if (typeof msg === 'string' && (msg.includes('http proxy error') || msg.includes('ECONNREFUSED'))) {
    return;
  }
  originalLoggerError(msg, options);
};

// https://vitejs.dev/config/
export default defineConfig({
  customLogger,
  plugins: [react()],
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@viewer': path.resolve(__dirname, '../viewer/src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Backend server not ready yet. Please ensure backend is running.' }));
            }
          });
        },
      },
      '/faces': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Backend server not ready yet.' }));
            }
          });
        },
      },
      '/thumbs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (_err, _req, res) => {
            if (res && !res.headersSent && typeof res.writeHead === 'function') {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Backend server not ready yet.' }));
            }
          });
        },
      },
    },
    fs: {
      allow: ['..'],
    },
  },
});
