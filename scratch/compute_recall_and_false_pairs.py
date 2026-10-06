import json
from pathlib import Path
from collections import defaultdict
import numpy as np

def load_ground_truth(gt_path="ground_truth.json"):
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sets = data.get("sets", {})
    different = data.get("different", [])
    return sets, different

def main():
    # 1. Load photo records & face embeddings
    cache_dir = Path("export/.cache")
    photos = {}
    face_map = {}
    for p_file in cache_dir.glob("*.json"):
        if p_file.name in ["config.json", "suggestions.json", "id_map.json"]:
            continue
        with open(p_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        photos[data["photo_id"]] = data
        for f in data.get("faces", []):
            face_map[f["face_id"]] = f

    # 2. Load flip-averaged embeddings
    with open("scratch/flip_embeddings.json", "r", encoding="utf-8") as f:
        flip_embs = json.load(f)

    # 3. Load ground truth
    gt_sets, gt_different = load_ground_truth("ground_truth.json")

    # Collect True Pairs from Ground Truth Sets
    true_pairs = []
    for set_name, fids in gt_sets.items():
        n = len(fids)
        for i in range(n):
            for j in range(i + 1, n):
                f1 = fids[i]
                f2 = fids[j]
                e1_std = np.array(face_map[f1]["embedding"], dtype=np.float32)
                e2_std = np.array(face_map[f2]["embedding"], dtype=np.float32)
                e1_flp = np.array(flip_embs[f1], dtype=np.float32)
                e2_flp = np.array(flip_embs[f2], dtype=np.float32)
                d_std = float(1.0 - np.dot(e1_std, e2_std))
                d_flp = float(1.0 - np.dot(e1_flp, e2_flp))
                true_pairs.append({
                    "set": set_name,
                    "face1": f1,
                    "face2": f2,
                    "d_std": d_std,
                    "d_flp": d_flp,
                })

    total_true_pairs = len(true_pairs)
    print(f"Total ground-truth true pairs: {total_true_pairs}")

    # 4. Collect Negative Pairs:
    # a. Same-photo seed negatives (excluding p041 collage)
    p041_fids = {"f_4a9b927f5789cd69_001", "f_4a9b927f5789cd69_005", "f_4a9b927f5789cd69_007"}
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

    neg_pair_dict = {}
    for pid, s_list in seeds_by_photo.items():
        n = len(s_list)
        for i in range(n):
            for j in range(i + 1, n):
                f1_id, e1_std, e1_flp = s_list[i]
                f2_id, e2_std, e2_flp = s_list[j]
                if f1_id in p041_fids and f2_id in p041_fids:
                    continue
                pair_key = tuple(sorted([f1_id, f2_id]))
                d_std = float(1.0 - np.dot(e1_std, e2_std))
                d_flp = float(1.0 - np.dot(e1_flp, e2_flp))
                neg_pair_dict[pair_key] = (d_std, d_flp)

    # b. Listed negatives from ground_truth.json["different"]
    for pair in gt_different:
        if len(pair) == 2:
            f1_id, f2_id = pair
            pair_key = tuple(sorted([f1_id, f2_id]))
            if pair_key not in neg_pair_dict:
                if f1_id in face_map and f2_id in face_map:
                    e1_std = np.array(face_map[f1_id]["embedding"], dtype=np.float32)
                    e2_std = np.array(face_map[f2_id]["embedding"], dtype=np.float32)
                    e1_flp = np.array(flip_embs[f1_id], dtype=np.float32)
                    e2_flp = np.array(flip_embs[f2_id], dtype=np.float32)
                    d_std = float(1.0 - np.dot(e1_std, e2_std))
                    d_flp = float(1.0 - np.dot(e1_flp, e2_flp))
                    neg_pair_dict[pair_key] = (d_std, d_flp)

    total_neg_pairs = len(neg_pair_dict)
    print(f"Total negative pairs (same-photo + listed): {total_neg_pairs}")

    # 5. Evaluate per threshold: True-pair recall & False-pair count
    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

    print("\n--- RECALL & FALSE PAIR PERFORMANCE TABLE ---")
    print(f"{'Threshold':<10} | {'True Recall (Std)':<20} | {'False Pairs (Std)':<20} | {'True Recall (Flip)':<20} | {'False Pairs (Flip)':<20}")
    print("-" * 100)

    report_table = []
    for t in thresholds:
        # Standard
        rec_std = sum(1 for p in true_pairs if p["d_std"] <= t)
        rec_std_pct = (rec_std / total_true_pairs) * 100.0
        fps_std = sum(1 for p in neg_pair_dict.values() if p[0] <= t)
        fps_std_pct = (fps_std / total_neg_pairs) * 100.0

        # Flip-averaged
        rec_flp = sum(1 for p in true_pairs if p["d_flp"] <= t)
        rec_flp_pct = (rec_flp / total_true_pairs) * 100.0
        fps_flp = sum(1 for p in neg_pair_dict.values() if p[1] <= t)
        fps_flp_pct = (fps_flp / total_neg_pairs) * 100.0

        print(f"<= {t:.2f}     | {rec_std:>2}/{total_true_pairs} ({rec_std_pct:>5.1f}%)        | {fps_std:>4}/{total_neg_pairs} ({fps_std_pct:>5.2f}%)   | {rec_flp:>2}/{total_true_pairs} ({rec_flp_pct:>5.1f}%)        | {fps_flp:>4}/{total_neg_pairs} ({fps_flp_pct:>5.2f}%)")
        report_table.append({
            "threshold": t,
            "true_recall_std_count": rec_std,
            "true_recall_std_pct": round(rec_std_pct, 2),
            "false_pairs_std_count": fps_std,
            "false_pairs_std_pct": round(fps_std_pct, 4),
            "true_recall_flip_count": rec_flp,
            "true_recall_flip_pct": round(rec_flp_pct, 2),
            "false_pairs_flip_count": fps_flp,
            "false_pairs_flip_pct": round(fps_flp_pct, 4),
        })

    out_data = {
        "total_true_pairs": total_true_pairs,
        "total_neg_pairs": total_neg_pairs,
        "table": report_table,
    }
    with open("scratch/recall_false_pairs_report.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print("Saved scratch/recall_false_pairs_report.json")

if __name__ == "__main__":
    main()
