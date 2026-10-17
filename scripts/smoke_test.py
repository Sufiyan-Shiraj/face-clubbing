"""Smoke test for CatLog standalone executable across all platforms.

Launches the built binary in --no-gui mode on a free port, validates
that /api/health responds with status 'ok' and matching version,
and cleanly terminates the process.
"""

from __future__ import annotations
import os
import sys
import time
import socket
import urllib.request
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_smoke_test(exe_path: str | Path | None = None) -> bool:
    print("=" * 70)
    print("CATLOG STANDALONE EXECUTABLE SMOKE TEST")
    print("=" * 70)

    if exe_path is None:
        if sys.platform.startswith("win"):
            candidates = [REPO_ROOT / "dist" / "CatLog.exe", REPO_ROOT / "dist" / "CatLog" / "CatLog.exe"]
        else:
            candidates = [REPO_ROOT / "dist" / "CatLog", REPO_ROOT / "dist" / "CatLog" / "CatLog"]
        for c in candidates:
            if c.exists():
                exe_path = c
                break

    if not exe_path or not Path(exe_path).exists():
        print(f"[FAIL] Executable not found. Checked: {candidates if 'candidates' in locals() else exe_path}")
        return False

    exe_path = Path(exe_path).resolve()
    print(f"[INFO] Executable: {exe_path} ({exe_path.stat().st_size:,} bytes)")

    # Read expected version from VERSION file
    version_file = REPO_ROOT / "VERSION"
    expected_version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else None
    print(f"[INFO] Expected Version: {expected_version}")

    port = find_free_port()
    cmd = [str(exe_path), "--no-gui", "--port", str(port)]
    print(f"[INFO] Launching: {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    t0 = time.time()
    healthy = False
    health_payload = {}
    timeout = 45.0

    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=2)
            print(f"[FAIL] Executable exited prematurely with code {proc.returncode}!")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return False

        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    health_payload = json.loads(resp.read().decode("utf-8"))
                    healthy = True
                    break
        except Exception:
            time.sleep(0.5)

    if not healthy:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except Exception:
            proc.kill()
        print(f"[FAIL] Health check timed out after {timeout}s.")
        return False

    dt = time.time() - t0
    print(f"[PASS] /api/health answered in {dt:.2f}s: {health_payload}")

    # Validate status and version
    if health_payload.get("status") != "ok":
        print(f"[FAIL] Expected status 'ok', got {health_payload.get('status')}")
        proc.terminate()
        return False

    if expected_version and health_payload.get("version") != expected_version:
        print(f"[FAIL] Version mismatch: expected {expected_version}, got {health_payload.get('version')}")
        proc.terminate()
        return False

    print(f"[PASS] Version verification passed: {health_payload.get('version')}")

    # Terminate cleanly
    print("[INFO] Terminating executable...")
    proc.terminate()
    try:
        proc.wait(timeout=10.0)
        print("[PASS] Executable terminated cleanly.")
    except subprocess.TimeoutExpired:
        print("[WARNING] Process did not terminate within 10s, killing...")
        proc.kill()
        proc.wait(timeout=5.0)

    print("=" * 70)
    print("ALL SMOKE CHECKS PASSED")
    print("=" * 70)
    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_smoke_test(target)
    sys.exit(0 if success else 1)
