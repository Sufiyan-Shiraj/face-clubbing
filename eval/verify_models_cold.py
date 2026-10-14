#!/usr/bin/env python3
"""Verification script for Model download behavior, offline error, and cold embedding cache run.

Proves:
1. When model folder is unavailable and network is offline, a clear offline error is returned.
2. With models available in ~/.photosorter/models and a COLD embedding cache (no pre-seeding),
   the exe successfully runs on a 20-photo subset and reports detected faces and people counts.
"""

import os
import sys
import time
import json
import shutil
import socket
import tempfile
import subprocess
from pathlib import Path
import urllib.request
import urllib.error


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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


def kill_proc(proc: subprocess.Popen):
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
    except Exception:
        pass


def test_offline_missing_models(exe_path: Path, repo_root: Path, sample_subset: Path):
    print("\n--- TEST 1: Model folder unavailable & offline error proof ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_models_offline_"))
    temp_work = temp_dir / "work"
    temp_out = temp_dir / "export"
    fake_home = temp_dir / "empty_userprofile"
    temp_work.mkdir(parents=True, exist_ok=True)
    temp_out.mkdir(parents=True, exist_ok=True)
    fake_home.mkdir(parents=True, exist_ok=True)

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["USERPROFILE"] = str(fake_home)
    env["HOME"] = str(fake_home)
    # Block external internet so download fails immediately
    env["HTTP_PROXY"] = "http://127.0.0.1:9"
    env["HTTPS_PROXY"] = "http://127.0.0.1:9"
    env["http_proxy"] = "http://127.0.0.1:9"
    env["https_proxy"] = "http://127.0.0.1:9"

    log_path = temp_dir / "server.log"
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            str(exe_path),
            "--no-gui",
            "--port", str(port),
            "--work-dir", str(temp_work),
            "--output-dir", str(temp_out),
        ],
        cwd=str(repo_root),
        env=env,
        stdout=log_file,
        stderr=log_file,
    )

    try:
        # Wait for health
        t0 = time.time()
        ready = False
        while time.time() - t0 < 30.0:
            if proc.poll() is not None:
                break
            try:
                status, _ = http_get(f"{base_url}/api/health", timeout=1.0)
                if status == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.2)

        assert ready, "Server failed to start"
        print(f"[OK] Server started on port {port} with models absent in {fake_home}")

        # Post job
        post_status, post_data = http_post(
            f"{base_url}/api/jobs/start",
            {"input_path": str(sample_subset), "output_dir": str(temp_out)},
        )
        print(f"[INFO] Job start response: status={post_status}, data={post_data}")

        # Poll until error
        job_error = None
        t0 = time.time()
        while time.time() - t0 < 60.0:
            time.sleep(0.5)
            status, job_data = http_get(f"{base_url}/api/jobs/status")
            if isinstance(job_data, dict):
                job_status = job_data.get("status")
                if job_status in {"error", "failed"}:
                    job_error = job_data.get("error")
                    break

        print(f"[INFO] Caught expected offline error: {job_error}")
        assert job_error is not None, "Expected job error when models are missing and offline"
        assert "InsightFace model 'buffalo_l' is not available" in job_error, f"Unexpected error format: {job_error}"
        assert "Please ensure an internet connection" in job_error, f"Missing offline remediation guidance: {job_error}"
        print("[PASS] Clear offline error verified when model folder is unavailable!")
    finally:
        kill_proc(proc)
        log_file.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_cold_cache_20_photos(exe_path: Path, repo_root: Path, subset_dir: Path):
    print("\n--- TEST 2: COLD embedding cache on 20-photo subset ---")
    temp_dir = Path(tempfile.mkdtemp(prefix="test_cold_cache_"))
    temp_work = temp_dir / "work"
    temp_out = temp_dir / "export"
    temp_work.mkdir(parents=True, exist_ok=True)
    temp_out.mkdir(parents=True, exist_ok=True)

    # Verify cold cache: temp_work MUST NOT contain any pre-seeded .json or .npy or cache files
    cached_items = list(temp_work.iterdir())
    assert len(cached_items) == 0, f"Cache directory not cold! Found: {cached_items}"
    print(f"[OK] Verified COLD embedding cache in {temp_work} (0 pre-seeded files)")

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    log_path = temp_dir / "server.log"
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            str(exe_path),
            "--no-gui",
            "--port", str(port),
            "--work-dir", str(temp_work),
            "--output-dir", str(temp_out),
        ],
        cwd=str(repo_root),
        stdout=log_file,
        stderr=log_file,
    )

    try:
        t0 = time.time()
        ready = False
        while time.time() - t0 < 30.0:
            if proc.poll() is not None:
                break
            try:
                status, _ = http_get(f"{base_url}/api/health", timeout=1.0)
                if status == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.2)

        assert ready, "Server failed to start"
        print(f"[OK] Server started on port {port}")

        # Post job on 20 photos
        post_status, post_data = http_post(
            f"{base_url}/api/jobs/start",
            {"input_path": str(subset_dir), "output_dir": str(temp_out)},
        )
        assert post_status == 200, f"Job start failed: {post_status} {post_data}"
        print(f"[INFO] Started sorting 20-photo subset from: {subset_dir}")

        # Poll job
        t0 = time.time()
        last_msg = ""
        completed = False
        while time.time() - t0 < 360.0:
            time.sleep(1.0)
            status, job_data = http_get(f"{base_url}/api/jobs/status")
            if isinstance(job_data, dict):
                stage = job_data.get("stage", "")
                percent = job_data.get("percent", 0.0)
                job_status = job_data.get("status")
                msg = job_data.get("message", "")
                if msg != last_msg:
                    print(f"       [{job_status}] stage={stage} percent={percent:.1f}% msg={msg}")
                    last_msg = msg
                if job_status == "completed":
                    completed = True
                    break
                if job_status in {"error", "failed"}:
                    raise RuntimeError(f"Job failed unexpectedly: {job_data.get('error')}")

        assert completed, f"Job did not complete within timeout (status={job_status})"
        duration = time.time() - t0
        print(f"[PASS] Cold run on 20 photos completed in {duration:.2f}s")

        # Verify results in export/people.json
        people_json_path = temp_out / "people.json"
        assert people_json_path.exists(), f"people.json missing from {temp_out}"
        with open(people_json_path, "r", encoding="utf-8") as f:
            export_data = json.load(f)

        total_photos = len(export_data.get("photos", {}))
        people_clusters = export_data.get("people", [])
        people_count = len(people_clusters)
        unrecognized = export_data.get("unrecognized", {})
        unrec_faces = unrecognized.get("faces", [])
        unrec_photos = unrecognized.get("photo_ids", [])

        # Count total detected faces across people and unrecognized
        faces_in_clusters = sum(len(p.get("faces", [])) for p in people_clusters)
        total_detected_faces = faces_in_clusters + len(unrec_faces)

        print("\n" + "=" * 50)
        print("COLD CACHE RUN RESULTS (20 Photos):")
        print(f"Total Photos Processed:     {total_photos}")
        print(f"Total Faces Detected:       {total_detected_faces}")
        print(f"  - Faces in Clusters:      {faces_in_clusters}")
        print(f"  - Unrecognized Faces:     {len(unrec_faces)}")
        print(f"People Clusters Count:      {people_count}")
        print(f"Unrecognized Photos Count:  {len(unrec_photos)}")
        print("=" * 50)

        assert total_photos == 20, f"Expected 20 photos processed, got {total_photos}"
        assert total_detected_faces > 0, "No faces detected!"
        assert people_count > 0, "No people clusters formed!"
        print("[PASS] Cold embedding cache test on 20 photos verified successfully!")
    finally:
        kill_proc(proc)
        log_file.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    exe_path = repo_root / "dist" / "photosorter.exe"
    test_photos = repo_root / "test_photos"

    assert exe_path.exists(), f"Executable not found: {exe_path}"

    # Prepare 20-photo subset
    temp_subset_dir = Path(tempfile.mkdtemp(prefix="test_subset_20_"))
    try:
        all_photos = sorted([
            p for p in test_photos.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".heic"}
        ])
        subset_photos = all_photos[:20]
        print(f"[INFO] Preparing 20-photo subset in {temp_subset_dir}")
        for p in subset_photos:
            shutil.copy2(p, temp_subset_dir / p.name)

        # 1. Offline & missing models test
        test_offline_missing_models(exe_path, repo_root, temp_subset_dir)

        # 2. Cold embedding cache run on 20 photos
        test_cold_cache_20_photos(exe_path, repo_root, temp_subset_dir)

    finally:
        shutil.rmtree(temp_subset_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
