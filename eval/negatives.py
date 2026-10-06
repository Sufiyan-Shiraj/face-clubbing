from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import numpy as np

def generate_same_photo_negatives(
    photos_cache: Dict[str, Any],
    same_photo_merge_max: float = 0.40,
    seed_min_size: int = 64,
    seed_max_yaw: float = 60.0,
    seed_min_score: float = 0.70
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates negative pairs from seed faces in the same photo.
    Excludes pairs whose distance is <= same_photo_merge_max (collage candidates).

    Returns:
        (negative_pairs, excluded_pairs)
        where each item is a dict with:
        {
            "photo_id": str,
            "face1_id": str,
            "face2_id": str,
            "distance_std": float,
            "distance_flip": Optional[float]
        }
    """
    seeds_by_photo = defaultdict(list)

    for pid, pdata in photos_cache.items():
        # Support PhotoRecord object or dict
        faces = pdata.faces if hasattr(pdata, "faces") else pdata.get("faces", [])
        for f in faces:
            bbox = f.bbox if hasattr(f, "bbox") else f["bbox"]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            dim = min(w, h)

            pose = f.pose if hasattr(f, "pose") else f.get("pose", [0, 0, 0])
            yaw = abs(pose[1]) if pose and len(pose) >= 2 else 0.0

            score = f.det_score if hasattr(f, "det_score") else f.get("det_score", 0.0)

            if dim >= seed_min_size and yaw <= seed_max_yaw and score >= seed_min_score:
                fid = f.face_id if hasattr(f, "face_id") else f["face_id"]
                emb_std = f.embedding if hasattr(f, "embedding") else f.get("embedding")
                emb_flp = f.embedding_flipped if hasattr(f, "embedding_flipped") else f.get("embedding_flipped")
                seeds_by_photo[pid].append({
                    "face_id": fid,
                    "embedding": np.array(emb_std, dtype=np.float32) if emb_std is not None else None,
                    "embedding_flipped": np.array(emb_flp, dtype=np.float32) if emb_flp is not None else None,
                })

    negative_pairs = []
    excluded_pairs = []

    for pid, seeds in seeds_by_photo.items():
        n = len(seeds)
        if n < 2:
            continue
        for i in range(n):
            for j in range(i + 1, n):
                s1 = seeds[i]
                s2 = seeds[j]
                if s1["embedding"] is None or s2["embedding"] is None:
                    continue

                d_std = float(1.0 - np.dot(s1["embedding"], s2["embedding"]))
                d_flp = None
                if s1["embedding_flipped"] is not None and s2["embedding_flipped"] is not None:
                    d_flp = float(1.0 - np.dot(s1["embedding_flipped"], s2["embedding_flipped"]))

                pair_info = {
                    "photo_id": pid,
                    "face1_id": min(s1["face_id"], s2["face_id"]),
                    "face2_id": max(s1["face_id"], s2["face_id"]),
                    "distance_std": d_std,
                    "distance_flip": d_flp
                }

                if d_std <= same_photo_merge_max:
                    excluded_pairs.append(pair_info)
                else:
                    negative_pairs.append(pair_info)

    return negative_pairs, excluded_pairs
