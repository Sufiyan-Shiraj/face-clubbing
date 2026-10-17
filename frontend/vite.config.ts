import { createLogger, defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import net from 'net';
import fs from 'fs';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Suppress noisy terminal stack dumps when proxy target is temporarily connecting
const customLogger = createLogger();
const originalLoggerError = customLogger.error;
customLogger.error = (msg, options) => {
  if (typeof msg === 'string' && (msg.includes('http proxy error') || msg.includes('ECONNREFUSED'))) {
    return;
  }
  originalLoggerError(msg, options);
};

// Auto-spawn FastAPI backend on port 8000 if not already running
function autoBackendPlugin(): Plugin {
  return {
    name: 'auto-backend-server',
    configureServer() {
      const sock = new net.Socket();
      sock.setTimeout(600);
      sock.on('connect', () => {
        sock.destroy();
      });
      sock.on('error', () => {
        sock.destroy();
        const repoRoot = path.resolve(__dirname, '..');
        const isWin = process.platform === 'win32';
        const candidatePaths = isWin
          ? [
              path.resolve(repoRoot, '.venv', 'Scripts', 'python.exe'),
              path.resolve(repoRoot, 'venv', 'Scripts', 'python.exe'),
              'python'
            ]
          : [
              path.resolve(repoRoot, '.venv', 'bin', 'python'),
              path.resolve(repoRoot, 'venv', 'bin', 'python'),
              'python3',
              'python'
            ];
        const pythonPath = candidatePaths.find(p => p === 'python' || p === 'python3' || fs.existsSync(p)) || (isWin ? 'python' : 'python3');
        try {
          const child = spawn(pythonPath, ['-m', 'uvicorn', 'backend.api.app:app', '--host', '127.0.0.1', '--port', '8000'], {
            cwd: repoRoot,
            stdio: 'ignore',
            detached: true,
          });
          child.unref();
        } catch {
          // ignore spawn failure
        }
      });
      sock.on('timeout', () => {
        sock.destroy();
      });
      sock.connect(8000, '127.0.0.1');
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  customLogger,
  plugins: [react(), autoBackendPlugin()],
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
