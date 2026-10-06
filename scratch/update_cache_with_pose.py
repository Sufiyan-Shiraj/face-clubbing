"""Updates existing cache with pose (yaw/pitch/roll) for all detected faces.
Saves back to export/.cache/*.json.
Identifies faces moved to Unrecognized due to extreme_pose (abs(yaw) > max_yaw).
Generates contact sheet for extreme pose faces with full filenames.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import time
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

from backend.engine.cache import EmbeddingCache
from backend.engine.loader import ImageLoader
from backend.engine.models import PhotoRecord
from insightface.app import FaceAnalysis
from insightface.app.common import Face

def main():
    cache_dir = Path("export/.cache").resolve()
    cache = EmbeddingCache(cache_dir)
    loader = ImageLoader()

    # Load InsightFace landmark_3d_68
    print("Initializing landmark_3d_68 model...")
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0)
    pose_model = app.models.get("landmark_3d_68")
    if not pose_model:
        raise RuntimeError("landmark_3d_68 not found in buffalo_l")

    json_files = list(cache_dir.glob("*.json"))
    print(f"Found {len(json_files)} cached photo records.")

    total_faces = 0
    faces_with_pose = 0
    extreme_pose_faces = []
    max_yaw = 70.0

    t0 = time.time()
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
        record = PhotoRecord.from_dict(data)

        if not record.faces:
            continue

        needs_update = any(face.pose is None for face in record.faces)
        orig_bgr = None

        for face in record.faces:
            total_faces += 1
            face_w = face.bbox[2] - face.bbox[0]
            face_h = face.bbox[3] - face.bbox[1]
            face_dim = min(face_w, face_h)

            was_good = (face.det_score >= 0.50 and face_dim >= 64)

            if face.pose is None:
                if orig_bgr is None:
                    rgb_img, _, _, _ = loader.load_image(record.original_path)
                    orig_bgr = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

                kps = np.array(face.landmarks) if face.landmarks else None
                face_obj = Face(bbox=np.array(face.bbox), kps=kps, det_score=face.det_score)
                pose_model.get(orig_bgr, face_obj)
                if hasattr(face_obj, "pose") and face_obj.pose is not None:
                    face.pose = [float(p) for p in face_obj.pose]
                    needs_update = True

            yaw = abs(face.pose[1]) if face.pose and len(face.pose) >= 2 else 0.0

            if face.det_score < 0.50:
                face.is_good_quality = False
                face.rejection_reason = f"low_det_score ({face.det_score:.2f} < 0.50)"
            elif face_dim < 64:
                face.is_good_quality = False
                face.rejection_reason = f"face_too_small ({face_dim:.0f}px < 64px)"
            elif yaw > max_yaw:
                face.is_good_quality = False
                face.rejection_reason = "extreme_pose"
                if was_good:
                    extreme_pose_faces.append({
                        "face_id": face.face_id,
                        "photo_id": record.photo_id,
                        "file_name": record.file_name,
                        "original_path": record.original_path,
                        "bbox": face.bbox,
                        "pose": face.pose,
                        "yaw": yaw,
                    })
            else:
                face.is_good_quality = True
                face.rejection_reason = None

            if face.pose is not None:
                faces_with_pose += 1

        if needs_update or True:
            cache.save(record)

    t1 = time.time()
    print(f"Updated cache in {t1 - t0:.2f}s.")
    print(f"Total faces: {total_faces}, faces with pose: {faces_with_pose}")
    print(f"Faces moved to Unrecognized due to extreme_pose (yaw > {max_yaw}): {len(extreme_pose_faces)}")

    for ef in extreme_pose_faces:
        print(f"  {ef['face_id']} in {ef['file_name']}: yaw={ef['yaw']:.1f} deg (pose={ef['pose']})")

    # Generate contact sheet for extreme pose faces
    if extreme_pose_faces:
        out_dir = Path("report_assets_v2")
        out_dir.mkdir(parents=True, exist_ok=True)
        cs_path = out_dir / "extreme_pose_faces.jpg"

        # Create contact sheet with crop + filename label
        crop_size = 200
        padding = 10
        label_height = 40
        cols = min(4, len(extreme_pose_faces))
        rows = (len(extreme_pose_faces) + cols - 1) // cols

        cell_w = crop_size + padding * 2
        cell_h = crop_size + label_height + padding * 2
        sheet_w = cols * cell_w
        sheet_h = rows * cell_h

        sheet = Image.new("RGB", (sheet_w, sheet_h), color=(240, 240, 240))
        draw = ImageDraw.Draw(sheet)

        from backend.engine.thumbnails import ThumbnailGenerator
        tg = ThumbnailGenerator(thumb_size=400, face_crop_size=crop_size)

        for idx, ef in enumerate(extreme_pose_faces):
            r = idx // cols
            c = idx % cols
            x = c * cell_w + padding
            y = r * cell_h + padding

            # Get crop
            crop_dest = Path(f"export/.cache/crops/{ef['face_id']}.jpg")
            if not crop_dest.exists():
                rgb_img, _, _, _ = loader.load_image(ef["original_path"])
                tg.generate_square_face_crop_from_image(Image.fromarray(rgb_img), ef["bbox"], crop_dest)

            crop_img = Image.open(crop_dest).resize((crop_size, crop_size), Image.Resampling.LANCZOS)
            sheet.paste(crop_img, (x, y))

            # Label with full filename and yaw
            label_text = f"{ef['file_name']}\nyaw={ef['yaw']:.1f}°"
            draw.text((x, y + crop_size + 4), label_text, fill=(20, 20, 20))

        sheet.save(cs_path, quality=90)
        print(f"Saved extreme pose contact sheet to {cs_path}")

if __name__ == "__main__":
    main()
