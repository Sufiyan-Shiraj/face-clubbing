"""Generates Evidence Sheets for report_assets_v4/:
1. Merge pairs binned by distance (0.50-0.52, 0.52-0.55, 0.55-0.58, 0.58-0.60; 10 random pairs per bin)
2. Top 10 clusters: 8 members farthest from centroid (worst-fitting faces)
3. Pairs #13, #24, #32, #19 enlarged: 4 faces from each side
All with full filenames (no truncation).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
from backend.engine.thumbnails import ThumbnailGenerator, select_representative_face
from backend.engine.loader import ImageLoader


def get_font(size=14, bold=False):
    font_name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            fb = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            return ImageFont.truetype(fb, size)
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

    out_dir = Path("report_assets_v4").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = Path("export/.cache").resolve()
    cache_crops_p = cache_dir / "crops"
    cache = EmbeddingCache(cache_dir)
    photos = cache.load_all()

    loader = ImageLoader()
    tg = ThumbnailGenerator(thumb_size=400, face_crop_size=256)

    # 1. Run Clusterer with seed + attach-only model
    clusterer = FaceClusterer(
        distance_threshold=0.50,
        seed_min_face_size=64,
        seed_max_yaw=60.0,
        seed_min_det_score=0.70,
    )
    people, unrecognized = clusterer.cluster(photos)

    for p in people:
        if p.rep_face is None:
            p.rep_face = select_representative_face(p.faces)

    cluster_by_id = {p.id: p for p in people}

    font_title = get_font(20, bold=True)
    font_subtitle = get_font(14, bold=True)
    font_bold = get_font(12, bold=True)
    font_regular = get_font(11, bold=False)
    font_small = get_font(10, bold=False)

    # =============================================================
    # SHEET 1: Merge pairs binned by distance (10 per bin, 4 bins)
    # =============================================================
    print("\n--- Generating Sheet 1: Binned Merge Pairs ---")
    suggs_path = cache_dir / "suggestions.json"
    if suggs_path.exists():
        with open(suggs_path, "r", encoding="utf-8") as f:
            sugg_data = json.load(f)
        suggestions = sugg_data.get("suggestions", [])
    else:
        suggestions = clusterer.compute_suggested_merges(people, min_dist=0.50, max_dist=0.62)

    bin_defs = [
        ("0.50-0.52", 0.50, 0.52),
        ("0.52-0.55", 0.52, 0.55),
        ("0.55-0.58", 0.55, 0.58),
        ("0.58-0.60", 0.58, 0.60),
    ]

    sampled_pairs_by_bin = {}
    for bname, low, high in bin_defs:
        matches = [s for s in suggestions if low <= s["distance"] < high]
        print(f"Bin {bname}: found {len(matches)} pairs")
        sampled = random.sample(matches, min(10, len(matches)))
        sampled_pairs_by_bin[bname] = sampled

    # Render Sheet 1: 4 columns (one per bin), 10 rows
    # Card width: 340px, Card height: 160px
    card_w = 350
    card_h = 165
    pad = 16
    sheet1_w = pad + 4 * (card_w + pad)
    sheet1_h = 75 + 10 * (card_h + pad)

    sheet1 = Image.new("RGB", (sheet1_w, sheet1_h), color=(15, 15, 18))
    draw1 = ImageDraw.Draw(sheet1)

    draw1.text((pad, 15), "MERGE PAIRS BINNED BY DISTANCE (10 Random Pairs per Bin)", fill=(255, 255, 255), font=font_title)
    draw1.text((pad, 42), "Evaluating candidate merges across distance bands (Threshold 0.50 -> 0.60)", fill=(160, 160, 160), font=font_regular)

    for col_idx, (bname, _, _) in enumerate(bin_defs):
        bin_pairs = sampled_pairs_by_bin[bname]
        col_x = pad + col_idx * (card_w + pad)

        for row_idx, item in enumerate(bin_pairs):
            row_y = 75 + row_idx * (card_h + pad)

            # Card background
            draw1.rectangle([(col_x, row_y), (col_x + card_w, row_y + card_h)], fill=(24, 24, 28), outline=(48, 48, 54))

            pa = cluster_by_id.get(item["cluster_a"])
            pb = cluster_by_id.get(item["cluster_b"])
            dist = item["distance"]

            if pa and pb:
                ph_a = photos[pa.rep_face.photo_id]
                ph_b = photos[pb.rep_face.photo_id]

                img_a = ensure_crop(ph_a, pa.rep_face, cache_crops_p, loader, tg).resize((90, 90), Image.Resampling.LANCZOS)
                img_b = ensure_crop(ph_b, pb.rep_face, cache_crops_p, loader, tg).resize((90, 90), Image.Resampling.LANCZOS)

                sheet1.paste(img_a, (col_x + 10, row_y + 10))
                sheet1.paste(img_b, (col_x + 110, row_y + 10))

                draw1.text((col_x + 210, row_y + 10), f"Bin: {bname}", fill=(245, 158, 11), font=font_bold)
                draw1.text((col_x + 210, row_y + 26), f"Pair #{row_idx+1}", fill=(160, 160, 160), font=font_regular)
                draw1.text((col_x + 210, row_y + 44), f"Dist: {dist:.4f}", fill=(52, 211, 153), font=font_bold)
                draw1.text((col_x + 210, row_y + 64), f"{pa.id} ({len(pa.photo_ids)}p)", fill=(96, 165, 250), font=font_regular)
                draw1.text((col_x + 210, row_y + 80), f"{pb.id} ({len(pb.photo_ids)}p)", fill=(244, 114, 182), font=font_regular)

                # Full filenames below (no truncation)
                draw1.text((col_x + 10, row_y + 108), f"A: {ph_a.file_name}", fill=(210, 210, 210), font=font_small)
                draw1.text((col_x + 10, row_y + 124), f"B: {ph_b.file_name}", fill=(210, 210, 210), font=font_small)

    sheet1_path = out_dir / "contact_sheet_merge_bins.jpg"
    sheet1.save(sheet1_path, quality=90)
    print(f"Saved: {sheet1_path}")

    # =============================================================
    # SHEET 2: Top 10 clusters: 8 members farthest from centroid
    # =============================================================
    print("\n--- Generating Sheet 2: Top 10 Clusters Worst-Fitting Members ---")
    top_10 = people[:10]

    # Grid: 10 rows (clusters), 8 face crops per row + left label column
    label_col_w = 200
    face_card_w = 150
    face_card_h = 195
    row_pad = 12
    col_pad = 10
    sheet2_w = pad + label_col_w + 8 * (face_card_w + col_pad) + pad
    sheet2_h = 75 + 10 * (face_card_h + row_pad) + pad

    sheet2 = Image.new("RGB", (sheet2_w, sheet2_h), color=(15, 15, 18))
    draw2 = ImageDraw.Draw(sheet2)

    draw2.text((pad, 15), "TOP 10 CLUSTERS: 8 WORST-FITTING MEMBERS (Farthest from Cluster Centroid)", fill=(255, 255, 255), font=font_title)
    draw2.text((pad, 42), "Faces with the highest cosine distance to their cluster centroid vector", fill=(160, 160, 160), font=font_regular)

    for row_idx, person in enumerate(top_10):
        row_y = 75 + row_idx * (face_card_h + row_pad)

        # 1. Compute cluster centroid
        embs = np.stack([f.embedding for f in person.faces])
        mean_vec = np.mean(embs, axis=0)
        norm = np.linalg.norm(mean_vec)
        centroid = mean_vec / norm if norm > 1e-8 else mean_vec

        # Cosine distance to centroid
        dots = np.dot(embs, centroid)
        dists = 1.0 - dots

        face_dist_pairs = list(zip(person.faces, dists))
        # Sort descending by distance (worst-fitting first)
        face_dist_pairs.sort(key=lambda x: x[1], reverse=True)

        farthest_8 = face_dist_pairs[:8]

        # Draw left label block
        draw2.rectangle([(pad, row_y), (pad + label_col_w - 10, row_y + face_card_h)], fill=(24, 24, 28), outline=(48, 48, 54))
        draw2.text((pad + 12, row_y + 15), f"Cluster: {person.id.upper()}", fill=(96, 165, 250), font=font_subtitle)
        draw2.text((pad + 12, row_y + 38), f"Photos: {len(person.photo_ids)}", fill=(255, 255, 255), font=font_bold)
        draw2.text((pad + 12, row_y + 56), f"Total faces: {len(person.faces)}", fill=(200, 200, 200), font=font_regular)
        draw2.text((pad + 12, row_y + 80), "Centroid Distance Range:", fill=(160, 160, 160), font=font_small)
        draw2.text((pad + 12, row_y + 96), f"Max dist: {farthest_8[0][1]:.4f}", fill=(248, 113, 113), font=font_bold)
        draw2.text((pad + 12, row_y + 114), f"Min dist: {face_dist_pairs[-1][1]:.4f}", fill=(52, 211, 153), font=font_small)
        draw2.text((pad + 12, row_y + 135), f"Showing {len(farthest_8)} worst-fit", fill=(245, 158, 11), font=font_small)

        # Draw 8 face crops
        for col_idx, (face, fdist) in enumerate(farthest_8):
            fc_x = pad + label_col_w + col_idx * (face_card_w + col_pad)
            ph = photos[face.photo_id]

            draw2.rectangle([(fc_x, row_y), (fc_x + face_card_w, row_y + face_card_h)], fill=(24, 24, 28), outline=(48, 48, 54))

            crop_img = ensure_crop(ph, face, cache_crops_p, loader, tg).resize((130, 130), Image.Resampling.LANCZOS)
            sheet2.paste(crop_img, (fc_x + 10, row_y + 10))

            draw2.text((fc_x + 10, row_y + 144), f"Dist: {fdist:.4f}", fill=(248, 113, 113), font=font_bold)
            draw2.text((fc_x + 85, row_y + 145), f"Sc: {face.det_score:.2f}", fill=(160, 160, 160), font=font_small)
            draw2.text((fc_x + 10, row_y + 162), ph.file_name, fill=(210, 210, 210), font=font_small)

    sheet2_path = out_dir / "contact_sheet_top10_worst_fitting.jpg"
    sheet2.save(sheet2_path, quality=90)
    print(f"Saved: {sheet2_path}")

    # =============================================================
    # SHEET 3: Pairs #13, #24, #32, #19 enlarged: 4 faces from each side
    # =============================================================
    print("\n--- Generating Sheet 3: Enlarged Questionable Merge Pairs (#13, #24, #32, #19) ---")

    # From previous merge sheet (report_assets_v3/contact_sheet_merge_diff_050_vs_060.jpg):
    # Pair #13 (Dist: 0.5068): p001 (IMG_2415.HEIC) vs p132 (IMG_2179.HEIC)
    # Pair #19 (Dist: 0.5106): p174 (IMG_6749.JPG) vs p305 (IMG_2165.JPG)
    # Pair #24 (Dist: 0.5123): p001 (IMG_2415.HEIC) vs p323 (IMG_2417.HEIC)
    # Pair #32 (Dist: 0.5159): p001 (IMG_2415.HEIC) vs p133 (IMG_2401.HEIC)

    # Let's map representative files to their current clusters
    def find_cluster_for_file(fn):
        for p in people:
            for f in p.faces:
                if photos[f.photo_id].file_name == fn:
                    return p
        return None

    target_pairs_info = [
        {"pair_num": 13, "dist": 0.5068, "side_a_fn": "IMG_2415.HEIC", "side_b_fn": "IMG_2179.HEIC"},
        {"pair_num": 19, "dist": 0.5106, "side_a_fn": "IMG_6749.JPG", "side_b_fn": "IMG_2165.JPG"},
        {"pair_num": 24, "dist": 0.5123, "side_a_fn": "IMG_2415.HEIC", "side_b_fn": "IMG_2417.HEIC"},
        {"pair_num": 32, "dist": 0.5159, "side_a_fn": "IMG_2415.HEIC", "side_b_fn": "IMG_2401.HEIC"},
    ]

    # Grid: 4 rows (1 per pair).
    # Each row: Title header, Left side: 4 crops (150x150), Center divider "VS", Right side: 4 crops (150x150)
    crop_size = 150
    crop_card_w = 165
    crop_card_h = 210
    row_h = 270
    sheet3_w = pad + 4 * crop_card_w + 100 + 4 * crop_card_w + pad
    sheet3_h = 80 + 4 * (row_h + pad)

    sheet3 = Image.new("RGB", (sheet3_w, sheet3_h), color=(15, 15, 18))
    draw3 = ImageDraw.Draw(sheet3)

    draw3.text((pad, 15), "ENLARGED INSPECTION: PAIRS #13, #19, #24, #32 (False Merge Candidates)", fill=(255, 255, 255), font=font_title)
    draw3.text((pad, 42), "4 representative face crops per side to judge facial features across candidates", fill=(160, 160, 160), font=font_regular)

    for row_idx, pinfo in enumerate(target_pairs_info):
        row_y = 80 + row_idx * (row_h + pad)
        pnum = pinfo["pair_num"]
        pdist = pinfo["dist"]
        ca = find_cluster_for_file(pinfo["side_a_fn"])
        cb = find_cluster_for_file(pinfo["side_b_fn"])

        # Row container
        draw3.rectangle([(pad, row_y), (sheet3_w - pad, row_y + row_h)], fill=(22, 22, 26), outline=(44, 44, 50))

        # Header inside row
        header_text = f"PAIR #{pnum} | Cosine Distance: {pdist:.4f} | Left: {pinfo['side_a_fn']} vs Right: {pinfo['side_b_fn']}"
        draw3.text((pad + 16, row_y + 12), header_text, fill=(245, 158, 11), font=font_subtitle)

        # Side A faces (pick up to 4 distinct photos if possible)
        faces_a = []
        if ca:
            # Pick representative face first
            faces_a.append(ca.rep_face)
            seen_pids = {ca.rep_face.photo_id}
            for f in ca.faces:
                if len(faces_a) >= 4:
                    break
                if f.photo_id not in seen_pids:
                    faces_a.append(f)
                    seen_pids.add(f.photo_id)
            # If still < 4, pad with any faces
            for f in ca.faces:
                if len(faces_a) >= 4:
                    break
                if f not in faces_a:
                    faces_a.append(f)

        # Draw Side A crops
        start_xa = pad + 16
        for cidx, face in enumerate(faces_a):
            cx = start_xa + cidx * crop_card_w
            cy = row_y + 45
            ph = photos[face.photo_id]

            draw3.rectangle([(cx, cy), (cx + crop_size, cy + crop_card_h)], fill=(28, 28, 32), outline=(50, 50, 56))
            cimg = ensure_crop(ph, face, cache_crops_p, loader, tg).resize((crop_size, crop_size), Image.Resampling.LANCZOS)
            sheet3.paste(cimg, (cx, cy))

            draw3.text((cx + 4, cy + crop_size + 6), f"Side A [{ca.id if ca else 'N/A'}]", fill=(96, 165, 250), font=font_bold)
            draw3.text((cx + 4, cy + crop_size + 22), ph.file_name, fill=(210, 210, 210), font=font_small)
            draw3.text((cx + 4, cy + crop_size + 38), f"Score: {face.det_score:.2f}", fill=(160, 160, 160), font=font_small)

        # VS divider
        vs_x = start_xa + 4 * crop_card_w + 15
        draw3.text((vs_x + 10, row_y + 110), "VS", fill=(248, 113, 113), font=font_title)
        draw3.text((vs_x - 5, row_y + 140), f"d={pdist:.4f}", fill=(52, 211, 153), font=font_bold)

        # Side B faces
        faces_b = []
        if cb:
            faces_b.append(cb.rep_face)
            seen_pids_b = {cb.rep_face.photo_id}
            for f in cb.faces:
                if len(faces_b) >= 4:
                    break
                if f.photo_id not in seen_pids_b:
                    faces_b.append(f)
                    seen_pids_b.add(f.photo_id)
            for f in cb.faces:
                if len(faces_b) >= 4:
                    break
                if f not in faces_b:
                    faces_b.append(f)

        # Draw Side B crops
        start_xb = vs_x + 75
        for cidx, face in enumerate(faces_b):
            cx = start_xb + cidx * crop_card_w
            cy = row_y + 45
            ph = photos[face.photo_id]

            draw3.rectangle([(cx, cy), (cx + crop_size, cy + crop_card_h)], fill=(28, 28, 32), outline=(50, 50, 56))
            cimg = ensure_crop(ph, face, cache_crops_p, loader, tg).resize((crop_size, crop_size), Image.Resampling.LANCZOS)
            sheet3.paste(cimg, (cx, cy))

            draw3.text((cx + 4, cy + crop_size + 6), f"Side B [{cb.id if cb else 'N/A'}]", fill=(244, 114, 182), font=font_bold)
            draw3.text((cx + 4, cy + crop_size + 22), ph.file_name, fill=(210, 210, 210), font=font_small)
            draw3.text((cx + 4, cy + crop_size + 38), f"Score: {face.det_score:.2f}", fill=(160, 160, 160), font=font_small)

    sheet3_path = out_dir / "contact_sheet_enlarged_pairs_13_24_32_19.jpg"
    sheet3.save(sheet3_path, quality=90)
    print(f"Saved: {sheet3_path}")


if __name__ == "__main__":
    main()
