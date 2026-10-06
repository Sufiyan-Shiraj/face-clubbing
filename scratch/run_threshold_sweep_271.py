"""Runs a clustering threshold sweep at 0.45, 0.50, 0.55, 0.60, 0.65
on the 271-photo dataset, tracking cluster count, size distribution,
and same-photo-collision counts.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer

def main():
    cache = EmbeddingCache("export/.cache")
    photos = cache.load_all()
    print(f"Loaded {len(photos)} photos from cache.")

    thresholds = [0.45, 0.50, 0.55, 0.60, 0.65]
    results = []

    for t in thresholds:
        t0 = time.perf_counter()
        clusterer = FaceClusterer(distance_threshold=t)
        people, unrec = clusterer.cluster(photos)
        elapsed = time.perf_counter() - t0

        # Collision diagnostic
        colliding_clusters, total_extra = clusterer.count_same_photo_collisions(people)

        # Size buckets
        b_1 = sum(1 for p in people if len(p.photo_ids) == 1)
        b_2_3 = sum(1 for p in people if 2 <= len(p.photo_ids) <= 3)
        b_4_10 = sum(1 for p in people if 4 <= len(p.photo_ids) <= 10)
        b_11_plus = sum(1 for p in people if len(p.photo_ids) >= 11)

        largest = max(len(p.photo_ids) for p in people) if people else 0

        res = {
            "threshold": t,
            "clusters": len(people),
            "largest_cluster_photos": largest,
            "bucket_1": b_1,
            "bucket_2_3": b_2_3,
            "bucket_4_10": b_4_10,
            "bucket_11_plus": b_11_plus,
            "colliding_clusters": colliding_clusters,
            "collision_pct": round(colliding_clusters / len(people) * 100, 2) if people else 0,
            "total_extra_faces": total_extra,
            "clustering_time_ms": round(elapsed * 1000, 1),
        }
        results.append(res)
        print(f"Threshold {t:.2f}: {len(people)} clusters | Collisions: {colliding_clusters} ({res['collision_pct']}%) | Extra faces: {total_extra} | Time: {res['clustering_time_ms']}ms")

    with open("scratch/threshold_sweep_271_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
