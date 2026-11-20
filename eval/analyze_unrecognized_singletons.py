#!/usr/bin/env python3
"""Analysis of Unrecognized faces and Singletons on the pinned 259-photo baseline.

This script performs analysis ONLY:
- Loads the canonical Phase 1b baseline dataset (eval/baseline/people.json, 259 photos, 1,701 faces).
- Computes top-5 normalized centroids for all 192 people clusters.
- For all 445 Unrecognized faces and all 81 Singletons:
    * Computes yaw, pitch, roll (from 3D landmarks / pose)
    * Computes bounding box size (min(w, h))
    * Computes detection score
    * Computes cosine distance to nearest and second-nearest person centroids
- Generates 2D distribution tables by yaw bucket (0-15°, 15-30°, 30-45°, 45°+) and size bucket (<64, 64-128, 128+).
- Evaluates the [0.45, 0.65] recoverable band and high-yaw prevalence.
- Saves raw output JSON (Counts/IDs only, no images or crops) and computes SHA-256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def compute_cluster_centroid(faces: List[Dict[str, Any]], top_k: int = 5) -> Optional[np.ndarray]:
    """Computes a normalized centroid embedding from top-k faces (ranked by det_score desc, size desc)."""
    scored = []
    for f in faces:
        emb = f.get("embedding")
        if emb is None:
            continue
        bbox = f["bbox"]
        w = float(bbox[2] - bbox[0])
        h = float(bbox[3] - bbox[1])
        dim = min(w, h)
        scored.append((float(f["det_score"]), dim, np.array(emb, dtype=np.float32)))

    # Sort descending by det_score, then face dimension
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top_faces = scored[:top_k]
    if not top_faces:
        return None

    embs = np.stack([x[2] for x in top_faces])
    mean_v = np.mean(embs, axis=0)
    norm = float(np.linalg.norm(mean_v))
    if norm > 1e-8:
        mean_v = mean_v / norm
    return mean_v


def build_analysis(
    baseline_dir: Path | str = "eval/baseline",
    cache_dir: Path | str = "export.work",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    bdir = Path(baseline_dir)
    cdir = Path(cache_dir)

    people_json_path = bdir / "people.json"
    if not people_json_path.exists():
        raise FileNotFoundError(f"Missing baseline file: {people_json_path}")

    with open(people_json_path, "r", encoding="utf-8") as f:
        pdata = json.load(f)

    # Load cache for all photos in baseline
    photo_cache: Dict[str, Dict[str, Any]] = {}
    photos_dict = pdata.get("photos", {})
    for pid in photos_dict:
        cfile = cdir / f"{pid}.json"
        if not cfile.exists():
            raise FileNotFoundError(f"Missing cache file for photo {pid}: {cfile}")
        with open(cfile, "r", encoding="utf-8") as cf:
            cdata = json.load(cf)
            photo_cache[pid] = {face["face_id"]: face for face in cdata.get("faces", [])}

    people = pdata.get("people", [])
    unrec_faces_raw = pdata.get("unrecognized", {}).get("faces", [])

    # 1. Compute centroids for all 192 people
    centroids: Dict[str, np.ndarray] = {}
    for person in people:
        pid = person["id"]
        p_faces = []
        for f in person.get("faces", []):
            cf = photo_cache[f["photo_id"]][f["face_id"]]
            p_faces.append(cf)
        c = compute_cluster_centroid(p_faces, top_k=5)
        if c is None:
            raise ValueError(f"Failed to compute centroid for cluster {pid}")
        centroids[pid] = c

    centroid_ids = [p["id"] for p in people]
    centroid_matrix = np.stack([centroids[cid] for cid in centroid_ids])  # (192, 512)

    # 2. Analyze Unrecognized Faces (445)
    unrec_records: List[Dict[str, Any]] = []
    for f in unrec_faces_raw:
        fid = f["face_id"]
        pid = f["photo_id"]
        cf = photo_cache[pid][fid]
        emb = np.array(cf["embedding"], dtype=np.float32)

        dists = 1.0 - np.dot(centroid_matrix, emb)
        idx_sorted = np.argsort(dists)

        d1 = float(dists[idx_sorted[0]])
        c1 = centroid_ids[idx_sorted[0]]
        d2 = float(dists[idx_sorted[1]])
        c2 = centroid_ids[idx_sorted[1]]

        pose = cf.get("pose", [0.0, 0.0, 0.0])
        pitch = float(pose[0]) if pose and len(pose) >= 1 else 0.0
        yaw_signed = float(pose[1]) if pose and len(pose) >= 2 else 0.0
        yaw = abs(yaw_signed)
        roll = float(pose[2]) if pose and len(pose) >= 3 else 0.0

        bbox = [float(x) for x in cf["bbox"]]
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        dim = min(bw, bh)
        score = float(cf["det_score"])

        unrec_records.append({
            "face_id": fid,
            "photo_id": pid,
            "category": "unrecognized",
            "cluster_id": None,
            "rejection_reason": f.get("rejection_reason"),
            "yaw_deg": round(yaw, 4),
            "yaw_signed_deg": round(yaw_signed, 4),
            "pitch_deg": round(pitch, 4),
            "roll_deg": round(roll, 4),
            "bbox": [round(coord, 2) for coord in bbox],
            "bbox_width": round(bw, 2),
            "bbox_height": round(bh, 2),
            "bbox_size": round(dim, 2),
            "det_score": round(score, 4),
            "nearest_centroid_id": c1,
            "nearest_centroid_distance": round(d1, 4),
            "second_nearest_centroid_id": c2,
            "second_nearest_centroid_distance": round(d2, 4),
            "distance_margin": round(d2 - d1, 4),
            "in_recoverable_band_045_065": bool(0.45 <= d1 <= 0.65),
            "is_high_yaw_45": bool(yaw >= 45.0),
            "is_seed_profile_yaw_60": bool(yaw > 60.0),
            "is_extreme_pose_yaw_70": bool(yaw > 70.0),
        })

    # 3. Analyze Singletons (81)
    singletons = [p for p in people if len(p.get("photos", p.get("photo_ids", []))) == 1]
    singleton_records: List[Dict[str, Any]] = []

    for p in singletons:
        f = p["faces"][0]
        fid = f["face_id"]
        pid = f["photo_id"]
        cf = photo_cache[pid][fid]
        emb = np.array(cf["embedding"], dtype=np.float32)

        dists = 1.0 - np.dot(centroid_matrix, emb)
        self_idx = centroid_ids.index(p["id"])

        # Nearest other cluster
        dists_other = dists.copy()
        dists_other[self_idx] = 999.0
        idx_other_sorted = np.argsort(dists_other)

        d1_other = float(dists_other[idx_other_sorted[0]])
        c1_other = centroid_ids[idx_other_sorted[0]]
        d2_other = float(dists_other[idx_other_sorted[1]])
        c2_other = centroid_ids[idx_other_sorted[1]]

        pose = cf.get("pose", [0.0, 0.0, 0.0])
        pitch = float(pose[0]) if pose and len(pose) >= 1 else 0.0
        yaw_signed = float(pose[1]) if pose and len(pose) >= 2 else 0.0
        yaw = abs(yaw_signed)
        roll = float(pose[2]) if pose and len(pose) >= 3 else 0.0

        bbox = [float(x) for x in cf["bbox"]]
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        dim = min(bw, bh)
        score = float(cf["det_score"])

        singleton_records.append({
            "face_id": fid,
            "photo_id": pid,
            "category": "singleton",
            "cluster_id": p["id"],
            "rejection_reason": None,
            "yaw_deg": round(yaw, 4),
            "yaw_signed_deg": round(yaw_signed, 4),
            "pitch_deg": round(pitch, 4),
            "roll_deg": round(roll, 4),
            "bbox": [round(coord, 2) for coord in bbox],
            "bbox_width": round(bw, 2),
            "bbox_height": round(bh, 2),
            "bbox_size": round(dim, 2),
            "det_score": round(score, 4),
            "nearest_centroid_id": p["id"],
            "nearest_centroid_distance": 0.0,
            "second_nearest_centroid_id": c1_other,
            "second_nearest_centroid_distance": round(d1_other, 4),
            "nearest_other_centroid_id": c1_other,
            "nearest_other_centroid_distance": round(d1_other, 4),
            "second_nearest_other_centroid_id": c2_other,
            "second_nearest_other_centroid_distance": round(d2_other, 4),
            "other_distance_margin": round(d2_other - d1_other, 4),
            "in_recoverable_band_045_065": bool(0.45 <= d1_other <= 0.65),
            "is_high_yaw_45": bool(yaw >= 45.0),
            "is_seed_profile_yaw_60": bool(yaw > 60.0),
            "is_extreme_pose_yaw_70": bool(yaw > 70.0),
        })

    # Helper function to generate 2D bucket stats
    yaw_buckets = [
        ("0-15", 0.0, 15.0),
        ("15-30", 15.0, 30.0),
        ("30-45", 30.0, 45.0),
        ("45+", 45.0, float("inf")),
    ]
    size_buckets = [
        ("<64", 0.0, 64.0),
        ("64-128", 64.0, 128.0),
        ("128+", 128.0, float("inf")),
    ]

    def compute_table(records_list: List[Dict[str, Any]], distance_key: str) -> Dict[str, Any]:
        grid: Dict[str, Dict[str, Dict[str, Any]]] = {}
        row_totals: Dict[str, int] = {}
        col_totals: Dict[str, int] = {s_name: 0 for s_name, _, _ in size_buckets}

        for y_name, y_min, y_max in yaw_buckets:
            grid[y_name] = {}
            y_matching = [r for r in records_list if y_min <= r["yaw_deg"] < y_max]
            row_totals[y_name] = len(y_matching)

            for s_name, s_min, s_max in size_buckets:
                cell_faces = [r for r in y_matching if s_min <= r["bbox_size"] < s_max]
                col_totals[s_name] += len(cell_faces)
                if cell_faces:
                    dists = [r[distance_key] for r in cell_faces]
                    grid[y_name][s_name] = {
                        "count": len(cell_faces),
                        "median_distance": round(float(np.median(dists)), 4),
                        "mean_distance": round(float(np.mean(dists)), 4),
                        "min_distance": round(float(np.min(dists)), 4),
                        "max_distance": round(float(np.max(dists)), 4),
                    }
                else:
                    grid[y_name][s_name] = {
                        "count": 0,
                        "median_distance": None,
                        "mean_distance": None,
                        "min_distance": None,
                        "max_distance": None,
                    }

        return {
            "grid": grid,
            "row_totals": row_totals,
            "col_totals": col_totals,
            "total_count": len(records_list),
        }

    table_unrec = compute_table(unrec_records, "nearest_centroid_distance")
    table_sing = compute_table(singleton_records, "nearest_other_centroid_distance")

    # Combined table using nearest distance (for singletons, to nearest other cluster)
    combined_records = []
    for r in unrec_records:
        rc = dict(r)
        rc["eval_dist"] = r["nearest_centroid_distance"]
        combined_records.append(rc)
    for r in singleton_records:
        rc = dict(r)
        rc["eval_dist"] = r["nearest_other_centroid_distance"]
        combined_records.append(rc)
    table_combined = compute_table(combined_records, "eval_dist")

    # Recoverable band stats for Unrecognized faces
    recov_unrec = [r for r in unrec_records if 0.45 <= r["nearest_centroid_distance"] <= 0.65]
    recov_high_yaw_45 = [r for r in recov_unrec if r["is_high_yaw_45"]]
    recov_seed_yaw_60 = [r for r in recov_unrec if r["is_seed_profile_yaw_60"]]
    recov_extreme_yaw_70 = [r for r in recov_unrec if r["is_extreme_pose_yaw_70"]]

    summary = {
        "dataset": "Pinned 259-photo baseline fixture",
        "total_photos": len(photos_dict),
        "total_detected_faces": len(unrec_records) + sum(len(p["faces"]) for p in people),
        "total_people_clusters": len(people),
        "total_singletons": len(singletons),
        "total_unrecognized_faces": len(unrec_records),
        "total_analyzed_faces": len(unrec_records) + len(singleton_records),
        "unrecognized_recoverable_band_analysis": {
            "band_definition": "[0.45, 0.65] (between attach_distance_cap=0.45 and maybe_threshold=0.65)",
            "total_unrecognized": len(unrec_records),
            "faces_in_recoverable_band": len(recov_unrec),
            "share_of_all_unrecognized_pct": round(len(recov_unrec) / len(unrec_records) * 100, 2),
            "high_yaw_breakdown_in_recoverable_band": {
                "high_yaw_45_plus_count": len(recov_high_yaw_45),
                "high_yaw_45_plus_share_pct": round(len(recov_high_yaw_45) / len(recov_unrec) * 100, 2),
                "seed_profile_yaw_gt_60_count": len(recov_seed_yaw_60),
                "seed_profile_yaw_gt_60_share_pct": round(len(recov_seed_yaw_60) / len(recov_unrec) * 100, 2),
                "extreme_pose_yaw_gt_70_count": len(recov_extreme_yaw_70),
                "extreme_pose_yaw_gt_70_share_pct": round(len(recov_extreme_yaw_70) / len(recov_unrec) * 100, 2),
                "sub_bands": {
                    "0_to_15_deg": {
                        "count": sum(1 for r in recov_unrec if r["yaw_deg"] < 15.0),
                        "share_pct": round(sum(1 for r in recov_unrec if r["yaw_deg"] < 15.0) / len(recov_unrec) * 100, 2),
                    },
                    "15_to_30_deg": {
                        "count": sum(1 for r in recov_unrec if 15.0 <= r["yaw_deg"] < 30.0),
                        "share_pct": round(sum(1 for r in recov_unrec if 15.0 <= r["yaw_deg"] < 30.0) / len(recov_unrec) * 100, 2),
                    },
                    "30_to_45_deg": {
                        "count": sum(1 for r in recov_unrec if 30.0 <= r["yaw_deg"] < 45.0),
                        "share_pct": round(sum(1 for r in recov_unrec if 30.0 <= r["yaw_deg"] < 45.0) / len(recov_unrec) * 100, 2),
                    },
                    "45_plus_deg": {
                        "count": sum(1 for r in recov_unrec if r["yaw_deg"] >= 45.0),
                        "share_pct": round(sum(1 for r in recov_unrec if r["yaw_deg"] >= 45.0) / len(recov_unrec) * 100, 2),
                    },
                },
            },
            "unrecognized_distance_bands_overall": {
                "below_045_attach_eligible_but_blocked": {
                    "count": sum(1 for r in unrec_records if r["nearest_centroid_distance"] < 0.45),
                    "share_pct": round(sum(1 for r in unrec_records if r["nearest_centroid_distance"] < 0.45) / len(unrec_records) * 100, 2),
                },
                "recoverable_band_045_to_065": {
                    "count": len(recov_unrec),
                    "share_pct": round(len(recov_unrec) / len(unrec_records) * 100, 2),
                },
                "above_065_distant": {
                    "count": sum(1 for r in unrec_records if r["nearest_centroid_distance"] > 0.65),
                    "share_pct": round(sum(1 for r in unrec_records if r["nearest_centroid_distance"] > 0.65) / len(unrec_records) * 100, 2),
                },
            },
        },
        "singletons_other_centroid_distance_analysis": {
            "total_singletons": len(singleton_records),
            "below_045_count": sum(1 for r in singleton_records if r["nearest_other_centroid_distance"] < 0.45),
            "band_045_to_065_count": sum(1 for r in singleton_records if 0.45 <= r["nearest_other_centroid_distance"] <= 0.65),
            "band_045_to_065_share_pct": round(sum(1 for r in singleton_records if 0.45 <= r["nearest_other_centroid_distance"] <= 0.65) / len(singleton_records) * 100, 2),
            "above_065_count": sum(1 for r in singleton_records if r["nearest_other_centroid_distance"] > 0.65),
            "above_065_share_pct": round(sum(1 for r in singleton_records if r["nearest_other_centroid_distance"] > 0.65) / len(singleton_records) * 100, 2),
        },
        "tables": {
            "unrecognized_faces": table_unrec,
            "singletons": table_sing,
            "combined": table_combined,
        },
    }

    full_payload = {
        "metadata": summary,
        "unrecognized_faces": unrec_records,
        "singletons": singleton_records,
    }

    return full_payload, summary


def format_markdown_table(title: str, table_data: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"### {title} (Total: {table_data['total_count']})")
    lines.append("")
    lines.append("| Yaw Bucket | < 64 px | 64 – 128 px | 128+ px | Total Faces |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")

    yaw_labels = [
        ("0-15", "0° – 15° (Frontal)"),
        ("15-30", "15° – 30° (Slight Angle)"),
        ("30-45", "30° – 45° (Quarter Turn)"),
        ("45+", "45°+ (Severe / Profile)"),
    ]
    grid = table_data["grid"]
    row_totals = table_data["row_totals"]
    col_totals = table_data["col_totals"]

    for y_key, y_display in yaw_labels:
        cols = []
        for s_key in ["<64", "64-128", "128+"]:
            cell = grid[y_key][s_key]
            cnt = cell["count"]
            med = cell["median_distance"]
            if cnt > 0 and med is not None:
                cols.append(f"**{cnt}**<br>*(med: {med:.4f})*")
            else:
                cols.append("0<br>*(—)*")
        row_tot = row_totals[y_key]
        lines.append(f"| **{y_display}** | {cols[0]} | {cols[1]} | {cols[2]} | **{row_tot}** |")

    # Column totals
    c_lt64 = col_totals["<64"]
    c_mid = col_totals["64-128"]
    c_gt128 = col_totals["128+"]
    tot = table_data["total_count"]
    lines.append(f"| **Total by Size** | **{c_lt64}** | **{c_mid}** | **{c_gt128}** | **{tot}** |")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze Unrecognized faces and Singletons on baseline")
    parser.add_argument("--baseline", default="eval/baseline", help="Baseline fixture directory")
    parser.add_argument("--cache", default="export.work", help="Embeddings cache directory")
    parser.add_argument("--out", default="eval/baseline_unrecognized_singletons_analysis.json", help="Output JSON path")
    args = parser.parse_args()

    print("=" * 80)
    print("RUNNING ANALYSIS ON PINNED 259-PHOTO BASELINE")
    print("=" * 80)

    payload, summary = build_analysis(args.baseline, args.cache)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    json_bytes = json.dumps(payload, indent=2).encode("utf-8")
    with open(out_path, "wb") as f:
        f.write(json_bytes)

    # Compute SHA-256
    sha256_hash = hashlib.sha256(json_bytes).hexdigest()
    sha_file = out_path.with_suffix(".json.sha256")
    with open(sha_file, "w", encoding="utf-8") as sf:
        sf.write(f"{sha256_hash}  {out_path.name}\n")

    # Also mirror into evidence directory for audit record
    evidence_dir = Path("evidence")
    if evidence_dir.exists():
        ev_json = evidence_dir / out_path.name
        with open(ev_json, "wb") as f:
            f.write(json_bytes)
        with open(evidence_dir / sha_file.name, "w", encoding="utf-8") as ef:
            ef.write(f"{sha256_hash}  {out_path.name}\n")

    print(f"[OK] Saved raw output JSON ({len(json_bytes)} bytes) to: {out_path}")
    print(f"[OK] SHA-256: {sha256_hash}")
    print(f"[OK] SHA-256 file saved to: {sha_file}")
    print()

    # Print markdown tables
    print(format_markdown_table("Table 1: Unrecognized Faces (Nearest Centroid Distance)", summary["tables"]["unrecognized_faces"]))
    print(format_markdown_table("Table 2: Singletons (Nearest OTHER Centroid Distance)", summary["tables"]["singletons"]))
    print(format_markdown_table("Table 3: Combined Unrecognized + Singletons", summary["tables"]["combined"]))

    recov_info = summary["unrecognized_recoverable_band_analysis"]
    print("=" * 80)
    print("RECOVERABLE BAND [0.45, 0.65] KEY FINDINGS:")
    print(f"Total Unrecognized Faces: {recov_info['total_unrecognized']}")
    print(f"Faces in [0.45, 0.65]: {recov_info['faces_in_recoverable_band']} ({recov_info['share_of_all_unrecognized_pct']}%)")
    hy_info = recov_info["high_yaw_breakdown_in_recoverable_band"]
    print(f"High-Yaw (>= 45°) in band: {hy_info['high_yaw_45_plus_count']} of {recov_info['faces_in_recoverable_band']} ({hy_info['high_yaw_45_plus_share_pct']}%)")
    print(f"Seed Profile Limit (> 60°) in band: {hy_info['seed_profile_yaw_gt_60_count']} of {recov_info['faces_in_recoverable_band']} ({hy_info['seed_profile_yaw_gt_60_share_pct']}%)")
    print(f"Extreme Pose (> 70°) in band: {hy_info['extreme_pose_yaw_gt_70_count']} of {recov_info['faces_in_recoverable_band']} ({hy_info['extreme_pose_yaw_gt_70_share_pct']}%)")
    print("=" * 80)


if __name__ == "__main__":
    main()

