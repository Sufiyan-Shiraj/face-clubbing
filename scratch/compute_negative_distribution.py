import json
from pathlib import Path
from collections import defaultdict
import numpy as np

def main():
    # 1. Load photo records from cache
    cache_dir = Path("export/.cache")
    photos = {}
    for p_file in cache_dir.glob("*.json"):
        if p_file.name in ["config.json", "suggestions.json", "id_map.json"]:
            continue
        with open(p_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        photos[data["photo_id"]] = data

    # 2. Load flip-averaged embeddings
    with open("scratch/flip_embeddings.json", "r", encoding="utf-8") as f:
        flip_embs = json.load(f)

    # 3. Find all seed faces per photo
    # Seed definition: face_dim >= 64, yaw <= 60.0, det_score >= 0.70
    seeds_by_photo = defaultdict(list)
    for pid, pdata in photos.items():
        for face in pdata.get("faces", []):
            bbox = face["bbox"]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            dim = min(w, h)
            pose = face.get("pose", [0, 0, 0])
            yaw = abs(pose[1]) if pose and len(pose) >= 2 else 0.0
            score = face.get("det_score", 0.0)

            if dim >= 64 and yaw <= 60.0 and score >= 0.70:
                fid = face["face_id"]
                std_emb = np.array(face["embedding"], dtype=np.float32)
                flp_emb = np.array(flip_embs[fid], dtype=np.float32)
                seeds_by_photo[pid].append((fid, std_emb, flp_emb))

    print(f"Total photos with seeds: {len(seeds_by_photo)}")
    total_seeds = sum(len(s) for s in seeds_by_photo.values())
    print(f"Total seed faces: {total_seeds}")

    # Collage faces in p041 (photo 4a9b927f5789cd69)
    p041_fids = {"f_4a9b927f5789cd69_001", "f_4a9b927f5789cd69_005", "f_4a9b927f5789cd69_007"}

    # Compute all negative pairs from the same photo, excluding the p041 collage pairs
    neg_pairs = []
    for pid, s_list in seeds_by_photo.items():
        n = len(s_list)
        for i in range(n):
            for j in range(i + 1, n):
                f1_id, e1_std, e1_flp = s_list[i]
                f2_id, e2_std, e2_flp = s_list[j]
                # Exclude pairs within p041 collage
                if f1_id in p041_fids and f2_id in p041_fids:
                    continue
                d_std = float(1.0 - np.dot(e1_std, e2_std))
                d_flp = float(1.0 - np.dot(e1_flp, e2_flp))
                neg_pairs.append({
                    "photo_id": pid,
                    "face1": f1_id,
                    "face2": f2_id,
                    "d_std": d_std,
                    "d_flp": d_flp,
                })

    total_pairs = len(neg_pairs)
    print(f"\nTotal negative seed pairs (excluding p041 collage): {total_pairs}")

    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

    print("\n--- NEGATIVE DISTRIBUTION TABLE ---")
    print(f"{'Threshold':<12} | {'Standard Embeddings':<22} | {'Flip-Averaged Embeddings':<25}")
    print("-" * 65)
    
    summary = {
        "total_pairs": total_pairs,
        "thresholds": {},
    }

    for t in thresholds:
        cnt_std = sum(1 for p in neg_pairs if p["d_std"] <= t)
        cnt_flp = sum(1 for p in neg_pairs if p["d_flp"] <= t)
        pct_std = (cnt_std / total_pairs) * 100.0
        pct_flp = (cnt_flp / total_pairs) * 100.0
        print(f"<= {t:.2f}       | {cnt_std:>6} ({pct_std:>5.2f}%)         | {cnt_flp:>6} ({pct_flp:>5.2f}%)")
        summary["thresholds"][str(t)] = {
            "standard_count": cnt_std,
            "standard_pct": round(pct_std, 4),
            "flip_count": cnt_flp,
            "flip_pct": round(pct_flp, 4),
        }

    min_std = min(p["d_std"] for p in neg_pairs)
    min_flp = min(p["d_flp"] for p in neg_pairs)
    print(f"\nMinimum negative distance: Standard = {min_std:.4f}, Flip-Averaged = {min_flp:.4f}")
    summary["min_distance"] = {
        "standard": round(min_std, 4),
        "flip_averaged": round(min_flp, 4),
    }

    with open("scratch/negative_distribution.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Saved scratch/negative_distribution.json")

if __name__ == "__main__":
    main()
