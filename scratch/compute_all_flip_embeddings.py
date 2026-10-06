import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import cv2
import numpy as np
from insightface.utils import face_align
from insightface.app import FaceAnalysis

from backend.engine.cache import EmbeddingCache
from backend.engine.loader import ImageLoader
import json

def main():
    cache = EmbeddingCache("export/.cache")
    photos = cache.load_all()

    print("Initializing InsightFace recognition model for flip averaging...")
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))
    rec = app.models["recognition"]
    loader = ImageLoader(max_dimension=1600)

    flip_embs = {}
    start_t = time.time()
    total_faces = 0

    for photo_id, record in photos.items():
        if not record.faces:
            continue
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
            flip_embs[face.face_id] = feat.tolist()
            total_faces += 1

    print(f"Computed flip-averaged embeddings for {total_faces} faces in {time.time() - start_t:.1f}s.")
    out_path = Path("scratch/flip_embeddings.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flip_embs, f)
    print(f"Saved flip-averaged embeddings to {out_path} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
