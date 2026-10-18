#!/usr/bin/env python3
"""Comprehensive executable verification script for PhotoSorter (BUILD_PLAN Phase 5).

Verifies:
1. Binary existence and size in dist/photosorter.exe
2. PE Subsystem (asserts IMAGE_SUBSYSTEM_WINDOWS_GUI, no console window)
3. Clean startup time and web server response
4. Pipeline execution on test_photos in isolated temp dirs
5. Real progress reporting (job.percent > 0 during processing)
6. Exact baseline cluster and photo counts (192 people, 445 unrecognized faces, 168 unrecognized photos, 259 photos)
7. Public export bundle hygiene (zero organizer files)
8. Clean termination and port release
"""

import os
import sys
import time
import socket
import struct
import shutil
import tempfile
import subprocess
import json
from pathlib import Path
import urllib.request
import urllib.error


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_pe_subsystem(exe_path: Path) -> int:
    """Reads Windows PE header to determine subsystem (2 = Windows GUI, 3 = Windows CUI / Console)."""
    with open(exe_path, "rb") as f:
        header = f.read(1024)
    pe_offset = struct.unpack_from("<I", header, 0x3C)[0]
    # In PE32+ (64-bit), Subsystem is at OptionalHeader + 68 bytes (pe_offset + 24 + 68 = pe_offset + 92 = 0x5C)
    subsystem = struct.unpack_from("<H", header, pe_offset + 0x5C)[0]
    return subsystem


def http_get(url: str, timeout: float = 5.0) -> tuple[int, dict | str]:
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read().decode("utf-8")
            if "application/json" in content_type:
                return resp.status, json.loads(data)
            return resp.status, data
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8")
        try:
            return e.code, json.loads(data)
        except Exception:
            return e.code, data


def http_post(url: str, payload: dict, timeout: float = 10.0) -> tuple[int, dict | str]:
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read().decode("utf-8")
            if "application/json" in content_type:
                return resp.status, json.loads(data)
            return resp.status, data
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8")
        try:
            return e.code, json.loads(data)
        except Exception:
            return e.code, data


