import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from collections import defaultdict
import numpy as np
import cv2
from insightface.utils import face_align
from insightface.app import FaceAnalysis

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
from backend.engine.loader import ImageLoader

def enhance_crop(aimg):
    gaussian = cv2.GaussianBlur(aimg, (0, 0), 2.0)
    unsharp = cv2.addWeighted(aimg, 1.5, gaussian, -0.5, 0)
    return unsharp

def main():
    with open("ground_truth.json", "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    cache = EmbeddingCache("export/.cache")
    records = cache.load_all()

    # Find face objects for all ground truth faces
    all_gt_fids = set()
    for s_name, fids in gt_data["sets"].items():
        all_gt_fids.update(fids)

    face_map = {}
    photo_map = {}
    for pid, precord in records.items():
        for face in precord.faces:
            if face.face_id in all_gt_fids:
                face_map[face.face_id] = face
                photo_map[face.face_id] = precord

    print(f"Found {len(face_map)}/{len(all_gt_fids)} ground truth faces in cache.")

    # Initialize FaceAnalysis for flip-averaged and enhanced embeddings
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))
    rec = app.models["recognition"]
    loader = ImageLoader(max_dimension=1600)

    # Preload photos needed
    loaded_bgr = {}
    for fid, precord in photo_map.items():
        if precord.original_path not in loaded_bgr:
            rgb, _, _, _ = loader.load_image(precord.original_path)
            loaded_bgr[precord.original_path] = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    # Condition 1: Standard embeddings
    embs_standard = {}
    for fid, face in face_map.items():
        embs_standard[fid] = face.embedding

    # Condition 2: Flip-averaged embeddings
    embs_flip = {}
    for fid, face in face_map.items():
        precord = photo_map[fid]
        bgr = loaded_bgr[precord.original_path]
        kps = np.array(face.landmarks, dtype=np.float32)
        aimg = face_align.norm_crop(bgr, landmark=kps, image_size=112)

        feat_orig = rec.get_feat(aimg).flatten()
        aimg_flip = cv2.flip(aimg, 1)
        feat_flip = rec.get_feat(aimg_flip).flatten()
        feat = (feat_orig + feat_flip) / 2.0
        norm = np.linalg.norm(feat)
        if norm > 1e-8:
            feat = feat / norm
        embs_flip[fid] = feat

    # Condition 3: Flip-averaged + small face enhancement (< 112px)
    embs_flip_enhanced = {}
    for fid, face in face_map.items():
        precord = photo_map[fid]
        bgr = loaded_bgr[precord.original_path]
        kps = np.array(face.landmarks, dtype=np.float32)
        aimg = face_align.norm_crop(bgr, landmark=kps, image_size=112)

        w = face.bbox[2] - face.bbox[0]
        h = face.bbox[3] - face.bbox[1]
        dim = min(w, h)
        if dim < 112:
            aimg = enhance_crop(aimg)

        feat_orig = rec.get_feat(aimg).flatten()
        aimg_flip = cv2.flip(aimg, 1)
        feat_flip = rec.get_feat(aimg_flip).flatten()
        feat = (feat_orig + feat_flip) / 2.0
        norm = np.linalg.norm(feat)
        if norm > 1e-8:
            feat = feat / norm
        embs_flip_enhanced[fid] = feat

    conditions = [
        ("standard", embs_standard),
        ("flip_averaged", embs_flip),
        ("flip_averaged_enhanced", embs_flip_enhanced),
    ]

    all_pairs_by_cond = defaultdict(list)

    for cond_name, emb_dict in conditions:
        print(f"\n========================================================")
        print(f"CONDITION: {cond_name}")
        print(f"========================================================")

        for set_name, fids in gt_data["sets"].items():
            print(f"\n--- Set {set_name} (Pairwise Cosine Distances) ---")
            header = f"{'Face ID':<25}" + "".join([f"{f[-12:]:>15}" for f in fids])
            print(header)
            for f1 in fids:
                row = f"{f1:<25}"
                for f2 in fids:
                    e1 = emb_dict[f1]
                    e2 = emb_dict[f2]
                    d = float(1.0 - np.dot(e1, e2))
                    row += f"{d:>15.4f}"
                print(row)

            # Collect unique pairs
            for i in range(len(fids)):
                for j in range(i+1, len(fids)):
                    f1 = fids[i]
                    f2 = fids[j]
                    d = float(1.0 - np.dot(emb_dict[f1], emb_dict[f2]))
                    all_pairs_by_cond[cond_name].append((set_name, f1, f2, d))

    print("\n========================================================")
    print("SET PAIRS THRESHOLD COUNTS PER CONDITION")
    print("========================================================")
    print(f"{'Condition':<25} | {'<= 0.50':<10} | {'<= 0.60':<10} | {'<= 0.70':<10} | {'<= 0.80':<10} | {'Total Pairs':<10}")
    print("-" * 85)
    for cond_name, _ in conditions:
        pairs = all_pairs_by_cond[cond_name]
        c_50 = sum(1 for p in pairs if p[3] <= 0.50)
        c_60 = sum(1 for p in pairs if p[3] <= 0.60)
        c_70 = sum(1 for p in pairs if p[3] <= 0.70)
        c_80 = sum(1 for p in pairs if p[3] <= 0.80)
        print(f"{cond_name:<25} | {c_50:<10} | {c_60:<10} | {c_70:<10} | {c_80:<10} | {len(pairs):<10}")

    # Next: Singletons analysis
    # "how many of the 82 final singleton clusters have no maybe link, and for those, the distance to their nearest other cluster. Numbers only, no image descriptions."
    print("\n========================================================")
    print("FINAL SINGLETON CLUSTERS WITH NO MAYBE LINK ANALYSIS")
    print("========================================================")
    cl = FaceClusterer(
        distance_threshold=0.50,
        seed_min_face_size=64,
        seed_max_yaw=60.0,
        seed_min_det_score=0.70,
        second_pass_merge=True,
        same_photo_merge_max=0.40,
    )
    people_final, _ = cl.cluster(records)
    print(f"Total final clusters: {len(people_final)}")
    singletons = [p for p in people_final if len(p.photo_ids) == 1]
    print(f"Total final singletons: {len(singletons)}")

    # Compute centroids for all people_final
    final_centroids = [cl.compute_cluster_centroid(p.faces, top_k=5) for p in people_final]
    cluster_idx_map = {p.id: idx for idx, p in enumerate(people_final)}

    # Clusters with maybe link from cl.maybe_groups
    clusters_with_maybe = set()
    for g in cl.maybe_groups:
        for c_id in g["clusters"]:
            clusters_with_maybe.add(c_id)

    singletons_no_maybe = [s for s in singletons if s.id not in clusters_with_maybe]
    print(f"Singletons WITH maybe link: {len(singletons) - len(singletons_no_maybe)}")
    print(f"Singletons with NO maybe link: {len(singletons_no_maybe)} (out of {len(singletons)})")

    # For each singleton with no maybe link, find distance to nearest other cluster
    singleton_nearest = []
    for s in singletons_no_maybe:
        s_idx = cluster_idx_map[s.id]
        c_s = final_centroids[s_idx]
        best_d = float("inf")
        best_other = None
        for other_idx, c_other in enumerate(final_centroids):
            if other_idx == s_idx or c_other is None:
                continue
            d = float(1.0 - np.dot(c_s, c_other))
            if d < best_d:
                best_d = d
                best_other = people_final[other_idx].id
        singleton_nearest.append((s.id, best_other, best_d))

    singleton_nearest.sort(key=lambda x: x[2])
    print(f"\nDistance to nearest other cluster for the {len(singletons_no_maybe)} isolated singletons:")
    print(f"{'Singleton ID':<15} | {'Nearest Cluster':<16} | {'Distance':<10}")
    print("-" * 48)
    for sid, nid, dist in singleton_nearest:
        print(f"{sid:<15} | {nid:<16} | {dist:.4f}")

if __name__ == "__main__":
    main()
