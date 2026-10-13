"""Generates a 20-photo privacy-safe synthetic bundle for Phase 2 Pages deployment.

Generates 20 abstract synthetic photos, thumbnails, face crops, config.json,
people.json, and copies built viewer assets into a deployable bundle.
"""

from __future__ import annotations
import json
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def build_synthetic_bundle(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir = output_dir / "thumbs"
    faces_dir = output_dir / "faces"
    thumbs_dir.mkdir(exist_ok=True)
    faces_dir.mkdir(exist_ok=True)

    colors = [
        (66, 133, 244), (234, 67, 53), (251, 188, 5), (52, 168, 83),
        (103, 58, 183), (233, 30, 99), (0, 188, 212), (255, 87, 34),
        (63, 81, 181), (156, 39, 176), (0, 150, 136), (255, 152, 0),
        (33, 150, 243), (76, 175, 80), (121, 85, 72), (96, 125, 139),
        (244, 67, 54), (139, 195, 74), (255, 193, 7), (158, 158, 158),
    ]

    photos_map = {}
    
    # 1. Generate 20 synthetic photos and thumbnails
    for i in range(1, 21):
        pid = f"synth_{i:02d}"
        bg_color = colors[(i - 1) % len(colors)]
        
        # High-res photo image
        img = Image.new("RGB", (800, 600), color=bg_color)
        draw = ImageDraw.Draw(img)
        # Draw avatar placeholder
        cx, cy = 400, 260
        r = 120
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
        # Eyes and smile
        draw.ellipse([cx - 45, cy - 30, cx - 25, cy - 10], fill=bg_color)
        draw.ellipse([cx + 25, cy - 30, cx + 45, cy - 10], fill=bg_color)
        draw.arc([cx - 40, cy + 10, cx + 40, cy + 60], start=0, end=180, fill=bg_color, width=8)
        
        # Text label
        draw.text((cx - 80, cy + 150), f"Synthetic Photo #{i:02d}", fill=(255, 255, 255))
        
        # Save thumb
        thumb = img.resize((240, 180), Image.Resampling.LANCZOS)
        thumb.save(thumbs_dir / f"{pid}.jpg", "JPEG", quality=90)
        
        photos_map[pid] = {
            "name": f"synth_{i:02d}.jpg",
            "thumb": f"thumbs/{pid}.jpg",
            "download": None,
            "width": 800,
            "height": 600,
        }

    # 2. Generate 5 representative person face crops
    people_defs = [
        {"id": "c_01", "label": "Alice (Synthetic)", "photos": ["synth_01", "synth_02", "synth_03", "synth_04", "synth_05"]},
        {"id": "c_02", "label": "Bob (Synthetic)", "photos": ["synth_06", "synth_07", "synth_08", "synth_09"]},
        {"id": "c_03", "label": "Charlie (Synthetic)", "photos": ["synth_10", "synth_11", "synth_12", "synth_13"]},
        {"id": "c_04", "label": "Diana (Synthetic)", "photos": ["synth_14", "synth_15", "synth_16"]},
        {"id": "c_05", "label": "Evan (Synthetic)", "photos": ["synth_17", "synth_18", "synth_19"]},
    ]

    people_list = []
    for idx, pdef in enumerate(people_defs, 1):
        cid = pdef["id"]
        # Face crop
        face_img = Image.new("RGB", (128, 128), color=colors[idx - 1])
        f_draw = ImageDraw.Draw(face_img)
        f_draw.ellipse([24, 24, 104, 104], fill=(255, 255, 255))
        f_draw.ellipse([44, 48, 54, 58], fill=colors[idx - 1])
        f_draw.ellipse([74, 48, 84, 58], fill=colors[idx - 1])
        f_draw.arc([46, 68, 82, 88], start=0, end=180, fill=colors[idx - 1], width=4)
        face_path = f"faces/{cid}.jpg"
        face_img.save(output_dir / face_path, "JPEG", quality=92)

        faces_objs = []
        for p_photo in pdef["photos"]:
            faces_objs.append({
                "face_id": f"f_{p_photo}_001",
                "photo_id": p_photo,
                "file_name": f"{p_photo}.jpg",
                "det_score": 0.95,
                "bbox": [280.0, 140.0, 520.0, 380.0],
            })

        people_list.append({
            "id": cid,
            "label": pdef["label"],
            "face": face_path,
            "photo_ids": pdef["photos"],
            "photos": pdef["photos"],
            "faces": faces_objs,
            "merged_from": [cid],
            "merged_from_numbering": f"pre-merge {idx}",
            "maybe_photos": [],
        })

    # 3. Generate 2 unrecognized faces and 1 no-face photo
    unrec_faces = []
    for u_idx, u_pid in enumerate(["synth_02", "synth_12"], 1):
        u_crop = Image.new("RGB", (128, 128), color=(140, 140, 150))
        u_draw = ImageDraw.Draw(u_crop)
        u_draw.ellipse([30, 30, 98, 98], fill=(220, 220, 220))
        u_draw.text((45, 55), f"U{u_idx}", fill=(50, 50, 50))
        u_file = f"faces/u_{u_idx:03d}.jpg"
        u_crop.save(output_dir / u_file, "JPEG", quality=90)
        unrec_faces.append({
            "face_id": f"f_{u_pid}_999",
            "photo_id": u_pid,
            "file_name": f"{u_pid}.jpg",
            "face": u_file,
            "rejection_reason": "unattached_profile",
            "det_score": 0.58,
        })

    unrecognized_group = {
        "photo_ids": ["synth_20"],
        "faces": unrec_faces,
    }

    # 4. Save people.json
    people_data = {
        "version": 1,
        "generated_at": "2026-10-13T12:00:00+00:00",
        "photos": photos_map,
        "people": people_list,
        "unrecognized": unrecognized_group,
    }
    with open(output_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_data, f, indent=2)

    # 5. Save config.json
    config_data = {
        "title": "PhotoSorter Privacy-Safe Gallery",
        "subtitle": "Synthetic 20-Photo Demonstration (Generated Avatars)",
        "hide_single_photo_default": False,
        "include_maybe": False,
        "accent": "#6366f1",
        "footer": "Deployed via PhotoSorter Phase 2 Privacy-Safe Deploy Test",
    }
    with open(output_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    # 6. Copy viewer build files
    viewer_dist = Path("viewer/dist")
    if (viewer_dist / "index.html").exists():
        shutil.copy2(viewer_dist / "index.html", output_dir / "index.html")
    if (viewer_dist / "assets").exists():
        if (output_dir / "assets").exists():
            shutil.rmtree(output_dir / "assets")
        shutil.copytree(viewer_dist / "assets", output_dir / "assets")

    # 7. Add .nojekyll for GitHub Pages
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    # 8. Copy or adapt gallery.html
    export_gallery = Path("export/gallery.html")
    if export_gallery.exists():
        shutil.copy2(export_gallery, output_dir / "gallery.html")

    print(f"[SUCCESS] Synthetic bundle generated in {output_dir}")
    print(f"  - Photos: {len(photos_map)} (20 synthetic photos)")
    print(f"  - People: {len(people_list)} (5 synthetic clusters)")
    print(f"  - Unrecognized faces: {len(unrec_faces)}")
    print(f"  - No-face photos: {len(unrecognized_group['photo_ids'])}")
    print(f"  - Files in bundle: {sorted([p.name for p in output_dir.iterdir()])}")


if __name__ == "__main__":
    target = Path("eval/synthetic_bundle")
    build_synthetic_bundle(target)