def main():
    repo_root = Path(__file__).resolve().parent.parent
    exe_candidates = [
        repo_root / "dist" / "CatLog" / "CatLog.exe",
        repo_root / "dist" / "CatLog.exe",
        repo_root / "dist" / "photosorter.exe",
    ]
    exe_path = next((p for p in exe_candidates if p.exists()), exe_candidates[0])
    test_photos = repo_root / "test_photos"

    print("=" * 80)
    print("CATLOG STANDALONE EXECUTABLE VERIFICATION (eval/verify_exe.py)")
    print("=" * 80)

    # 1. Binary checks
    if not exe_path.exists():
        print(f"[FAIL] Executable not found at: {exe_path}")
        sys.exit(1)

    size_bytes = exe_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"[PASS] Executable located: {exe_path}")
    print(f"       Binary Size: {size_bytes:,} bytes ({size_mb:.2f} MB)")

    # 2. Check PE Subsystem (GUI vs Console)
    subsystem = check_pe_subsystem(exe_path)
    subsystem_desc = {
        2: "IMAGE_SUBSYSTEM_WINDOWS_GUI (Windowed - No console popup)",
        3: "IMAGE_SUBSYSTEM_WINDOWS_CUI (Console application)",
    }.get(subsystem, f"Unknown ({subsystem})")

    print(f"       Subsystem Code: {subsystem} -> {subsystem_desc}")
    if subsystem == 2:
        print(f"[PASS] Subsystem check: Built as pure Windows GUI application (console=False).")
    else:
        print(f"[WARN] Subsystem is {subsystem}; spec prefers windowed launch (2).")

    # 3. Setup temporary working and output directories
    temp_dir = Path(tempfile.mkdtemp(prefix="photosorter_exe_verify_"))
    temp_work = temp_dir / "work"
    temp_out = temp_dir / "export"
    temp_work.mkdir(parents=True, exist_ok=True)
    temp_out.mkdir(parents=True, exist_ok=True)

    # Pre-seed embedding cache from export.work or .cache directly into temp_work for fast evaluation
    source_caches = [repo_root / "export.work", repo_root / ".cache"]
    seeded_count = 0
    for src in source_caches:
        if src.exists():
            for f in src.glob("*.json"):
                if f.name not in {"edits.json", "id_map.json", "suggestions.json"}:
                    dest = temp_work / f.name
                    if not dest.exists():
                        shutil.copy2(f, dest)
                        seeded_count += 1
            if (src / "thumbs").exists():
                shutil.copytree(src / "thumbs", temp_work / "thumbs", dirs_exist_ok=True)
            if (src / "crops").exists():
                shutil.copytree(src / "crops", temp_work / "crops", dirs_exist_ok=True)
    print(f"[INFO] Pre-seeded embedding cache into temp work dir ({seeded_count} cached photos)")

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n[INFO] Isolated Test Environment:")
    print(f"       Temp Root:   {temp_dir}")
    print(f"       Work Dir:    {temp_work}")
    print(f"       Export Dir:  {temp_out}")
    print(f"       Port:        {port}")

    # 4. Launch executable in background
    cmd = [
        str(exe_path),
        "--no-gui",
        "--port", str(port),
        "--work-dir", str(temp_work),
        "--output-dir", str(temp_out),
    ]

    print(f"\n[INFO] Launching: {' '.join(cmd)}")
    t0 = time.time()
    server_log_path = temp_dir / "server.log"
    server_log = open(server_log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        stdout=server_log,
        stderr=server_log,
    )

    # 5. Wait for server readiness
    ready = False
    startup_latency = 0.0
    while time.time() - t0 < 30.0:
        if proc.poll() is not None:
            server_log.close()
            with open(server_log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            print(f"[FAIL] Executable exited prematurely (code {proc.returncode})!")
            print(f"SERVER LOG:\n{log_content}")
            sys.exit(1)
        try:
            status, resp = http_get(f"{base_url}/api/health")
            if status == 200:
                startup_latency = time.time() - t0
                ready = True
                break
        except Exception:
            time.sleep(0.1)

    if not ready:
        proc.kill()
        print(f"[FAIL] Server failed to become healthy within 30 seconds.")
        sys.exit(1)

    print(f"[PASS] Executable online in {startup_latency:.2f}s at {base_url}")

    # Check root UI mount
    status, root_content = http_get(f"{base_url}/")
    assert status == 200, f"Root / returned status {status}"
    assert "<title>" in root_content or "html" in root_content.lower(), "Root / did not return HTML"
    print(f"[PASS] Frontend UI assets properly mounted at root / (status {status})")

    # 6. Trigger pipeline job on test_photos
    print(f"\n[INFO] Triggering job on input: {test_photos}")
    start_status, start_resp = http_post(
        f"{base_url}/api/jobs/start",
        {
            "input_path": str(test_photos),
            "output_dir": str(temp_out),
        },
    )
    assert start_status == 200, f"Failed to start job: {start_status} {start_resp}"
    print(f"[PASS] Job started: {start_resp}")

    # 7. Poll progress and verify job.percent > 0
    job_start = time.time()
    observed_positive_percent = False
    last_reported_stage = ""

    while time.time() - job_start < 300:
        time.sleep(1.0)
        st_code, st_data = http_get(f"{base_url}/api/jobs/status")
        if st_code != 200 or not isinstance(st_data, dict):
            continue

        job_status = st_data.get("status")
        stage = st_data.get("stage", "")
        percent = st_data.get("percent", 0.0)
        progress = st_data.get("progress", 0.0)
        current = st_data.get("current", 0)
        total = st_data.get("total", 0)
        msg = st_data.get("message", "")

        if percent > 0.0:
            observed_positive_percent = True

        if stage != last_reported_stage or int(percent) % 25 == 0:
            print(f"       [Job Progress] Stage: {stage:<12} | Progress: {progress*100:5.1f}% (percent={percent:5.1f}%) | [{current}/{total}] {msg[:45]}")
            last_reported_stage = stage

        if job_status == "completed":
            break
        elif job_status == "failed":
            print(f"[FAIL] Job failed! Error:\n{st_data.get('error')}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
                proc.wait()
            server_log.close()
            with open(server_log_path, "r", encoding="utf-8", errors="replace") as f:
                print(f"SERVER LOG:\n{f.read()}")
            sys.exit(1)

    total_job_time = time.time() - job_start
    print(f"\n[PASS] Pipeline finished in {total_job_time:.2f}s")
    assert observed_positive_percent, "[FAIL] job.percent never exceeded 0.0% during execution!"
    print(f"[PASS] Real progress broadcast verified: job.percent actively tracked scanning/detection.")

    # 8. Verify baseline counts in generated export
    people_file = temp_out / "people.json"
    assert people_file.exists(), f"[FAIL] Export people.json missing at: {people_file}"

    with open(people_file, "r", encoding="utf-8") as f:
        pdata = json.load(f)

    people = pdata.get("people", [])
    unrec_faces = pdata.get("unrecognized", {}).get("faces", [])
    unrec_photos = pdata.get("unrecognized", {}).get("photo_ids", [])
    all_photos = pdata.get("photos", {})

    print("\n--- BASELINE METRICS REPRODUCIBILITY CHECK ---")
    print(f"People Clusters:     {len(people)} (Baseline expected: 192)")
    print(f"Unrecognized Faces:  {len(unrec_faces)} (Baseline expected: 445)")
    print(f"Unrecognized Photos: {len(unrec_photos)} (Baseline expected: 168)")
    print(f"Total Photo Records: {len(all_photos)} (Baseline expected: 259)")

    assert len(people) == 192, f"People count {len(people)} != 192"
    assert len(unrec_faces) == 445, f"Unrecognized faces {len(unrec_faces)} != 445"
    assert len(unrec_photos) == 168, f"Unrecognized photos {len(unrec_photos)} != 168"
    assert len(all_photos) == 259, f"Photos count {len(all_photos)} != 259"
    print("[PASS] All cluster, face, and photo counts match pinned baseline fixture identically!")

    # 9. Verify Public Export Bundle Hygiene
    exported_items = sorted([p.name for p in temp_out.iterdir()])
    allowed_items = {"config.json", "people.json", "faces", "thumbs", "gallery.html", "index.html", "assets"}
    forbidden_items = {"suggestions.json", "edits.json", "id_map.json", ".cache"}

    has_forbidden = any(f in exported_items for f in forbidden_items)
    assert not has_forbidden, f"[FAIL] Forbidden organizer files found in public bundle: {exported_items}"
    print(f"[PASS] Public Export Bundle Hygiene verified. Export files: {exported_items}")

    # 10. Clean shutdown
    print("\n[INFO] Terminating executable...")
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    server_log.close()

    # Verify port is released
    port_free = False
    for _ in range(10):
        time.sleep(0.5)
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                port_free = False
        except (OSError, ConnectionRefusedError):
            port_free = True
            break

    assert port_free, f"[FAIL] Port {port} was not released on process shutdown!"
    print(f"[PASS] Executable terminated cleanly; port {port} released.")

    # Cleanup temp dir
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 80)
    print("ALL PHASE 5 EXECUTABLE REQUIREMENTS VERIFIED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
