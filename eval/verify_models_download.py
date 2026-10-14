#!/usr/bin/env python3
"""Verification script for Model First-Run Download, Time Split, Cold Cache, and Monotonic Progress.

Verifies:
1. Run standalone dist/photosorter.exe with empty USERPROFILE (no pre-existing models).
2. Network enabled: downloads buffalo_l models directly from GitHub releases.
3. Proves legacy ~/.insightface fallback is NOT used (models go to ~/.photosorter/models).
4. Captures all download and pipeline events.
5. Verifies percent never goes backwards and model_init does not start at 100%.
6. Measures exact time split:
   - model download time
   - model load time
   - per-photo detect time
7. Verifies final counts on 20-photo cold cache run.
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


def run_model_download_and_cold_cache_test():
    repo_root = Path(__file__).resolve().parent.parent
    exe_path = repo_root / "dist" / "photosorter.exe"
    test_photos = repo_root / "test_photos"

    assert exe_path.exists(), f"Executable not found: {exe_path}"

    temp_run_dir = Path(tempfile.mkdtemp(prefix="test_models_download_"))
    fake_home = temp_run_dir / "userprofile"
    fake_home.mkdir(parents=True, exist_ok=True)
    temp_work = temp_run_dir / "work"
    temp_out = temp_run_dir / "export"
    temp_work.mkdir(parents=True, exist_ok=True)
    temp_out.mkdir(parents=True, exist_ok=True)
    temp_subset_dir = temp_run_dir / "photos_20"
    temp_subset_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Prepare 20-photo subset
        all_photos = sorted([
            p for p in test_photos.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".heic"}
        ])
        subset_photos = all_photos[:20]
        for p in subset_photos:
            shutil.copy2(p, temp_subset_dir / p.name)

        print("=" * 80)
        print("PHOTOSORTER MODEL FIRST-RUN DOWNLOAD & COLD CACHE TEST")
        print("=" * 80)
        print(f"[INFO] Executable:        {exe_path}")
        print(f"[INFO] Empty USERPROFILE: {fake_home}")
        print(f"[INFO] Cold Work Dir:     {temp_work} (cached files: {len(list(temp_work.iterdir()))})")
        print(f"[INFO] 20-Photo Subset:   {temp_subset_dir} ({len(subset_photos)} photos)")

        # Verify no models exist
        legacy_insightface = fake_home / ".insightface"
        target_photosorter_models = fake_home / ".photosorter" / "models" / "buffalo_l"
        assert not legacy_insightface.exists(), "Legacy .insightface directory must not exist"
        assert not target_photosorter_models.exists(), "Target .photosorter/models must not exist"

        port = find_free_port()
        base_url = f"http://127.0.0.1:{port}"

        env = os.environ.copy()
        env["USERPROFILE"] = str(fake_home)
        env["HOME"] = str(fake_home)
        # Ensure proxies are cleared so network is enabled
        env.pop("HTTP_PROXY", None)
        env.pop("HTTPS_PROXY", None)
        env.pop("http_proxy", None)
        env.pop("https_proxy", None)

        log_path = temp_run_dir / "server.log"
        log_file = open(log_path, "w", encoding="utf-8")
        launch_t0 = time.time()

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
            # Measure time to /api/health
            server_ready = False
            time_to_health = None
            while time.time() - launch_t0 < 45.0:
                if proc.poll() is not None:
                    break
                try:
                    status, _ = http_get(f"{base_url}/api/health", timeout=1.0)
                    if status == 200:
                        server_ready = True
                        time_to_health = time.time() - launch_t0
                        break
                except Exception:
                    time.sleep(0.2)

            assert server_ready, "Server failed to start within 45s"
            print(f"[PASS] Exe online in {time_to_health:.2f}s at {base_url}/api/health")

            # Post job
            job_post_t0 = time.time()
            post_status, post_data = http_post(
                f"{base_url}/api/jobs/start",
                {"input_path": str(temp_subset_dir), "output_dir": str(temp_out)},
            )
            assert post_status == 200, f"Job start failed: {post_status} {post_data}"
            print(f"[INFO] Started sorting 20-photo subset on cold cache & cold models...")

            # Poll events and track timestamps
            events = []
            percentages = []
            last_event_signature = None

            t_download_start = None
            t_download_end = None
            t_load_start = None
            t_load_end = None
            t_detect_start = None
            t_detect_end = None

            timeout = 600.0  # 10 minutes to allow downloading ~300MB
            poll_t0 = time.time()
            completed = False

            while time.time() - poll_t0 < timeout:
                time.sleep(0.5)
                status, job_data = http_get(f"{base_url}/api/jobs/status")
                if not isinstance(job_data, dict):
                    continue

                stage = job_data.get("stage", "")
                percent = job_data.get("percent", 0.0)
                job_status = job_data.get("status")
                msg = job_data.get("message", "")
                current = job_data.get("current", 0)
                total = job_data.get("total", 0)
                now = time.time()

                sig = (stage, percent, msg)
                if sig != last_event_signature:
                    last_event_signature = sig
                    events.append({
                        "elapsed": round(now - job_post_t0, 2),
                        "stage": stage,
                        "percent": percent,
                        "status": job_status,
                        "message": msg,
                        "current": current,
                        "total": total,
                    })
                    percentages.append(percent)
                    print(f"       [{now - job_post_t0:6.2f}s] [{job_status}] stage={stage:<14} percent={percent:5.1f}% | {msg}")

                # Track timing milestones
                if stage == "model_download" and t_download_start is None:
                    t_download_start = now
                if stage == "model_init":
                    if t_download_end is None and t_download_start is not None:
                        t_download_end = now
                    if t_load_start is None:
                        t_load_start = now
                if stage == "processing":
                    if t_load_end is None and t_load_start is not None:
                        t_load_end = now
                    if t_detect_start is None:
                        t_detect_start = now
                if stage in {"clustering", "exporting", "complete"}:
                    if t_detect_end is None and t_detect_start is not None:
                        t_detect_end = now
                if job_status == "completed":
                    completed = True
                    break
                if job_status in {"error", "failed"}:
                    raise RuntimeError(f"Job failed: {job_data.get('error')}")

            assert completed, "Job did not complete within timeout"

            # Check model directory on disk
            assert not legacy_insightface.exists(), "Legacy ~/.insightface directory was unexpectedly created!"
            assert target_photosorter_models.exists(), f"Expected models in {target_photosorter_models}"
            onnx_files = list(target_photosorter_models.glob("*.onnx"))
            print(f"\n[PASS] Legacy ~/.insightface fallback was NOT used.")
            print(f"[PASS] Models downloaded to ~/.photosorter/models/buffalo_l: {len(onnx_files)} ONNX files found:")
            for of in sorted(onnx_files):
                print(f"       - {of.name} ({of.stat().st_size:,} bytes)")

            # Check percentages monotonicity
            model_init_events = [e for e in events if e["stage"] == "model_init"]
            if model_init_events:
                first_model_init = model_init_events[0]
                assert first_model_init["percent"] < 50.0, f"model_init must not start at 100%! Got {first_model_init['percent']}%"
                print(f"[PASS] model_init did not start at 100% (started at {first_model_init['percent']}%)")

            decreases = [
                (percentages[i], percentages[i+1])
                for i in range(len(percentages) - 1)
                if percentages[i+1] < percentages[i]
            ]
            assert len(decreases) == 0, f"Percent went backwards! Violations: {decreases}"
            print("[PASS] Percent strictly non-decreasing throughout entire run (never went backwards)!")

            # Time split calculations
            download_time = (t_download_end - t_download_start) if (t_download_start and t_download_end) else 0.0
            load_time = (t_load_end - t_load_start) if (t_load_start and t_load_end) else 0.0
            detect_time = (t_detect_end - t_detect_start) if (t_detect_start and t_detect_end) else 0.0
            per_photo_detect = detect_time / 20.0 if detect_time > 0 else 0.0

            # Read exported people.json
            people_json_path = temp_out / "people.json"
            assert people_json_path.exists(), "people.json missing from export"
            with open(people_json_path, "r", encoding="utf-8") as f:
                export_data = json.load(f)

            total_photos = len(export_data.get("photos", {}))
            people_clusters = export_data.get("people", [])
            people_count = len(people_clusters)
            unrecognized = export_data.get("unrecognized", {})
            unrec_faces = unrecognized.get("faces", [])
            unrec_photos = unrecognized.get("photo_ids", [])
            faces_in_clusters = sum(len(p.get("faces", [])) for p in people_clusters)
            total_detected_faces = faces_in_clusters + len(unrec_faces)

            print("\n" + "=" * 60)
            print("COLD CACHE & FIRST-RUN MODEL DOWNLOAD AUDIT RESULTS:")
            print("=" * 60)
            print(f"Time to /api/health:        {time_to_health:.2f} s")
            print(f"Model Download Time:        {download_time:.2f} s")
            print(f"Model Load Time:            {load_time:.2f} s")
            print(f"Total Detection Time:       {detect_time:.2f} s")
            print(f"Per-Photo Detect Time:      {per_photo_detect:.2f} s/photo")
            print("-" * 60)
            print(f"Total Photos Processed:     {total_photos}")
            print(f"Total Faces Detected:       {total_detected_faces}")
            print(f"  - Faces in Clusters:      {faces_in_clusters}")
            print(f"  - Unrecognized Faces:     {len(unrec_faces)}")
            print(f"People Clusters Count:      {people_count}")
            print(f"Unrecognized Photos Count:  {len(unrec_photos)}")
            print("=" * 60)

            # Assert final counts
            assert total_photos == 20, f"Expected 20 photos, got {total_photos}"
            assert total_detected_faces == 302, f"Expected 302 detected faces, got {total_detected_faces}"
            assert faces_in_clusters == 142, f"Expected 142 faces in clusters, got {faces_in_clusters}"
            assert len(unrec_faces) == 160, f"Expected 160 unrecognized faces, got {len(unrec_faces)}"
            assert people_count == 62, f"Expected 62 people clusters, got {people_count}"
            assert len(unrec_photos) == 17, f"Expected 17 unrecognized photos, got {len(unrec_photos)}"
            print("[PASS] All cold cache 20-photo counts match exact expected invariant targets!")

        finally:
            kill_proc(proc)
            log_file.close()

    finally:
        shutil.rmtree(temp_run_dir, ignore_errors=True)


if __name__ == "__main__":
    run_model_download_and_cold_cache_test()
