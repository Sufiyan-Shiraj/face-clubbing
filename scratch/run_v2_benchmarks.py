import sys
import time
import json
import shutil
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psutil
import numpy as np
import cv2
from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer

process = psutil.Process()

print("=" * 60)
print("STARTING V2 COLD PIPELINE EXECUTION")
print("=" * 60)

t0_cold = time.time()
mem_peak = process.memory_info().rss

def track_mem(status):
    global mem_peak
    rss = process.memory_info().rss
    if rss > mem_peak:
        mem_peak = rss
    msg = status.get("message", "")
    stage = status.get("stage", "")
    if stage in ["scanned", "model_init", "clustered", "complete"]:
        print(f"[{stage.upper()}] {msg}")
    elif stage == "processing" and status.get("current", 0) % 10 == 0:
        print(f"Progress: {status.get('current')}/{status.get('total')} photos - {msg}")

config_cold = EngineConfig(
    input_path="test_photos",
    output_dir="export",
    cache_dir="export/.cache",
    distance_threshold=0.5,
    min_det_score=0.5,
    min_face_size=64, # in original pixels
    max_image_dim=1600,
    progress_callback=track_mem,
)

res_cold = run_pipeline(config_cold)
cold_duration = time.time() - t0_cold
peak_mb = mem_peak / (1024 * 1024)

print("\n" + "=" * 60)
print(f"COLD RUN COMPLETED IN {cold_duration:.2f} seconds ({cold_duration / 59:.2f}s / photo)")
print(f"PEAK RAM: {peak_mb:.2f} MB")
print("=" * 60)

# 2. Warm Re-Run Benchmark
print("\n" + "=" * 60)
print("TESTING WARM RE-RUN (Target: under 5 seconds)")
print("=" * 60)

t0_warm = time.time()
config_warm = EngineConfig(
    input_path="test_photos",
    output_dir="export",
    cache_dir="export/.cache",
    distance_threshold=0.5,
    min_det_score=0.5,
    min_face_size=64,
    max_image_dim=1600,
)
res_warm = run_pipeline(config_warm)
warm_duration = time.time() - t0_warm

print(f"WARM RE-RUN COMPLETED IN {warm_duration:.2f} seconds!")
print("=" * 60)

# 3. Diagnostic & Sweep across thresholds
cache = EmbeddingCache("export/.cache")
cached_photos = cache.load_all()

sweep_thresholds = [0.35, 0.45, 0.50, 0.55, 0.60, 0.65]
sweep_results = []

for th in sweep_thresholds:
    cl = FaceClusterer(distance_threshold=th)
    people_th, unrec_th = cl.cluster(cached_photos)
    counts = [len(p.photo_ids) for p in people_th]
    single_c = sum(1 for c in counts if c == 1)
    max_c = max(counts) if counts else 0
    colliding_clusters, total_extra = FaceClusterer.count_same_photo_collisions(people_th)

    sweep_results.append({
        "threshold": th,
        "total_clusters": len(people_th),
        "single_photo_clusters": single_c,
        "max_cluster_size": max_c,
        "same_photo_collision_clusters": colliding_clusters,
        "same_photo_extra_faces": total_extra,
    })

# 4. Near-Duplicate Analysis using pHash (DCT) and dHash
def compute_phash(p: Path) -> np.ndarray:
    img = ImageOps.exif_transpose(Image.open(p)).convert('L').resize((32, 32), Image.Resampling.LANCZOS)
    arr = np.float32(img)
    dct = cv2.dct(arr)
    dct_low = dct[:8, :8]
    med = np.median(dct_low[1:, 1:])
    return dct_low > med

def compute_dhash(p: Path) -> np.ndarray:
    img = ImageOps.exif_transpose(Image.open(p)).convert('L').resize((9, 8), Image.Resampling.LANCZOS)
    arr = np.array(img)
    return arr[:, 1:] > arr[:, :-1]

photo_paths = sorted(list(Path("test_photos").iterdir()))
phashes = {p.name: compute_phash(p) for p in photo_paths}
dhashes = {p.name: compute_dhash(p) for p in photo_paths}

duplicate_pairs = []
for i in range(len(photo_paths)):
    for j in range(i + 1, len(photo_paths)):
        name1, name2 = photo_paths[i].name, photo_paths[j].name
        p_dist = int(np.sum(phashes[name1] != phashes[name2]))
        d_dist = int(np.sum(dhashes[name1] != dhashes[name2]))
        duplicate_pairs.append({
            "photo1": name1,
            "photo2": name2,
            "phash_distance": p_dist,
            "dhash_distance": d_dist,
        })

duplicate_pairs.sort(key=lambda x: x["phash_distance"])

# 5. Compile Final Metrics
total_detected = sum(len(p.faces) for p in cached_photos.values())
quality_faces = sum(sum(1 for f in p.faces if f.is_good_quality) for p in cached_photos.values())
unrec_faces = sum(sum(1 for f in p.faces if not f.is_good_quality) for p in cached_photos.values())
counts_default = [len(p.photo_ids) for p in res_cold.people]

top_10 = []
for idx, p in enumerate(res_cold.people[:10]):
    top_10.append({
        "rank": idx + 1,
        "id": p.id,
        "photo_count": len(p.photo_ids),
        "face_count": len(p.faces),
        "photo_ids": p.photo_ids,
        "rep_face_id": p.rep_face.face_id if p.rep_face else None,
        "rep_photo_id": p.rep_face.photo_id if p.rep_face else None,
    })

metrics_data = {
    "cold_duration_seconds": round(cold_duration, 2),
    "cold_avg_per_photo": round(cold_duration / 59, 2),
    "warm_duration_seconds": round(warm_duration, 2),
    "peak_ram_mb": round(peak_mb, 2),
    "total_detected_faces": total_detected,
    "quality_faces": quality_faces,
    "unrecognized_faces": unrec_faces,
    "total_clusters": len(res_cold.people),
    "single_photo_clusters": sum(1 for c in counts_default if c == 1),
    "clusters_2_3": sum(1 for c in counts_default if 2 <= c <= 3),
    "clusters_4_10": sum(1 for c in counts_default if 4 <= c <= 10),
    "clusters_11_plus": sum(1 for c in counts_default if c >= 11),
    "unrecognized_photos_count": len(res_cold.unrecognized.photo_ids),
    "sweep_results": sweep_results,
    "top_10": top_10,
    "top_10_closest_photo_pairs": duplicate_pairs[:10],
}

Path("scratch").mkdir(exist_ok=True)
with open("scratch/v2_metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics_data, f, indent=2)

print("\nSaved scratch/v2_metrics.json successfully!")
