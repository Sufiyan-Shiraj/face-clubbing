import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import copy
import numpy as np

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer

def main():
    # 1. Load base records from cache
    cache = EmbeddingCache("export/.cache")
    photos_base = cache.load_all()

    # 2. Load precomputed flip-averaged embeddings
    with open("scratch/flip_embeddings.json", "r", encoding="utf-8") as f:
        flip_embs = json.load(f)

    # 3. Create deepcopy of photos and replace embeddings with flip-averaged ones
    photos_flip = copy.deepcopy(photos_base)
    for pid, precord in photos_flip.items():
        for f in precord.faces:
            if f.face_id in flip_embs:
                f.embedding = np.array(flip_embs[f.face_id], dtype=np.float32)

    # 4. Run clustering with FaceClusterer
    cl = FaceClusterer(
        distance_threshold=0.50,
        seed_min_face_size=64,
        seed_max_yaw=60.0,
        seed_min_det_score=0.70,
        second_pass_merge=True,
        same_photo_merge_max=0.40,
    )
    people_flip, unrec_flip = cl.cluster(photos_flip)

    total_clusters = len(people_flip)
    singletons = sum(1 for p in people_flip if len(p.photo_ids) == 1)
    unrec_faces = len(unrec_flip.faces)
    unrec_photos = len(unrec_flip.photo_ids)

    # Check collisions
    colliding = 0
    extra_faces = 0
    collision_details = []
    for p in people_flip:
        pids = [f.photo_id for f in p.faces]
        if len(pids) > len(set(pids)):
            colliding += 1
            extra = len(pids) - len(set(pids))
            extra_faces += extra
            collision_details.append((p.id, extra, len(set(pids)), len(pids)))

    # 5. Check Ground-Truth Pairs under Flip-Averaging
    with open("ground_truth.json", "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    gt_sets = gt_data.get("sets", {})

    gt_pairs = []
    for s_name, fids in gt_sets.items():
        n = len(fids)
        for i in range(n):
            for j in range(i + 1, n):
                f1 = fids[i]
                f2 = fids[j]
                e1 = np.array(flip_embs[f1], dtype=np.float32)
                e2 = np.array(flip_embs[f2], dtype=np.float32)
                d = float(1.0 - np.dot(e1, e2))
                gt_pairs.append((s_name, f1, f2, d))

    gt_le_50 = sum(1 for p in gt_pairs if p[3] <= 0.50)
    gt_le_60 = sum(1 for p in gt_pairs if p[3] <= 0.60)
    total_gt = len(gt_pairs)

    print("=== FLIP-AVERAGING FULL SET EXPERIMENT RESULTS ===")
    print(f"Total Person Clusters: {total_clusters}")
    print(f"Singletons: {singletons}")
    print(f"Unrecognized Faces: {unrec_faces}")
    print(f"Unrecognized Photos: {unrec_photos}")
    print(f"Collision Clusters: {colliding} (Extra Faces: {extra_faces})")
    print(f"Collision Details: {collision_details}")
    print(f"Ground-Truth Pairs <= 0.50: {gt_le_50} / {total_gt} ({gt_le_50/total_gt*100:.1f}%)")
    print(f"Ground-Truth Pairs <= 0.60: {gt_le_60} / {total_gt} ({gt_le_60/total_gt*100:.1f}%)")

    results = {
        "experiment": "flip_average_full_set",
        "clusters": total_clusters,
        "singletons": singletons,
        "unrecognized_faces": unrec_faces,
        "unrecognized_photos": unrec_photos,
        "colliding_clusters": colliding,
        "extra_faces": extra_faces,
        "collision_details": collision_details,
        "ground_truth_total_pairs": total_gt,
        "ground_truth_le_0_50": gt_le_50,
        "ground_truth_le_0_60": gt_le_60,
    }
    with open("scratch/flip_average_full_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved scratch/flip_average_full_experiment_results.json")

if __name__ == "__main__":
    main()
