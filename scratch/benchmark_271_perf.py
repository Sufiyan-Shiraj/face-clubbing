"""Benchmark script to measure warm re-run performance and peak RAM on all 271 photos,
and compute detailed counts for the 271-photo test set.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import threading
import psutil
import os
import json
from collections import Counter

from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer

def main():
    pid = os.getpid()
    proc = psutil.Process(pid)
    peak_ram_bytes = 0
    stop_monitor = False

    def monitor_ram():
        nonlocal peak_ram_bytes, stop_monitor
        while not stop_monitor:
            try:
                mem = proc.memory_info().rss
                if mem > peak_ram_bytes:
                    peak_ram_bytes = mem
            except Exception:
                pass
            time.sleep(0.05)

    monitor_thread = threading.Thread(target=monitor_ram, daemon=True)
    monitor_thread.start()

    print("Running warm re-run pipeline on test_photos (271 files)...")
    config = EngineConfig(
        input_path="test_photos",
        output_dir="export",
        cache_dir="export/.cache",
        distance_threshold=0.50,
        min_det_score=0.50,
        min_face_size=64,
        max_yaw=70.0,
    )

    t0 = time.perf_counter()
    result = run_pipeline(config)
    warm_elapsed = time.perf_counter() - t0

    stop_monitor = True
    monitor_thread.join(timeout=0.5)

    peak_ram_mb = peak_ram_bytes / (1024 * 1024)
    print(f"\nWarm re-run finished in: {warm_elapsed:.2f}s")
    print(f"Peak RAM during warm run: {peak_ram_mb:.1f} MB")

    # Counts and statistics
    photos = result.photos
    total_scanned_files = 271
    unique_photos = len(photos)
    
    total_faces = sum(len(p.faces) for p in photos.values())
    quality_faces = sum(sum(1 for f in p.faces if f.is_good_quality) for p in photos.values())
    unrec_faces = sum(sum(1 for f in p.faces if not f.is_good_quality) for p in photos.values())
    
    # Reasons breakdown for unrec faces
    reasons = Counter()
    for p in photos.values():
        for f in p.faces:
            if not f.is_good_quality:
                reasons[f.rejection_reason or "unknown"] += 1

    photos_with_no_faces = [pid for pid, p in photos.items() if len(p.faces) == 0]
    photos_with_faces = [pid for pid, p in photos.items() if len(p.faces) > 0]

    people = result.people
    total_clusters = len(people)

    # Cluster-size buckets: 1 photo, 2-3 photos, 4-10 photos, 11+ photos
    bucket_1 = 0
    bucket_2_3 = 0
    bucket_4_10 = 0
    bucket_11_plus = 0

    for p in people:
        num_photos = len(p.photo_ids)
        if num_photos == 1:
            bucket_1 += 1
        elif 2 <= num_photos <= 3:
            bucket_2_3 += 1
        elif 4 <= num_photos <= 10:
            bucket_4_10 += 1
        else:
            bucket_11_plus += 1

    stats = {
        "total_scanned_files": total_scanned_files,
        "unique_photos": unique_photos,
        "total_faces_detected": total_faces,
        "quality_faces": quality_faces,
        "unrecognized_faces": unrec_faces,
        "rejection_reasons": dict(reasons),
        "photos_with_no_face": len(photos_with_no_faces),
        "photos_with_at_least_one_face": len(photos_with_faces),
        "total_clusters": total_clusters,
        "bucket_1": bucket_1,
        "bucket_2_3": bucket_2_3,
        "bucket_4_10": bucket_4_10,
        "bucket_11_plus": bucket_11_plus,
        "cold_run_time_s": 821.5,
        "warm_run_time_s": round(warm_elapsed, 2),
        "peak_ram_mb": round(peak_ram_mb, 1),
    }

    print("\n--- 271-Photo Dataset Statistics ---")
    print(json.dumps(stats, indent=2))

    with open("scratch/stats_271.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    main()
