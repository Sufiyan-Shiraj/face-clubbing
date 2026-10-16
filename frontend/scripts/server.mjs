import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');

const isWin = process.platform === 'win32';
const candidatePaths = isWin
  ? [
      path.resolve(REPO_ROOT, '.venv', 'Scripts', 'python.exe'),
      path.resolve(REPO_ROOT, 'venv', 'Scripts', 'python.exe'),
      'python'
    ]
  : [
      path.resolve(REPO_ROOT, '.venv', 'bin', 'python'),
      path.resolve(REPO_ROOT, 'venv', 'bin', 'python'),
      'python3',
      'python'
    ];

const pythonPath = candidatePaths.find(p => p === 'python' || p === 'python3' || fs.existsSync(p)) || (isWin ? 'python' : 'python3');

const child = spawn(pythonPath, ['-m', 'uvicorn', 'backend.api.app:app', '--port', '8000', '--reload'], {
  cwd: REPO_ROOT,
  stdio: 'inherit'
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});
