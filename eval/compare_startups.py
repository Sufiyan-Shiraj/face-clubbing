#!/usr/bin/env python3
"""Measures cold start time to /api/health for PyInstaller onedir vs onefile (3 runs each)."""

from __future__ import annotations
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def measure_single_run(exe_path: Path, timeout: float = 45.0) -> float:
    port = find_free_port()
    cmd = [str(exe_path), "--no-gui", "--port", str(port)]
    
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    health_url = f"http://127.0.0.1:{port}/api/health"
    ready = False
    elapsed = 0.0
    
    try:
        while time.perf_counter() - t0 < timeout:
            if proc.poll() is not None:
                raise RuntimeError(f"Executable {exe_path.name} exited prematurely with code {proc.returncode}")
            try:
                with urllib.request.urlopen(health_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        elapsed = time.perf_counter() - t0
                        ready = True
                        break
            except Exception:
                time.sleep(0.05)
        
        if not ready:
            raise TimeoutError(f"Executable {exe_path.name} failed to answer /api/health within {timeout}s")
            
        return elapsed
    finally:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        
        # Wait for port release
        for _ in range(20):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    time.sleep(0.1)
            except (OSError, ConnectionRefusedError):
                break


def run_benchmark():
    repo_root = Path(__file__).resolve().parent.parent
    onefile_exe = repo_root / "dist" / "CatLog.exe"
    onedir_exe = repo_root / "dist" / "CatLog_onedir" / "CatLog.exe"
    
    print("=" * 70)
    print("PYINSTALLER STARTUP BENCHMARK: ONEFILE VS ONEDIR (3 COLD RUNS EACH)")
    print("=" * 70)
    
    if not onefile_exe.exists():
        print(f"[FAIL] Onefile executable not found at: {onefile_exe}")
        sys.exit(1)
        
    if not onedir_exe.exists():
        print(f"[FAIL] Onedir executable not found at: {onedir_exe}")
        sys.exit(1)
        
    results = {
        "onefile": {
            "path": str(onefile_exe),
            "size_bytes": onefile_exe.stat().st_size,
            "runs": [],
        },
        "onedir": {
            "path": str(onedir_exe),
            "size_bytes": onedir_exe.stat().st_size,
            "runs": [],
        },
    }
    
    # 3 runs of onefile
    print(f"\n[INFO] Measuring Onefile: {onefile_exe} ({onefile_exe.stat().st_size:,} bytes)")
    for i in range(1, 4):
        time.sleep(2.0)  # cooldown
        t = measure_single_run(onefile_exe)
        results["onefile"]["runs"].append(t)
        print(f"  Run {i}: {t:.3f} s")
        
    # 3 runs of onedir
    print(f"\n[INFO] Measuring Onedir: {onedir_exe}")
    for i in range(1, 4):
        time.sleep(2.0)  # cooldown
        t = measure_single_run(onedir_exe)
        results["onedir"]["runs"].append(t)
        print(f"  Run {i}: {t:.3f} s")
        
    # Compute summaries
    of_runs = results["onefile"]["runs"]
    od_runs = results["onedir"]["runs"]
    
    results["onefile"]["mean"] = sum(of_runs) / len(of_runs)
    results["onefile"]["min"] = min(of_runs)
    results["onefile"]["max"] = max(of_runs)
    
    results["onedir"]["mean"] = sum(od_runs) / len(od_runs)
    results["onedir"]["min"] = min(od_runs)
    results["onedir"]["max"] = max(od_runs)
    
    speedup = results["onefile"]["mean"] / results["onedir"]["mean"]
    results["speedup"] = speedup
    
    out_file = repo_root / "scratch" / "startup_benchmark.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print(f"Onefile: {of_runs[0]:.3f}s, {of_runs[1]:.3f}s, {of_runs[2]:.3f}s | Mean: {results['onefile']['mean']:.3f}s")
    print(f"Onedir:  {od_runs[0]:.3f}s, {od_runs[1]:.3f}s, {od_runs[2]:.3f}s | Mean: {results['onedir']['mean']:.3f}s")
    print(f"Ratio (Onefile / Onedir): {speedup:.2f}x faster with onedir")
    print(f"Results written to: {out_file}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
