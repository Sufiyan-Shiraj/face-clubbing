"""Runs detection size experiment comparing det_size=(640, 640) vs det_size=(1280, 1280)
on the 10 photos with the most faces.
Reports face counts vs 640 and time per photo.
DOES NOT change default configuration.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
import numpy as np
import cv2

from backend.engine.loader import ImageLoader
from insightface.app import FaceAnalysis

def main():
    loader = ImageLoader(max_dimension=1600)
    cache_dir = Path("export/.cache").resolve()

    # Find the 10 photos with the most faces from cached records
    photo_face_counts = []
    for jf in cache_dir.glob("*.json"):
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
        p_path = data["original_path"]
        fname = data["file_name"]
        faces = data.get("faces", [])
        photo_face_counts.append((len(faces), fname, p_path, data["width"], data["height"]))

    photo_face_counts.sort(key=lambda x: x[0], reverse=True)
    top_10 = photo_face_counts[:10]

    print("Top 10 photos with most faces:")
    for count, fname, p_path, w, h in top_10:
        print(f"  {fname}: {count} faces ({w}x{h})")

    # Initialize FaceAnalysis with det_size=(640, 640)
    print("\nInitializing detector with det_size=(640, 640)...")
    app_640 = FaceAnalysis(name="buffalo_l", allowed_modules=["detection"])
    app_640.prepare(ctx_id=0, det_size=(640, 640))

    # Initialize FaceAnalysis with det_size=(1280, 1280)
    print("Initializing detector with det_size=(1280, 1280)...")
    app_1280 = FaceAnalysis(name="buffalo_l", allowed_modules=["detection"])
    app_1280.prepare(ctx_id=0, det_size=(1280, 1280))

    results = []

    # Warmup
    dummy = np.zeros((1066, 1600, 3), dtype=np.uint8)
    app_640.det_model.detect(dummy, max_num=0)
    app_1280.det_model.detect(dummy, max_num=0)

    print("\nRunning benchmark on top 10 photos...")
    for count, fname, p_path, orig_w, orig_h in top_10:
        rgb_img, w, h, _ = loader.load_image(p_path)
        bgr_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

        # Scale down to 1600 longest side for detection per SPEC
        max_side = max(w, h)
        if max_side > 1600:
            scale = max_side / 1600.0
            down_w = max(1, int(round(w / scale)))
            down_h = max(1, int(round(h / scale)))
            down_bgr = cv2.resize(bgr_img, (down_w, down_h), interpolation=cv2.INTER_AREA)
        else:
            scale = 1.0
            down_bgr = bgr_img

        # Benchmark 640x640
        t0 = time.perf_counter()
        bboxes_640, _ = app_640.det_model.detect(down_bgr, max_num=0)
        t_640 = time.perf_counter() - t0

        # Filter: det_score >= 0.50, min face dimension in ORIGINAL pixels >= 64
        valid_640 = 0
        if bboxes_640 is not None:
            for i in range(bboxes_640.shape[0]):
                score = float(bboxes_640[i, 4])
                orig_bw = (bboxes_640[i, 2] - bboxes_640[i, 0]) * scale
                orig_bh = (bboxes_640[i, 3] - bboxes_640[i, 1]) * scale
                if score >= 0.50 and min(orig_bw, orig_bh) >= 64:
                    valid_640 += 1

        # Benchmark 1280x1280
        t0 = time.perf_counter()
        bboxes_1280, _ = app_1280.det_model.detect(down_bgr, max_num=0)
        t_1280 = time.perf_counter() - t0

        valid_1280 = 0
        if bboxes_1280 is not None:
            for i in range(bboxes_1280.shape[0]):
                score = float(bboxes_1280[i, 4])
                orig_bw = (bboxes_1280[i, 2] - bboxes_1280[i, 0]) * scale
                orig_bh = (bboxes_1280[i, 3] - bboxes_1280[i, 1]) * scale
                if score >= 0.50 and min(orig_bw, orig_bh) >= 64:
                    valid_1280 += 1

        results.append({
            "file_name": fname,
            "orig_dims": f"{orig_w}x{orig_h}",
            "faces_640": valid_640,
            "raw_640": len(bboxes_640) if bboxes_640 is not None else 0,
            "time_640_ms": round(t_640 * 1000, 1),
            "faces_1280": valid_1280,
            "raw_1280": len(bboxes_1280) if bboxes_1280 is not None else 0,
            "time_1280_ms": round(t_1280 * 1000, 1),
            "delta_faces": valid_1280 - valid_640,
            "slowdown": round(t_1280 / t_640, 2) if t_640 > 0 else 0,
        })
        print(f"  {fname}: 640->{valid_640} faces ({t_640*1000:.1f}ms) | 1280->{valid_1280} faces ({t_1280*1000:.1f}ms) [delta: {valid_1280 - valid_640:+d}]")

    print("\n--- Summary Table ---")
    print(json.dumps(results, indent=2))

    with open("scratch/det_size_experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
