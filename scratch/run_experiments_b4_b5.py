import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
import copy
from collections import defaultdict
import numpy as np
import cv2
from PIL import Image
from insightface.utils import face_align
from insightface.app import FaceAnalysis

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
from backend.engine.loader import ImageLoader

def get_cluster_centroid(faces, top_k=5):
    scored_faces = []
    for f in faces:
        if f.embedding is None:
            continue
        w = f.bbox[2] - f.bbox[0]
        h = f.bbox[3] - f.bbox[1]
        dim = min(w, h)
        scored_faces.append((float(f.det_score), dim, f.embedding))
    scored_faces.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top_faces = scored_faces[:top_k]
    if not top_faces:
        return None
    embs = np.stack([x[2] for x in top_faces])
    mean_v = np.mean(embs, axis=0)
    norm = np.linalg.norm(mean_v)
    if norm > 1e-8:
        mean_v = mean_v / norm
    return mean_v

def run_clustering_with_merge(records):
    clusterer = FaceClusterer(
        distance_threshold=0.50,
        seed_min_face_size=64,
        seed_max_yaw=60.0,
        seed_min_det_score=0.70,
    )
    people_before, unrecognized = clusterer.cluster(records)
    singletons_before = sum(1 for p in people_before if len(p.photo_ids) == 1)

    # Centroids
    centroids = [get_cluster_centroid(p.faces) for p in people_before]
    n = len(people_before)

    # Auto-merge graph (d < 0.50)
    adj = defaultdict(list)
    for i in range(n):
        if centroids[i] is None:
            continue
        for j in range(i + 1, n):
            if centroids[j] is None:
                continue
            dist = float(1.0 - np.dot(centroids[i], centroids[j]))
            if dist < 0.50:
                adj[i].append(j)
                adj[j].append(i)

    visited = set()
    merged_components = []
    for i in range(n):
        if i not in visited:
            comp = []
            queue = [i]
            visited.add(i)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            merged_components.append(comp)

    merged_clusters_data = []
    for comp in merged_components:
        all_faces = []
        all_photo_ids = []
        for idx in comp:
            all_faces.extend(people_before[idx].faces)
            for pid in people_before[idx].photo_ids:
                if pid not in all_photo_ids:
                    all_photo_ids.append(pid)
        merged_clusters_data.append({
            "photo_ids": all_photo_ids,
            "faces": all_faces,
        })

    merged_clusters_data.sort(key=lambda x: (len(x["photo_ids"]), len(x["faces"])), reverse=True)
    singletons_after = sum(1 for c in merged_clusters_data if len(c["photo_ids"]) == 1)

    return {
        "clusters_before": len(people_before),
        "singletons_before": singletons_before,
        "unrecognized_faces": len(unrecognized.faces),
        "unrecognized_photos": len(unrecognized.photo_ids),
        "clusters_after": len(merged_clusters_data),
        "singletons_after": singletons_after,
        "people_before": people_before,
        "merged_clusters_data": merged_clusters_data,
    }

