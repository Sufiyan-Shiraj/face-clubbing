import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
import cv2
from insightface.utils import face_align
from insightface.app import FaceAnalysis

from backend.engine.cache import EmbeddingCache
from backend.engine.loader import ImageLoader

def compute_centroid_from_embs(faces, top_k=5):
    # Sort by det_score desc, then dimension desc
    scored = []
    for f in faces:
        w = f["bbox"][2] - f["bbox"][0]
        h = f["bbox"][3] - f["bbox"][1]
        dim = min(w, h)
        scored.append((f["det_score"], dim, f["embedding"]))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top_faces = scored[:top_k]
    embs = np.stack([x[2] for x in top_faces])
    mean_v = np.mean(embs, axis=0)
    norm = np.linalg.norm(mean_v)
    if norm > 1e-8:
        mean_v = mean_v / norm
    return mean_v

def main():
    print("=== Running B.5 Sharpening/Upscaling Experiment ===")
    with open("export/people.json", "r", encoding="utf-8") as f:
        export_data = json.load(f)

    cache = EmbeddingCache("export/.cache")
    cache_records = cache.load_all()

    target_ids = ["p001", "p080", "p121", "p129"]
    people_map = {p["id"]: p for p in export_data["people"] if p["id"] in target_ids}

    # Attach cached embeddings, landmarks and bounding boxes
    for pid in target_ids:
        p = people_map[pid]
        for f in p["faces"]:
            rec = cache_records[f["photo_id"]]
            cached_face = next(cf for cf in rec.faces if cf.face_id == f["face_id"])
            f["embedding"] = cached_face.embedding
            f["landmarks"] = cached_face.landmarks
            f["bbox"] = cached_face.bbox
            f["original_path"] = rec.original_path

    # Baseline centroid distances
    c_p001_base = compute_centroid_from_embs(people_map["p001"]["faces"])
    c_p080_base = compute_centroid_from_embs(people_map["p080"]["faces"])
    c_p121_base = compute_centroid_from_embs(people_map["p121"]["faces"])
    c_p129_base = compute_centroid_from_embs(people_map["p129"]["faces"])

    d_base = {
        "p001 vs p080": float(1.0 - np.dot(c_p001_base, c_p080_base)),
        "p001 vs p121": float(1.0 - np.dot(c_p001_base, c_p121_base)),
        "p001 vs p129": float(1.0 - np.dot(c_p001_base, c_p129_base)),
    }
    print("\nBaseline Distances (without enhancement):")
    for pair, dist in d_base.items():
        print(f"  {pair}: {dist:.4f}")

    # Initialize model
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))
    rec_model = app.models["recognition"]
    loader = ImageLoader(max_dimension=1600)

    # Enhancements
    def enhance_sharpen(aimg):
        gaussian = cv2.GaussianBlur(aimg, (0, 0), 2.0)
        return cv2.addWeighted(aimg, 1.5, gaussian, -0.5, 0)

    def enhance_upscale(aimg):
        h, w = aimg.shape[:2]
        up = cv2.resize(aimg, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        gaussian = cv2.GaussianBlur(up, (0, 0), 2.0)
        unsharp = cv2.addWeighted(up, 1.5, gaussian, -0.5, 0)
        return cv2.resize(unsharp, (w, h), interpolation=cv2.INTER_AREA)

    def recompute_embeddings(mode="sharpen"):
        enhanced_faces_by_pid = {}
        # Preload photos needed
        photos_needed = {}
        for pid in target_ids:
            for f in people_map[pid]["faces"]:
                if f["photo_id"] not in photos_needed:
                    rgb, _, _, _ = loader.load_image(f["original_path"])
                    photos_needed[f["photo_id"]] = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        for pid in target_ids:
            faces_copy = []
            for f in people_map[pid]["faces"]:
                bgr = photos_needed[f["photo_id"]]
                kps = np.array(f["landmarks"], dtype=np.float32)
                aimg = face_align.norm_crop(bgr, landmark=kps, image_size=112)

                w = f["bbox"][2] - f["bbox"][0]
                h = f["bbox"][3] - f["bbox"][1]
                dim = min(w, h)

                # Prompt: "sharpening or upscaling small faces before embedding"
                if dim < 112:
                    if mode == "sharpen":
                        aimg = enhance_sharpen(aimg)
                    elif mode == "upscale":
                        aimg = enhance_upscale(aimg)

                feat = rec_model.get_feat(aimg).flatten()
                norm = np.linalg.norm(feat)
                if norm > 1e-8:
                    feat = feat / norm

                f_c = dict(f)
                f_c["embedding"] = feat
                faces_copy.append(f_c)
            enhanced_faces_by_pid[pid] = faces_copy
        return enhanced_faces_by_pid

    print("\nComputing distances with Sharpening on small faces (<112px)...")
    sharp_faces = recompute_embeddings(mode="sharpen")
    c_p001_sharp = compute_centroid_from_embs(sharp_faces["p001"])
    c_p080_sharp = compute_centroid_from_embs(sharp_faces["p080"])
    c_p121_sharp = compute_centroid_from_embs(sharp_faces["p121"])
    c_p129_sharp = compute_centroid_from_embs(sharp_faces["p129"])

    d_sharp = {
        "p001 vs p080": float(1.0 - np.dot(c_p001_sharp, c_p080_sharp)),
        "p001 vs p121": float(1.0 - np.dot(c_p001_sharp, c_p121_sharp)),
        "p001 vs p129": float(1.0 - np.dot(c_p001_sharp, c_p129_sharp)),
    }
    for pair, dist in d_sharp.items():
        print(f"  {pair}: {dist:.4f} (diff: {dist - d_base[pair]:+.4f})")

    print("\nComputing distances with Upscaling + Sharpening on small faces (<112px)...")
    up_faces = recompute_embeddings(mode="upscale")
    c_p001_up = compute_centroid_from_embs(up_faces["p001"])
    c_p080_up = compute_centroid_from_embs(up_faces["p080"])
    c_p121_up = compute_centroid_from_embs(up_faces["p121"])
    c_p129_up = compute_centroid_from_embs(up_faces["p129"])

    d_up = {
        "p001 vs p080": float(1.0 - np.dot(c_p001_up, c_p080_up)),
        "p001 vs p121": float(1.0 - np.dot(c_p001_up, c_p121_up)),
        "p001 vs p129": float(1.0 - np.dot(c_p001_up, c_p129_up)),
    }
    for pair, dist in d_up.items():
        print(f"  {pair}: {dist:.4f} (diff: {dist - d_base[pair]:+.4f})")

    out_json = {
        "without_enhancement": d_base,
        "with_sharpening": d_sharp,
        "with_upscaling": d_up,
    }
    with open("scratch/b5_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=2)
    print("\nSaved results to scratch/b5_experiment_results.json")

if __name__ == "__main__":
    main()
