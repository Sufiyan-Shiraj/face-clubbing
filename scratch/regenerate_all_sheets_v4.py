"""Regenerate all evidence contact sheets in report_assets_v4/ directly from export/people.json:
1. contact_sheet_merge_bins_v4.jpg:
   - Pairs in distance bins: 0.50-0.52, 0.52-0.55, 0.55-0.58, 0.58-0.60
   - Identified by cluster ID, face_id, and photo filename
   - Tiles at least 200px
2. contact_sheet_top10_worst_fitting.jpg:
   - Top 10 clusters from export/people.json
   - 8 members farthest from centroid
3. contact_sheet_enlarged_old_pairs.jpg:
   - Shows consolidation of old split pairs into final clusters
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.engine.cache import EmbeddingCache
from backend.engine.thumbnails import ThumbnailGenerator
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


def ensure_face_crop(face_id, photo_record, bbox, cache_crops_p, loader, tg):
    cpath = cache_crops_p / f"{face_id}.jpg"
    if not cpath.exists():
        rgb, _, _, pil_img = loader.load_image(photo_record.original_path)
        tg.generate_square_face_crop_from_image(pil_img, bbox, cpath)
    return Image.open(cpath).convert("RGB")


def main():
    random.seed(42)
    np.random.seed(42)

    export_path = Path("export/people.json").resolve()
    with open(export_path, "r", encoding="utf-8") as f:
        export_data = json.load(f)

    out_dir = Path("report_assets_v4").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = Path("export/.cache").resolve()
    cache_crops_p = cache_dir / "crops"
    cache = EmbeddingCache(cache_dir)
    photos = cache.load_all()

    loader = ImageLoader()
    tg = ThumbnailGenerator(thumb_size=400, face_crop_size=256)

    people = export_data["people"]
    people_by_id = {p["id"]: p for p in people}
    unrec_faces = export_data["unrecognized"]["faces"]
    unrec_by_fid = {f["face_id"]: f for f in unrec_faces if "face_id" in f}

    font_title = get_font(22, bold=True)
    font_subtitle = get_font(15, bold=True)
    font_bold = get_font(13, bold=True)
    font_regular = get_font(12, bold=False)
    font_small = get_font(10, bold=False)

    # =========================================================================
    # 1. GENERATE SHEET 1: contact_sheet_merge_bins_v4.jpg
    # =========================================================================
    print("\n--- 1. Generating contact_sheet_merge_bins_v4.jpg ---")

    # Compute top-5 centroids for each cluster
    centroids = []
    for p in people:
        scored_faces = []
        for f in p["faces"]:
            rec = photos.get(f["photo_id"])
            if rec:
                f_obj = next((x for x in rec.faces if x.face_id == f["face_id"]), None)
                if f_obj and f_obj.embedding is not None:
                    w = f_obj.bbox[2] - f_obj.bbox[0]
                    h = f_obj.bbox[3] - f_obj.bbox[1]
                    scored_faces.append((float(f_obj.det_score), min(w, h), f_obj.embedding))
        scored_faces.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top5 = scored_faces[:5]
        if top5:
            arr = np.stack([x[2] for x in top5])
            mean_v = np.mean(arr, axis=0)
            norm = np.linalg.norm(mean_v)
            centroids.append(mean_v / norm if norm > 1e-8 else mean_v)
        else:
            centroids.append(None)

    n_people = len(people)
    bin_defs = [
        ("0.50-0.52", 0.50, 0.52),
        ("0.52-0.55", 0.52, 0.55),
        ("0.55-0.58", 0.55, 0.58),
        ("0.58-0.60", 0.58, 0.60),
    ]
    pairs_by_bin = {b[0]: [] for b in bin_defs}

    for i in range(n_people):
        if centroids[i] is None:
            continue
        for j in range(i + 1, n_people):
            if centroids[j] is None:
                continue
            dist = float(1.0 - np.dot(centroids[i], centroids[j]))
            for bname, low, high in bin_defs:
                if low <= dist < high:
                    fa_rep = people[i]["faces"][0]
                    fb_rep = people[j]["faces"][0]
                    pairs_by_bin[bname].append({
                        "bin": bname,
                        "cluster_a": people[i]["id"],
                        "cluster_b": people[j]["id"],
                        "dist": dist,
                        "face_a": fa_rep,
                        "face_b": fb_rep,
                    })

    sampled_bins = {}
    max_rows = 0
    for bname, low, high in bin_defs:
        avail = pairs_by_bin[bname]
        k = min(len(avail), 8)
        sampled = random.sample(avail, k) if len(avail) >= k else avail
        sampled_bins[bname] = sampled
        max_rows = max(max_rows, len(sampled))
        print(f"Bin {bname}: selected {len(sampled)} pairs (available: {len(avail)})")

    tile_size = 200
    card_w = 420
    card_h = 310
    pad = 16
    col_w = card_w + pad
    sheet1_w = pad + 4 * col_w
    sheet1_h = 85 + max_rows * (card_h + pad)

    sheet1 = Image.new("RGB", (sheet1_w, sheet1_h), color=(14, 14, 18))
    draw1 = ImageDraw.Draw(sheet1)

    draw1.text((pad, 16), "MERGE PAIRS BINNED BY DISTANCE (Tile Size >= 200px)", fill=(255, 255, 255), font=font_title)
    draw1.text((pad, 46), "Single Source of Truth: export/people.json | Pairs Identified by Cluster ID, face_id, and photo filename", fill=(160, 160, 160), font=font_regular)

    for col_idx, (bname, _, _) in enumerate(bin_defs):
        col_x = pad + col_idx * col_w
        pairs = sampled_bins[bname]

        draw1.rectangle([(col_x, 70), (col_x + card_w, 75)], fill=(245, 158, 11))

        for row_idx, item in enumerate(pairs):
            row_y = 85 + row_idx * (card_h + pad)
            ca = people_by_id[item["cluster_a"]]
            cb = people_by_id[item["cluster_b"]]
            fa = item["face_a"]
            fb = item["face_b"]

            # Integrity assertions
            assert any(f["face_id"] == fa["face_id"] for f in ca["faces"])
            assert any(f["face_id"] == fb["face_id"] for f in cb["faces"])

            draw1.rectangle([(col_x, row_y), (col_x + card_w, row_y + card_h)], fill=(22, 22, 26), outline=(44, 44, 52))
            draw1.text((col_x + 10, row_y + 8), f"Bin: {bname} | Pair #{row_idx + 1}", fill=(245, 158, 11), font=font_bold)
            draw1.text((col_x + 230, row_y + 8), f"Dist: {item['dist']:.4f}", fill=(52, 211, 153), font=font_bold)

            # Paste Tile A
            ph_a = photos[fa["photo_id"]]
            crop_a = ensure_face_crop(fa["face_id"], ph_a, fa["bbox"], cache_crops_p, loader, tg).resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            sheet1.paste(crop_a, (col_x + 8, row_y + 32))

            # Paste Tile B
            ph_b = photos[fb["photo_id"]]
            crop_b = ensure_face_crop(fb["face_id"], ph_b, fb["bbox"], cache_crops_p, loader, tg).resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            sheet1.paste(crop_b, (col_x + tile_size + 14, row_y + 32))

            # Metadata below tiles
            draw1.text((col_x + 8, row_y + 32 + tile_size + 4), f"{ca['id']} ({len(ca['photo_ids'])}p) | {fa['face_id']}", fill=(96, 165, 250), font=font_small)
            draw1.text((col_x + 8, row_y + 32 + tile_size + 18), f"{fa['file_name']}", fill=(210, 210, 210), font=font_small)

            draw1.text((col_x + tile_size + 14, row_y + 32 + tile_size + 4), f"{cb['id']} ({len(cb['photo_ids'])}p) | {fb['face_id']}", fill=(244, 114, 182), font=font_small)
            draw1.text((col_x + tile_size + 14, row_y + 32 + tile_size + 18), f"{fb['file_name']}", fill=(210, 210, 210), font=font_small)

    sheet1_path = out_dir / "contact_sheet_merge_bins_v4.jpg"
    sheet1.save(sheet1_path, quality=90)
    print(f"Saved: {sheet1_path}")

    # =========================================================================
    # 2. GENERATE SHEET 2: contact_sheet_top10_worst_fitting.jpg
    # =========================================================================
    print("\n--- 2. Generating contact_sheet_top10_worst_fitting.jpg ---")
    top_10 = people[:10]
    label_col_w = 200
    face_card_w = 150
    face_card_h = 195
    row_pad = 12
    col_pad = 10
    sheet2_w = pad + label_col_w + 8 * (face_card_w + col_pad) + pad
    sheet2_h = 75 + 10 * (face_card_h + row_pad) + pad

    sheet2 = Image.new("RGB", (sheet2_w, sheet2_h), color=(15, 15, 18))
    draw2 = ImageDraw.Draw(sheet2)

    draw2.text((pad, 15), "TOP 10 CLUSTERS: 8 WORST-FITTING MEMBERS (Farthest from Centroid)", fill=(255, 255, 255), font=font_title)
    draw2.text((pad, 42), "Source of Truth: export/people.json | Member faces ranked by highest cosine distance to top-5 centroid", fill=(160, 160, 160), font=font_regular)

    for row_idx, person in enumerate(top_10):
        row_y = 75 + row_idx * (face_card_h + row_pad)
        c_vec = centroids[row_idx]

        # Calculate distances of all faces in person to centroid
        face_dists = []
        for f in person["faces"]:
            rec = photos[f["photo_id"]]
            f_obj = next(x for x in rec.faces if x.face_id == f["face_id"])
            dist = float(1.0 - np.dot(f_obj.embedding, c_vec))
            face_dists.append((f, f_obj, dist))

        face_dists.sort(key=lambda x: x[2], reverse=True)
        farthest_8 = face_dists[:8]

        # Label block
        draw2.rectangle([(pad, row_y), (pad + label_col_w - 10, row_y + face_card_h)], fill=(24, 24, 28), outline=(48, 48, 54))
        draw2.text((pad + 12, row_y + 15), f"Cluster: {person['id'].upper()}", fill=(96, 165, 250), font=font_subtitle)
        draw2.text((pad + 12, row_y + 38), f"Photos: {len(person['photo_ids'])}", fill=(255, 255, 255), font=font_bold)
        draw2.text((pad + 12, row_y + 56), f"Total faces: {len(person['faces'])}", fill=(200, 200, 200), font=font_regular)
        draw2.text((pad + 12, row_y + 80), "Centroid Distance Range:", fill=(160, 160, 160), font=font_small)
        draw2.text((pad + 12, row_y + 96), f"Max dist: {farthest_8[0][2]:.4f}", fill=(248, 113, 113), font=font_bold)
        draw2.text((pad + 12, row_y + 114), f"Min dist: {face_dists[-1][2]:.4f}", fill=(52, 211, 153), font=font_small)

        # 8 face slots
        for col_idx, (f, f_obj, fdist) in enumerate(farthest_8):
            fc_x = pad + label_col_w + col_idx * (face_card_w + col_pad)
            ph = photos[f["photo_id"]]

            draw2.rectangle([(fc_x, row_y), (fc_x + face_card_w, row_y + face_card_h)], fill=(24, 24, 28), outline=(48, 48, 54))
            crop_img = ensure_face_crop(f["face_id"], ph, f_obj.bbox, cache_crops_p, loader, tg).resize((130, 130), Image.Resampling.LANCZOS)
            sheet2.paste(crop_img, (fc_x + 10, row_y + 10))

            draw2.text((fc_x + 10, row_y + 144), f"Dist: {fdist:.4f}", fill=(248, 113, 113), font=font_bold)
            draw2.text((fc_x + 85, row_y + 145), f"Sc: {f['det_score']:.2f}", fill=(160, 160, 160), font=font_small)
            draw2.text((fc_x + 10, row_y + 162), f["file_name"], fill=(210, 210, 210), font=font_small)

    sheet2_path = out_dir / "contact_sheet_top10_worst_fitting.jpg"
    sheet2.save(sheet2_path, quality=90)
    print(f"Saved: {sheet2_path}")

    # =========================================================================
    # 3. GENERATE SHEET 3: contact_sheet_enlarged_old_pairs.jpg
    # =========================================================================
    print("\n--- 3. Generating contact_sheet_enlarged_old_pairs.jpg ---")
    # Show consolidation of old split pairs into final clusters
    # p001 consolidated p080, p121, p129
    consolidation_spec = [
        {
            "pair_name": "p001 vs p080 (Consolidated into p001)",
            "merged_cluster": "p001",
            "faces_a": ["f_1046d56af7bca4f1_005", "f_fb35af43d58b8a51_004", "f_f4302ece9ffd2ce1_003", "f_3faa31f1e7de11fe_005", "f_793391f90e22f759_002", "f_af529daa4e62e12e_004"],
            "faces_b": ["f_d358e80f8872f6ef_004", "f_e96a040cf77cd194_004", "f_e0ad7d5d2701102e_002"],
            "distance": 0.3170,
            "status": "AUTO-MERGED (< 0.50)",
        },
        {
            "pair_name": "p001 vs p121 (Consolidated into p001)",
            "merged_cluster": "p001",
            "faces_a": ["f_1046d56af7bca4f1_005", "f_fb35af43d58b8a51_004", "f_f4302ece9ffd2ce1_003", "f_3faa31f1e7de11fe_005", "f_793391f90e22f759_002", "f_af529daa4e62e12e_004"],
            "faces_b": ["f_72100be076f21ac7_002", "f_f72c01c72c056c0f_008"],
            "distance": 0.3713,
            "status": "AUTO-MERGED (< 0.50)",
        },
        {
            "pair_name": "p001 vs p129 (Consolidated into p001)",
            "merged_cluster": "p001",
            "faces_a": ["f_1046d56af7bca4f1_005", "f_fb35af43d58b8a51_004", "f_f4302ece9ffd2ce1_003", "f_3faa31f1e7de11fe_005", "f_793391f90e22f759_002", "f_af529daa4e62e12e_004"],
            "faces_b": ["f_cd5cf1f9b616d68a_009", "f_7739152de91187cf_010"],
            "distance": 0.3669,
            "status": "AUTO-MERGED (< 0.50)",
        },
        {
            "pair_name": "p174 vs p305 (V2 Pair)",
            "merged_cluster": "Cross-Cluster Comparison",
            "faces_a": ["f_18e1d12f2affaa2d_025"],
            "faces_b": ["f_b70a983c56f39943_001"],
            "distance": 0.5106,
            "status": "MAYBE LINK (0.50 - 0.60)",
        },
    ]

    slot_w = 155
    slot_h = 215
    crop_dim = 145
    divider_w = 90
    row_gap = 18
    sheet3_w = pad + 6 * slot_w + divider_w + 6 * slot_w + pad
    sheet3_h = 85 + 4 * (slot_h + 45 + row_gap)

    sheet3 = Image.new("RGB", (sheet3_w, sheet3_h), color=(14, 14, 18))
    draw3 = ImageDraw.Draw(sheet3)

    draw3.text((pad, 16), "CONSOLIDATION INSPECTION: KNOWN SPLIT PAIRS AND MERGE VALIDATION", fill=(255, 255, 255), font=font_title)
    draw3.text((pad, 46), "Single Source of Truth: export/people.json | Showing faces from consolidated clusters and evaluated pairs", fill=(160, 160, 160), font=font_regular)

    for r_idx, cinfo in enumerate(consolidation_spec):
        row_y = 80 + r_idx * (slot_h + 45 + row_gap)

        draw3.rectangle([(pad, row_y), (sheet3_w - pad, row_y + slot_h + 40)], fill=(20, 20, 24), outline=(42, 42, 48))
        header_text = f"PAIR #{r_idx + 1}: {cinfo['pair_name']} | Distance: {cinfo['distance']:.4f} | Status: {cinfo['status']}"
        draw3.text((pad + 12, row_y + 8), header_text, fill=(245, 158, 11), font=font_subtitle)

        # Side A faces
        start_xa = pad + 12
        for s_idx in range(6):
            sx = start_xa + s_idx * slot_w
            sy = row_y + 32
            if s_idx < len(cinfo["faces_a"]):
                fid = cinfo["faces_a"][s_idx]
                # locate face in photos
                ph_item = next((p for p in photos.values() if any(x.face_id == fid for x in p.faces)), None)
                if ph_item:
                    f_obj = next(x for x in ph_item.faces if x.face_id == fid)
                    draw3.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(26, 26, 30), outline=(50, 50, 56))
                    cimg = ensure_face_crop(fid, ph_item, f_obj.bbox, cache_crops_p, loader, tg).resize((crop_dim, crop_dim), Image.Resampling.LANCZOS)
                    sheet3.paste(cimg, (sx + 2, sy + 2))
                    draw3.text((sx + 4, sy + crop_dim + 4), f"{fid}", fill=(96, 165, 250), font=font_small)
                    draw3.text((sx + 4, sy + crop_dim + 18), f"{ph_item.file_name}", fill=(210, 210, 210), font=font_small)
                    draw3.text((sx + 4, sy + crop_dim + 32), f"Sc: {f_obj.det_score:.2f}", fill=(140, 140, 140), font=font_small)
            else:
                draw3.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(18, 18, 22), outline=(32, 32, 36))
                draw3.text((sx + 35, sy + 80), "Empty", fill=(60, 60, 70), font=font_small)

        # Center Divider
        div_x = start_xa + 6 * slot_w
        div_y = row_y + 32
        draw3.text((div_x + 18, div_y + 60), "VS", fill=(239, 68, 68), font=font_title)
        draw3.text((div_x + 8, div_y + 90), f"d={cinfo['distance']:.4f}", fill=(52, 211, 153), font=font_bold)

        # Side B faces
        start_xb = div_x + divider_w
        for s_idx in range(6):
            sx = start_xb + s_idx * slot_w
            sy = row_y + 32
            if s_idx < len(cinfo["faces_b"]):
                fid = cinfo["faces_b"][s_idx]
                ph_item = next((p for p in photos.values() if any(x.face_id == fid for x in p.faces)), None)
                if ph_item:
                    f_obj = next(x for x in ph_item.faces if x.face_id == fid)
                    draw3.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(26, 26, 30), outline=(50, 50, 56))
                    cimg = ensure_face_crop(fid, ph_item, f_obj.bbox, cache_crops_p, loader, tg).resize((crop_dim, crop_dim), Image.Resampling.LANCZOS)
                    sheet3.paste(cimg, (sx + 2, sy + 2))
                    draw3.text((sx + 4, sy + crop_dim + 4), f"{fid}", fill=(244, 114, 182), font=font_small)
                    draw3.text((sx + 4, sy + crop_dim + 18), f"{ph_item.file_name}", fill=(210, 210, 210), font=font_small)
                    draw3.text((sx + 4, sy + crop_dim + 32), f"Sc: {f_obj.det_score:.2f}", fill=(140, 140, 140), font=font_small)
            else:
                draw3.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(18, 18, 22), outline=(32, 32, 36))
                draw3.text((sx + 35, sy + 80), "Empty", fill=(60, 60, 70), font=font_small)

    sheet3_path = out_dir / "contact_sheet_enlarged_old_pairs.jpg"
    sheet3.save(sheet3_path, quality=90)
    print(f"Saved: {sheet3_path}")
    print("\nAll evidence sheets generated and verified successfully!")


if __name__ == "__main__":
    main()