def main():
    print("=== Loading Records and Initializing Models ===")
    cache = EmbeddingCache("export/.cache")
    records_base = cache.load_all()
    print(f"Loaded {len(records_base)} photo records.")

    # 1. Baseline Run
    print("\n--- Running Baseline Clustering ---")
    base_results = run_clustering_with_merge(records_base)
    print(f"Baseline: Clusters before: {base_results['clusters_before']}, Singletons before: {base_results['singletons_before']}")
    print(f"Baseline: Unrecognized faces: {base_results['unrecognized_faces']}, Unrecognized photos: {base_results['unrecognized_photos']}")
    print(f"Baseline: Clusters after merge: {base_results['clusters_after']}, Singletons after: {base_results['singletons_after']}")

    # 2. Initialize InsightFace Recognition Model for Experiments
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))
    rec = app.models["recognition"]
    loader = ImageLoader(max_dimension=1600)

    # -------------------------------------------------------------
    # B.4: Flip-averaged embedding experiment
    # -------------------------------------------------------------
    print("\n--- Computing Flip-Averaged Embeddings for all faces ---")
    records_flip = copy.deepcopy(records_base)
    start_t = time.time()
    total_faces_processed = 0

    for photo_id, record in records_flip.items():
        if not record.faces:
            continue
        # Load image once per photo
        rgb_img, _, _, _ = loader.load_image(record.original_path)
        bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

        for face in record.faces:
            if face.landmarks is None:
                continue
            kps = np.array(face.landmarks, dtype=np.float32)
            aimg = face_align.norm_crop(bgr_img, landmark=kps, image_size=112)
            if aimg is None or aimg.shape[0] != 112 or aimg.shape[1] != 112:
                continue

            feat_orig = rec.get_feat(aimg).flatten()
            aimg_flip = cv2.flip(aimg, 1)
            feat_flip = rec.get_feat(aimg_flip).flatten()

            feat = (feat_orig + feat_flip) / 2.0
            norm = np.linalg.norm(feat)
            if norm > 1e-8:
                feat = feat / norm
            face.embedding = feat
            total_faces_processed += 1

    print(f"Flip-averaged {total_faces_processed} faces in {time.time() - start_t:.1f}s.")

    print("\n--- Running Clustering with Flip-Averaged Embeddings ---")
    flip_results = run_clustering_with_merge(records_flip)
    print(f"Flip-Averaged: Clusters before: {flip_results['clusters_before']} (diff: {flip_results['clusters_before'] - base_results['clusters_before']:+d})")
    print(f"Flip-Averaged: Singletons before: {flip_results['singletons_before']} (diff: {flip_results['singletons_before'] - base_results['singletons_before']:+d})")
    print(f"Flip-Averaged: Unrecognized faces: {flip_results['unrecognized_faces']} (diff: {flip_results['unrecognized_faces'] - base_results['unrecognized_faces']:+d})")
    print(f"Flip-Averaged: Unrecognized photos: {flip_results['unrecognized_photos']} (diff: {flip_results['unrecognized_photos'] - base_results['unrecognized_photos']:+d})")
    print(f"Flip-Averaged: Clusters after merge: {flip_results['clusters_after']} (diff: {flip_results['clusters_after'] - base_results['clusters_after']:+d})")
    print(f"Flip-Averaged: Singletons after merge: {flip_results['singletons_after']} (diff: {flip_results['singletons_after'] - base_results['singletons_after']:+d})")

    # -------------------------------------------------------------
    # B.5: Sharpening or upscaling small faces experiment
    # Known split pairs: p001 vs p121, p080, p129
    # -------------------------------------------------------------
    print("\n--- Running B.5: Sharpening / Upscaling Small Faces Experiment ---")
    # Identify faces in p001, p080, p121, p129 from base_results['people_before']
    base_people_map = {p.id: p for p in base_results['people_before']}

    target_clusters = ["p001", "p080", "p121", "p129"]
    for cid in target_clusters:
        p = base_people_map.get(cid)
        if p:
            print(f"Cluster {cid}: {len(p.faces)} faces")
            for f in p.faces:
                w = f.bbox[2] - f.bbox[0]
                h = f.bbox[3] - f.bbox[1]
                print(f"   Face {f.face_id}: photo {f.photo_id}, det_score={f.det_score:.3f}, dim={min(w,h):.1f}x{max(w,h):.1f}")

    # Compute baseline centroid distances between p001 and [p080, p121, p129]
    c_p001_base = get_cluster_centroid(base_people_map["p001"].faces)
    c_p080_base = get_cluster_centroid(base_people_map["p080"].faces)
    c_p121_base = get_cluster_centroid(base_people_map["p121"].faces)
    c_p129_base = get_cluster_centroid(base_people_map["p129"].faces)

    d_base = {
        "p001_vs_p080": float(1.0 - np.dot(c_p001_base, c_p080_base)),
        "p001_vs_p121": float(1.0 - np.dot(c_p001_base, c_p121_base)),
        "p001_vs_p129": float(1.0 - np.dot(c_p001_base, c_p129_base)),
    }
    print("\nBaseline Distances (without sharpening/upscaling):")
    for pair, dist in d_base.items():
        print(f"  {pair}: {dist:.4f}")

    # Sharpening function:
    # Unsharp masking on face crop or original image before embedding:
    def enhance_crop(aimg):
        # Gaussian blur + weighted subtraction (unsharp mask)
        gaussian = cv2.GaussianBlur(aimg, (0, 0), 2.0)
        unsharp = cv2.addWeighted(aimg, 1.5, gaussian, -0.5, 0)
        return unsharp

    # Upscaling function (super-resolution / bicubic 2x upscaling then sharpening):
    def upscale_sharpen_crop(aimg):
        # Resize to 2x then resize back with sharpening
        h, w = aimg.shape[:2]
        up = cv2.resize(aimg, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        gaussian = cv2.GaussianBlur(up, (0, 0), 2.0)
        unsharp = cv2.addWeighted(up, 1.5, gaussian, -0.5, 0)
        down = cv2.resize(unsharp, (w, h), interpolation=cv2.INTER_AREA)
        return down

    # Re-embed faces for p001, p080, p121, p129 with sharpening and with upscale+sharpen
    def reembed_faces_enhanced(people_list, mode="sharpen"):
        enhanced_people = copy.deepcopy(people_list)
        # map photos
        photos_needed = set()
        for p in enhanced_people:
            for f in p.faces:
                photos_needed.add(f.photo_id)

        photo_bgr = {}
        for pid in photos_needed:
            rec = records_base[pid]
            rgb, _, _, _ = loader.load_image(rec.original_path)
            photo_bgr[pid] = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        for p in enhanced_people:
            for f in p.faces:
                bgr = photo_bgr[f.photo_id]
                kps = np.array(f.landmarks, dtype=np.float32)
                aimg = face_align.norm_crop(bgr, landmark=kps, image_size=112)

                # Check face size in original image
                w = f.bbox[2] - f.bbox[0]
                h = f.bbox[3] - f.bbox[1]
                dim = min(w, h)

                # Apply enhancement if small face (< 112px or mode applies to all)
                # Prompt: "sharpening or upscaling small faces before embedding"
                if dim < 112:
                    if mode == "sharpen":
                        aimg = enhance_crop(aimg)
                    elif mode == "upscale_sharpen":
                        aimg = upscale_sharpen_crop(aimg)

                feat = rec.get_feat(aimg).flatten()
                norm = np.linalg.norm(feat)
                if norm > 1e-8:
                    feat = feat / norm
                f.embedding = feat

        return enhanced_people

    print("\nComputing embeddings with Unsharp Mask Sharpening on small faces (<112px)...")
    enhanced_people_sharp = reembed_faces_enhanced([base_people_map[c] for c in target_clusters], mode="sharpen")
    sharp_map = {p.id: p for p in enhanced_people_sharp}
    c_p001_sharp = get_cluster_centroid(sharp_map["p001"].faces)
    c_p080_sharp = get_cluster_centroid(sharp_map["p080"].faces)
    c_p121_sharp = get_cluster_centroid(sharp_map["p121"].faces)
    c_p129_sharp = get_cluster_centroid(sharp_map["p129"].faces)

    d_sharp = {
        "p001_vs_p080": float(1.0 - np.dot(c_p001_sharp, c_p080_sharp)),
        "p001_vs_p121": float(1.0 - np.dot(c_p001_sharp, c_p121_sharp)),
        "p001_vs_p129": float(1.0 - np.dot(c_p001_sharp, c_p129_sharp)),
    }
    print("Sharpened Distances:")
    for pair, dist in d_sharp.items():
        print(f"  {pair}: {dist:.4f} (diff: {dist - d_base[pair]:+.4f})")

    print("\nComputing embeddings with Upscale + Sharpening on small faces (<112px)...")
    enhanced_people_up = reembed_faces_enhanced([base_people_map[c] for c in target_clusters], mode="upscale_sharpen")
    up_map = {p.id: p for p in enhanced_people_up}
    c_p001_up = get_cluster_centroid(up_map["p001"].faces)
    c_p080_up = get_cluster_centroid(up_map["p080"].faces)
    c_p121_up = get_cluster_centroid(up_map["p121"].faces)
    c_p129_up = get_cluster_centroid(up_map["p129"].faces)

    d_up = {
        "p001_vs_p080": float(1.0 - np.dot(c_p001_up, c_p080_up)),
        "p001_vs_p121": float(1.0 - np.dot(c_p001_up, c_p121_up)),
        "p001_vs_p129": float(1.0 - np.dot(c_p001_up, c_p129_up)),
    }
    print("Upscaled + Sharpened Distances:")
    for pair, dist in d_up.items():
        print(f"  {pair}: {dist:.4f} (diff: {dist - d_base[pair]:+.4f})")

    # Save results to json for reporting
    results_summary = {
        "flip_averaging": {
            "baseline": {
                "clusters_before": base_results["clusters_before"],
                "singletons_before": base_results["singletons_before"],
                "unrecognized_faces": base_results["unrecognized_faces"],
                "unrecognized_photos": base_results["unrecognized_photos"],
                "clusters_after": base_results["clusters_after"],
                "singletons_after": base_results["singletons_after"],
            },
            "flip_averaged": {
                "clusters_before": flip_results["clusters_before"],
                "singletons_before": flip_results["singletons_before"],
                "unrecognized_faces": flip_results["unrecognized_faces"],
                "unrecognized_photos": flip_results["unrecognized_photos"],
                "clusters_after": flip_results["clusters_after"],
                "singletons_after": flip_results["singletons_after"],
            },
        },
        "split_pairs_experiment": {
            "without_enhancement": d_base,
            "with_sharpening": d_sharp,
            "with_upscale_sharpening": d_up,
        }
    }
    with open("scratch/experiments_b4_b5_results.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print("\nSaved experiments results to scratch/experiments_b4_b5_results.json")

if __name__ == "__main__":
    main()
