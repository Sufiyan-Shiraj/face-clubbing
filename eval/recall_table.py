import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import numpy as np

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.engine.cache import EmbeddingCache
from eval.loader import load_ground_truth
from eval.negatives import generate_same_photo_negatives

def compute_recall_and_false_pairs(work_dir: str = "export.work", gt_path: str = None):
    # 1. Load cache
    cache = EmbeddingCache(work_dir)
    photos = cache.load_all()

    # Build face embedding lookup
    face_map = {}
    for pid, pdata in photos.items():
        for f in pdata.faces:
            face_map[f.face_id] = f

    # 2. Load ground truth
    gt = load_ground_truth(gt_path)

    # 3. Generate negatives
    same_photo_negs, excluded_collages = generate_same_photo_negatives(photos, same_photo_merge_max=0.40)
    print(f"Same-photo negative generator: found {len(same_photo_negs)} valid negative pairs.")
    print(f"Excluded {len(excluded_collages)} same-photo pair(s) with distance <= 0.40 (collage candidates).")

    # Combine with listed negatives from ground truth
    all_negs_dict = {}
    for item in same_photo_negs:
        pair_key = (item["face1_id"], item["face2_id"])
        all_negs_dict[pair_key] = (item["distance_std"], item["distance_flip"])

    for f1, f2 in gt.get_different_pairs():
        pair_key = (min(f1, f2), max(f1, f2))
        if pair_key not in all_negs_dict:
            f1_obj = face_map.get(f1)
            f2_obj = face_map.get(f2)
            if f1_obj and f2_obj and f1_obj.embedding is not None and f2_obj.embedding is not None:
                d_std = float(1.0 - np.dot(f1_obj.embedding, f2_obj.embedding))
                d_flp = None
                if f1_obj.embedding_flipped is not None and f2_obj.embedding_flipped is not None:
                    d_flp = float(1.0 - np.dot(f1_obj.embedding_flipped, f2_obj.embedding_flipped))
                all_negs_dict[pair_key] = (d_std, d_flp)

    total_neg_pairs = len(all_negs_dict)

    # 4. Collect all true pairs
    raw_true_pairs = gt.get_true_pairs(exclude_unconfirmed=False)
    
    true_pairs_data = []
    near_duplicates_count = 0
    unconfirmed_pairs_count = 0

    for s_name, f1, f2 in raw_true_pairs:
        f1_obj = face_map.get(f1)
        f2_obj = face_map.get(f2)
        if not (f1_obj and f2_obj and f1_obj.embedding is not None and f2_obj.embedding is not None):
            continue

        d_std = float(1.0 - np.dot(f1_obj.embedding, f2_obj.embedding))
        d_flp = None
        if f1_obj.embedding_flipped is not None and f2_obj.embedding_flipped is not None:
            d_flp = float(1.0 - np.dot(f1_obj.embedding_flipped, f2_obj.embedding_flipped))

        is_unconfirmed = (f1 in gt.unconfirmed or f2 in gt.unconfirmed)
        is_near_dup = (d_std < 0.20)

        if is_unconfirmed:
            unconfirmed_pairs_count += 1
        if is_near_dup:
            near_duplicates_count += 1

        true_pairs_data.append({
            "set": s_name,
            "face1": f1,
            "face2": f2,
            "d_std": d_std,
            "d_flp": d_flp,
            "is_unconfirmed": is_unconfirmed,
            "is_near_dup": is_near_dup
        })

    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

    def build_table(pairs_subset, title, total_pairs_count, total_sets_count):
        print("\n" + "=" * 90)
        print(f"{title}")
        print(f"Total Positive Pairs: {total_pairs_count} | Labelled Sets: {total_sets_count} | Total Negative Pairs: {total_neg_pairs}")
        print("=" * 90)
        header = f"{'Threshold':<10} | {'True Recall (Std)':<20} | {'False Pairs (Std)':<20} | {'True Recall (Flip)':<20} | {'False Pairs (Flip)':<20}"
        print(header)
        print("-" * 90)
        rows = []
        for t in thresholds:
            r_std = sum(1 for p in pairs_subset if p["d_std"] <= t)
            r_std_pct = (r_std / total_pairs_count * 100.0) if total_pairs_count > 0 else 0.0
            f_std = sum(1 for d_s, _ in all_negs_dict.values() if d_s is not None and d_s <= t)
            f_std_pct = (f_std / total_neg_pairs * 100.0) if total_neg_pairs > 0 else 0.0

            r_flp = sum(1 for p in pairs_subset if p["d_flp"] is not None and p["d_flp"] <= t)
            r_flp_pct = (r_flp / total_pairs_count * 100.0) if total_pairs_count > 0 else 0.0
            f_flp = sum(1 for _, d_f in all_negs_dict.values() if d_f is not None and d_f <= t)
            f_flp_pct = (f_flp / total_neg_pairs * 100.0) if total_neg_pairs > 0 else 0.0

            row_str = f"<= {t:.2f}     | {r_std:>2}/{total_pairs_count} ({r_std_pct:>5.1f}%)        | {f_std:>4}/{total_neg_pairs} ({f_std_pct:>5.2f}%)   | {r_flp:>2}/{total_pairs_count} ({r_flp_pct:>5.1f}%)        | {f_flp:>4}/{total_neg_pairs} ({f_flp_pct:>5.2f}%)"
            print(row_str)
            rows.append({
                "threshold": t,
                "true_recall_std_count": r_std,
                "true_recall_std_pct": round(r_std_pct, 2),
                "false_pairs_std_count": f_std,
                "false_pairs_std_pct": round(f_std_pct, 4),
                "true_recall_flip_count": r_flp,
                "true_recall_flip_pct": round(r_flp_pct, 2),
                "false_pairs_flip_count": f_flp,
                "false_pairs_flip_pct": round(f_flp_pct, 4),
            })
        return rows

    # (A) All labelled pairs
    sets_a_count = len(set(p["set"] for p in true_pairs_data))
    table_a = build_table(
        true_pairs_data,
        "TABLE (A): ALL LABELLED PAIRS",
        total_pairs_count=len(true_pairs_data),
        total_sets_count=sets_a_count
    )

    # (B) Clean set: excluding unconfirmed face pairs AND near-duplicates (< 0.20)
    clean_pairs = [p for p in true_pairs_data if not p["is_unconfirmed"] and not p["is_near_dup"]]
    sets_b_count = len(set(p["set"] for p in clean_pairs))
    print(f"\n[Filter Note for Table B]: Excluded {unconfirmed_pairs_count} unconfirmed pair(s) and {near_duplicates_count} near-duplicate pair(s) (< 0.20).")
    table_b = build_table(
        clean_pairs,
        "TABLE (B): CLEAN SET (EXCLUDING UNCONFIRMED & NEAR-DUPLICATES < 0.20)",
        total_pairs_count=len(clean_pairs),
        total_sets_count=sets_b_count
    )

    result = {
        "total_true_pairs_a": len(true_pairs_data),
        "total_sets_a": sets_a_count,
        "total_true_pairs_b": len(clean_pairs),
        "total_sets_b": sets_b_count,
        "unconfirmed_pairs_excluded": unconfirmed_pairs_count,
        "near_duplicates_excluded": near_duplicates_count,
        "total_neg_pairs": total_neg_pairs,
        "excluded_collages_count": len(excluded_collages),
        "table_a": table_a,
        "table_b": table_b
    }

    out_file = Path(__file__).parent / "recall_false_pairs_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved evaluation metrics to {out_file}")
    return result

if __name__ == "__main__":
    compute_recall_and_false_pairs()
