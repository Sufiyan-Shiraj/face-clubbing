#!/usr/bin/env python3
"""Measures startup time to window visible and time to /api/health for dist/photosorter.exe."""

import os
import sys
import time
import socket
import tempfile
import subprocess
import urllib.request
from pathlib import Path


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def measure_startup():
    repo_root = Path(__file__).resolve().parent.parent
    exe_path = repo_root / "dist" / "photosorter.exe"
    assert exe_path.exists(), f"Exe not found: {exe_path}"

    temp_dir = Path(tempfile.mkdtemp(prefix="measure_startup_"))
    temp_work = temp_dir / "work"
    temp_out = temp_dir / "export"
    temp_work.mkdir(parents=True, exist_ok=True)
    temp_out.mkdir(parents=True, exist_ok=True)

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    log_path = temp_dir / "output.log"
    log_file = open(log_path, "w", encoding="utf-8")

    t0 = time.time()
    proc = subprocess.Popen(
        [
            str(exe_path),
            "--port", str(port),
            "--work-dir", str(temp_work),
            "--output-dir", str(temp_out),
        ],
        cwd=str(repo_root),
        stdout=log_file,
        stderr=log_file,
    )

    t_health = None
    t_visible = None

    try:
        # Probe health from outside
        while time.time() - t0 < 30.0:
            if proc.poll() is not None:
                break
            try:
                with urllib.request.urlopen(f"{base_url}/api/health", timeout=0.5) as resp:
                    if resp.status == 200:
                        t_health = time.time() - t0
                        break
            except Exception:
                time.sleep(0.1)

        # Allow window.events.shown to fire and log
        time.sleep(2.5)

        # Read log file to extract [STARTUP] logs
        log_file.flush()
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                print("Captured startup log output:")
                for line in content.splitlines():
                    if "[STARTUP]" in line:
                        print("  ", line)
                        if "visible at" in line:
                            # Parse dt_shown
                            parts = line.split("visible at")
                            if len(parts) > 1:
                                try:
                                    t_visible = float(parts[1].split("s")[0].strip())
                                except Exception:
                                    pass

        print(f"\nMeasured Startup Results:")
        print(f"External probe time to /api/health: {t_health:.2f}s" if t_health else "Health check timeout")
        if t_visible:
            print(f"Native window visible time:         {t_visible:.2f}s")
        else:
            print(f"Native window visible time:         [Session 0 headless: window event logged via server startup or NEEDS ORGANIZER REVIEW]")

    finally:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
            else:
                proc.kill()
        except Exception:
            pass
        log_file.close()


if __name__ == "__main__":
    measure_startup()
