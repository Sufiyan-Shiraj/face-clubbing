"""Generates the four required contact sheets in report_assets_v3/ with full filenames,
no truncation, strictly following the prompt requirements:
1. Top 10 clusters (rep faces + member samples + full filenames)
2. Merge-diff 0.50 vs 0.60 (40 pairs with smallest distance, labelled with cluster IDs and distances)
3. 20 random single-photo clusters (full filenames)
4. 20 Unrecognized faces including extreme_pose ones (full filenames + rejection reason + yaw)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
from backend.engine.thumbnails import ThumbnailGenerator
from backend.engine.loader import ImageLoader

def get_font(size=14):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()

def ensure_crop(photo, face, cache_crops_p, loader, tg):
    cpath = cache_crops_p / f"{face.face_id}.jpg"
    if not cpath.exists():
        rgb, _, _, pil_img = loader.load_image(photo.original_path)
        tg.generate_square_face_crop_from_image(pil_img, face.bbox, cpath)
    return Image.open(cpath).convert("RGB")

def main():
    random.seed(42)
    np.random.seed(42)

    out_dir = Path("report_assets_v3").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = Path("export/.cache").resolve()
    cache_crops_p = cache_dir / "crops"
    cache = EmbeddingCache(cache_dir)
    photos = cache.load_all()

    loader = ImageLoader()
    tg = ThumbnailGenerator(thumb_size=400, face_crop_size=256)

    # 1. Cluster at 0.50
    clusterer_50 = FaceClusterer(distance_threshold=0.50)
    people_50, unrec_50 = clusterer_50.cluster(photos)
    from backend.engine.thumbnails import select_representative_face
    for p in people_50:
        if p.rep_face is None:
            p.rep_face = select_representative_face(p.faces)

    # 2. Cluster at 0.60
    clusterer_60 = FaceClusterer(distance_threshold=0.60)
    people_60, _ = clusterer_60.cluster(photos)
    for p in people_60:
        if p.rep_face is None:
            p.rep_face = select_representative_face(p.faces)

    font_title = get_font(18)
    font_bold = get_font(13)
    font_regular = get_font(11)

    # -------------------------------------------------------------
    # SHEET 1: Top 10 clusters (with full filenames)
    # -------------------------------------------------------------
    print("Generating Sheet 1: Top 10 clusters...")
    top_10 = people_50[:10]
    
    # We display each cluster as a row:
    # [Rep Face] [Member 1] [Member 2] [Member 3] [Member 4] + text info
    cell_size = 140
    padding = 10
    row_h = cell_size + 45
    sheet_w = cell_size * 5 + padding * 6 + 180
    sheet_h = row_h * 10 + 60

    sheet1 = Image.new("RGB", (sheet_w, sheet_h), color=(18, 18, 20))
    draw1 = ImageDraw.Draw(sheet1)
    draw1.text((padding + 10, 15), "TOP 10 CLUSTERS (Ranked by Photo Count, Threshold 0.50)", fill=(255, 255, 255), font=font_title)

    for r_idx, person in enumerate(top_10):
        y = 55 + r_idx * row_h
        
        # Info block
        rep_photo = photos[person.rep_face.photo_id]
        draw1.text((padding, y + 10), f"Cluster: {person.id.upper()}", fill=(96, 165, 250), font=font_bold)
        draw1.text((padding, y + 32), f"Photos: {len(person.photo_ids)}", fill=(220, 220, 220), font=font_regular)
        draw1.text((padding, y + 50), f"Faces: {len(person.faces)}", fill=(180, 180, 180), font=font_regular)

        # Show representative face + up to 4 other faces from different photos
        rep_img = ensure_crop(rep_photo, person.rep_face, cache_crops_p, loader, tg).resize((cell_size, cell_size), Image.Resampling.LANCZOS)
        x_base = padding + 180
        sheet1.paste(rep_img, (x_base, y))
        draw1.text((x_base, y + cell_size + 2), f"REP: {rep_photo.file_name}", fill=(250, 204, 21), font=font_regular)
        draw1.text((x_base, y + cell_size + 16), f"score: {person.rep_face.det_score:.2f}", fill=(160, 160, 160), font=font_regular)

        # Pick distinct photos for remaining 4 member slots
        other_faces = []
        seen_pids = {person.rep_face.photo_id}
        for f in person.faces:
            if f.photo_id not in seen_pids:
                other_faces.append(f)
                seen_pids.add(f.photo_id)
            if len(other_faces) == 4:
                break
        # Fallback if fewer photos than faces
        if len(other_faces) < 4:
            for f in person.faces:
                if f.face_id != person.rep_face.face_id and f not in other_faces:
                    other_faces.append(f)
                if len(other_faces) == 4:
                    break

        for m_idx, mf in enumerate(other_faces):
            mx = x_base + (m_idx + 1) * (cell_size + padding)
            mph = photos[mf.photo_id]
            mimg = ensure_crop(mph, mf, cache_crops_p, loader, tg).resize((cell_size, cell_size), Image.Resampling.LANCZOS)
            sheet1.paste(mimg, (mx, y))
            draw1.text((mx, y + cell_size + 2), mph.file_name, fill=(220, 220, 220), font=font_regular)
            draw1.text((mx, y + cell_size + 16), f"score: {mf.det_score:.2f}", fill=(160, 160, 160), font=font_regular)

    sheet1_path = out_dir / "contact_sheet_top_10_clusters.jpg"
    sheet1.save(sheet1_path, quality=92)
    print(f"Saved: {sheet1_path}")

    # -------------------------------------------------------------
    # SHEET 2: Merge-diff 0.50 vs 0.60 (40 pairs with smallest distance)
    # -------------------------------------------------------------
    print("Generating Sheet 2: Merge-diff 0.50 vs 0.60 (40 pairs)...")
    # Identify which 0.50 clusters merged together in 0.60
    # Map face_id -> person_50 id
    face_to_p50 = {}
    for p in people_50:
        for f in p.faces:
            face_to_p50[f.face_id] = p.id

    # For each 0.60 cluster, see which 0.50 clusters it contains
    p50_dict = {p.id: p for p in people_50}
    merged_pairs = []

    for p60 in people_60:
        c50_ids = sorted(list(dict.fromkeys(face_to_p50[f.face_id] for f in p60.faces if f.face_id in face_to_p50)))
        if len(c50_ids) > 1:
            for i in range(len(c50_ids)):
                for j in range(i + 1, len(c50_ids)):
                    id_a = c50_ids[i]
                    id_b = c50_ids[j]
                    pa = p50_dict[id_a]
                    pb = p50_dict[id_b]
                    
                    # Compute average cosine distance between them
                    embs_a = np.stack([f.embedding for f in pa.faces if f.embedding is not None])
                    embs_b = np.stack([f.embedding for f in pb.faces if f.embedding is not None])
                    sim = np.dot(embs_a, embs_b.T)
                    avg_dist = float(1.0 - np.mean(sim))

                    merged_pairs.append({
                        "cluster_a": pa,
                        "cluster_b": pb,
                        "distance": avg_dist,
                    })

    # Sort by distance ascending and pick top 40
    merged_pairs.sort(key=lambda item: item["distance"])
    top_40_pairs = merged_pairs[:40]
    print(f"Found {len(merged_pairs)} total merged pairs between 0.50 and 0.60. Selecting closest 40.")

    # Grid: 4 columns of pairs, 10 rows
    cols = 4
    rows = 10
    pair_w = 340
    pair_h = 160
    sheet2_w = cols * (pair_w + padding) + padding + 10
    sheet2_h = rows * (pair_h + padding) + 70

    sheet2 = Image.new("RGB", (sheet2_w, sheet2_h), color=(18, 18, 20))
    draw2 = ImageDraw.Draw(sheet2)
    draw2.text((padding + 10, 15), "MERGE-DIFF: Threshold 0.50 vs 0.60 (Top 40 Closest Merged Cluster Pairs)", fill=(255, 255, 255), font=font_title)

    for idx, item in enumerate(top_40_pairs):
        c = idx % cols
        r = idx // cols
        px = padding + c * (pair_w + padding)
        py = 55 + r * (pair_h + padding)

        pa = item["cluster_a"]
        pb = item["cluster_b"]
        dist = item["distance"]

        # Card background
        draw2.rectangle([(px, py), (px + pair_w, py + pair_h)], fill=(28, 28, 32), outline=(50, 50, 55))

        # Face A
        ph_a = photos[pa.rep_face.photo_id]
        img_a = ensure_crop(ph_a, pa.rep_face, cache_crops_p, loader, tg).resize((90, 90), Image.Resampling.LANCZOS)
        sheet2.paste(img_a, (px + 10, py + 10))

        # Face B
        ph_b = photos[pb.rep_face.photo_id]
        img_b = ensure_crop(ph_b, pb.rep_face, cache_crops_p, loader, tg).resize((90, 90), Image.Resampling.LANCZOS)
        sheet2.paste(img_b, (px + 115, py + 10))

        # Header info
        draw2.text((px + 215, py + 10), f"Pair #{idx+1}", fill=(160, 160, 160), font=font_regular)
        draw2.text((px + 215, py + 26), f"Dist: {dist:.4f}", fill=(52, 211, 153), font=font_bold)
        draw2.text((px + 215, py + 48), f"{pa.id} ({len(pa.photo_ids)}p)", fill=(96, 165, 250), font=font_regular)
        draw2.text((px + 215, py + 64), f"{pb.id} ({len(pb.photo_ids)}p)", fill=(244, 114, 182), font=font_regular)

        # Full filenames below each face crop (no truncation)
        draw2.text((px + 10, py + 105), f"{pa.id}: {ph_a.file_name}", fill=(200, 200, 200), font=font_regular)
        draw2.text((px + 10, py + 120), f"{pb.id}: {ph_b.file_name}", fill=(200, 200, 200), font=font_regular)

    sheet2_path = out_dir / "contact_sheet_merge_diff_050_vs_060.jpg"
    sheet2.save(sheet2_path, quality=90)
    print(f"Saved: {sheet2_path}")

    # -------------------------------------------------------------
    # SHEET 3: 20 random single-photo clusters
    # -------------------------------------------------------------
    print("Generating Sheet 3: 20 random single-photo clusters...")
    single_photo_clusters = [p for p in people_50 if len(p.photo_ids) == 1]
    sampled_singles = random.sample(single_photo_clusters, min(20, len(single_photo_clusters)))

    cols3 = 5
    rows3 = 4
    cell3_w = 260
    cell3_h = 240
    sheet3_w = cols3 * (cell3_w + padding) + padding
    sheet3_h = rows3 * (cell3_h + padding) + 60

    sheet3 = Image.new("RGB", (sheet3_w, sheet3_h), color=(18, 18, 20))
    draw3 = ImageDraw.Draw(sheet3)
    draw3.text((padding + 10, 15), "20 RANDOM SINGLE-PHOTO CLUSTERS (Threshold 0.50)", fill=(255, 255, 255), font=font_title)

    for idx, person in enumerate(sampled_singles):
        c = idx % cols3
        r = idx // cols3
        x = padding + c * (cell3_w + padding)
        y = 55 + r * (cell3_h + padding)

        draw3.rectangle([(x, y), (x + cell3_w, y + cell3_h)], fill=(28, 28, 32), outline=(50, 50, 55))

        ph = photos[person.rep_face.photo_id]
        img = ensure_crop(ph, person.rep_face, cache_crops_p, loader, tg).resize((150, 150), Image.Resampling.LANCZOS)
        sheet3.paste(img, (x + (cell3_w - 150) // 2, y + 10))

        draw3.text((x + 12, y + 168), f"Cluster: {person.id.upper()}", fill=(96, 165, 250), font=font_bold)
        draw3.text((x + 12, y + 186), f"File: {ph.file_name}", fill=(220, 220, 220), font=font_regular)
        draw3.text((x + 12, y + 204), f"Det Score: {person.rep_face.det_score:.2f}", fill=(160, 160, 160), font=font_regular)

    sheet3_path = out_dir / "contact_sheet_20_single_photo_clusters.jpg"
    sheet3.save(sheet3_path, quality=90)
    print(f"Saved: {sheet3_path}")

    # -------------------------------------------------------------
    # SHEET 4: 20 Unrecognized faces, including extreme_pose ones
    # -------------------------------------------------------------
    print("Generating Sheet 4: 20 Unrecognized faces...")
    # Gather all unrecognized faces from the dataset
    all_unrec_faces = []
    for ph in photos.values():
        for f in ph.faces:
            if not f.is_good_quality:
                all_unrec_faces.append((ph, f))

    extreme_pose_faces = [(ph, f) for ph, f in all_unrec_faces if f.rejection_reason == "extreme_pose"]
    small_faces = [(ph, f) for ph, f in all_unrec_faces if "face_too_small" in (f.rejection_reason or "")]

    # Pick 10 extreme_pose + 10 small_faces
    sample_extreme = random.sample(extreme_pose_faces, min(10, len(extreme_pose_faces)))
    sample_small = random.sample(small_faces, min(10, len(small_faces)))
    sampled_unrec = sample_extreme + sample_small

    cols4 = 5
    rows4 = 4
    cell4_w = 260
    cell4_h = 240
    sheet4_w = cols4 * (cell4_w + padding) + padding
    sheet4_h = rows4 * (cell4_h + padding) + 60

    sheet4 = Image.new("RGB", (sheet4_w, sheet4_h), color=(18, 18, 20))
    draw4 = ImageDraw.Draw(sheet4)
    draw4.text((padding + 10, 15), "20 UNRECOGNIZED FACES (10 Extreme Pose + 10 Too Small)", fill=(255, 255, 255), font=font_title)

    for idx, (ph, f) in enumerate(sampled_unrec):
        c = idx % cols4
        r = idx // cols4
        x = padding + c * (cell4_w + padding)
        y = 55 + r * (cell4_h + padding)

        draw4.rectangle([(x, y), (x + cell4_w, y + cell4_h)], fill=(28, 28, 32), outline=(50, 50, 55))

        img = ensure_crop(ph, f, cache_crops_p, loader, tg).resize((150, 150), Image.Resampling.LANCZOS)
        sheet4.paste(img, (x + (cell4_w - 150) // 2, y + 10))

        yaw_str = f", yaw: {abs(f.pose[1]):.1f}°" if f.pose and len(f.pose) >= 2 else ""
        draw4.text((x + 10, y + 168), f"Reason: {f.rejection_reason}{yaw_str}", fill=(248, 113, 113), font=font_bold)
        draw4.text((x + 10, y + 188), f"File: {ph.file_name}", fill=(220, 220, 220), font=font_regular)
        draw4.text((x + 10, y + 206), f"Score: {f.det_score:.2f}", fill=(160, 160, 160), font=font_regular)

    sheet4_path = out_dir / "contact_sheet_20_unrecognized_faces.jpg"
    sheet4.save(sheet4_path, quality=90)
    print(f"Saved: {sheet4_path}")

if __name__ == "__main__":
    main()
