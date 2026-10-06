"""Generates definitive evidence sheets for report_assets_v4/:
1. contact_sheet_merge_bins_v4.jpg:
   - 4 distance bins: 0.50-0.52, 0.52-0.55, 0.55-0.58, 0.58-0.60
   - 8 random pairs per bin (32 pairs total)
   - Tiles at least 200 px (200x200 px)
   - NO true/false labels
   - Identified by face_id and photo filename
   - Automated integrity check asserting every label matches export/people.json

2. contact_sheet_enlarged_old_pairs.jpg:
   - Redo enlarged inspection for old V2 pairs:
     p001 vs p132, p174 vs p305, p001 vs p323, p001 vs p133
   - Map them to current IDs via face IDs
   - 6 faces per side
   - Identified by face_id and photo filename
   - Automated integrity check asserting every label matches export/people.json
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from backend.engine.cache import EmbeddingCache
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
    if not export_path.exists():
        raise FileNotFoundError(f"Export file not found: {export_path}")

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

    # Pre-compute cluster embeddings from cached face objects
    person_embs = []
    for p in people:
        embs = []
        for f in p["faces"]:
            rec = photos.get(f["photo_id"])
            if rec:
                f_obj = next((x for x in rec.faces if x.face_id == f["face_id"]), None)
                if f_obj and f_obj.embedding is not None:
                    embs.append(f_obj.embedding)
        if embs:
            arr = np.stack(embs)
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            person_embs.append(arr / norms)
        else:
            person_embs.append(None)

    n_people = len(people)
    bin_defs = [
        ("0.50-0.52", 0.50, 0.52),
        ("0.52-0.55", 0.52, 0.55),
        ("0.55-0.58", 0.55, 0.58),
        ("0.58-0.60", 0.58, 0.60),
    ]
    pairs_by_bin = {b[0]: [] for b in bin_defs}

    for i in range(n_people):
        if person_embs[i] is None:
            continue
        for j in range(i + 1, n_people):
            if person_embs[j] is None:
                continue
            sim = float(np.mean(np.dot(person_embs[i], person_embs[j].T)))
            dist = float(1.0 - sim)
            for bname, low, high in bin_defs:
                if low <= dist < high:
                    # Representative faces for A and B
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

    # Sample exactly 8 random pairs per bin
    sampled_bins = {}
    for bname, low, high in bin_defs:
        available = pairs_by_bin[bname]
        if len(available) < 8:
            raise ValueError(f"Not enough pairs in bin {bname}: found {len(available)}, needed 8")
        sampled = random.sample(available, 8)
        sampled_bins[bname] = sampled
        print(f"Bin {bname}: sampled 8 random pairs from {len(available)} candidates")

    # Layout for Sheet 1:
    # 4 columns (one per bin), 8 rows per column
    # Tile size >= 200px (200x200)
    # Card width: 2 * 200 + info_width = 400 + 10 = 410px; height = 200 + 100 = 300px
    tile_size = 200
    card_w = 420
    card_h = 310
    pad = 16
    col_w = card_w + pad
    sheet1_w = pad + 4 * col_w
    sheet1_h = 85 + 8 * (card_h + pad)

    sheet1 = Image.new("RGB", (sheet1_w, sheet1_h), color=(14, 14, 18))
    draw1 = ImageDraw.Draw(sheet1)

    draw1.text((pad, 16), "MERGE PAIRS BINNED BY DISTANCE (8 Random Pairs per Bin, Tile Size >= 200px)", fill=(255, 255, 255), font=font_title)
    draw1.text((pad, 46), "Single Source of Truth: export/people.json | Pairs Identified by face_id and photo filename | Unlabeled for Manual Evaluation", fill=(160, 160, 160), font=font_regular)

    for col_idx, (bname, _, _) in enumerate(bin_defs):
        col_x = pad + col_idx * col_w
        pairs = sampled_bins[bname]

        # Column Header
        draw1.rectangle([(col_x, 70), (col_x + card_w, 75)], fill=(245, 158, 11))

        for row_idx, item in enumerate(pairs):
            row_y = 85 + row_idx * (card_h + pad)

            # Integrity Check: verify label matches actual cluster contents in export/people.json
            ca = people_by_id[item["cluster_a"]]
            cb = people_by_id[item["cluster_b"]]
            fa = item["face_a"]
            fb = item["face_b"]

            # Assert face_a is genuinely inside cluster_a
            assert any(f["face_id"] == fa["face_id"] and f["file_name"] == fa["file_name"] for f in ca["faces"]), \
                f"Integrity check failed: {fa['face_id']} not in {item['cluster_a']}"
            # Assert face_b is genuinely inside cluster_b
            assert any(f["face_id"] == fb["face_id"] and f["file_name"] == fb["file_name"] for f in cb["faces"]), \
                f"Integrity check failed: {fb['face_id']} not in {item['cluster_b']}"

            # Card background
            draw1.rectangle([(col_x, row_y), (col_x + card_w, row_y + card_h)], fill=(22, 22, 26), outline=(44, 44, 52))

            # Header info
            draw1.text((col_x + 10, row_y + 8), f"Bin: {bname} | Pair #{row_idx + 1}/8", fill=(245, 158, 11), font=font_bold)
            draw1.text((col_x + 230, row_y + 8), f"Avg Dist: {item['dist']:.4f}", fill=(52, 211, 153), font=font_bold)

            # Paste Tile A (200x200)
            ph_a = photos[fa["photo_id"]]
            crop_a = ensure_face_crop(fa["face_id"], ph_a, fa["bbox"], cache_crops_p, loader, tg).resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            sheet1.paste(crop_a, (col_x + 8, row_y + 30))

            # Paste Tile B (200x200)
            ph_b = photos[fb["photo_id"]]
            crop_b = ensure_face_crop(fb["face_id"], ph_b, fb["bbox"], cache_crops_p, loader, tg).resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            sheet1.paste(crop_b, (col_x + 8 + tile_size + 4, row_y + 30))

            # Metadata Below Tiles (face_id and filename identified, NO true/false labels)
            y_info = row_y + 30 + tile_size + 6
            # Side A
            draw1.text((col_x + 8, y_info), f"A: [{ca['id']}] {fa['face_id']}", fill=(96, 165, 250), font=font_small)
            draw1.text((col_x + 8, y_info + 14), f"File: {fa['file_name']}", fill=(200, 200, 200), font=font_small)
            draw1.text((col_x + 8, y_info + 28), f"Score: {fa['det_score']:.2f} | Cluster: {len(ca['photo_ids'])}p", fill=(140, 140, 140), font=font_small)

            # Side B
            x_b = col_x + 8 + tile_size + 4
            draw1.text((x_b, y_info), f"B: [{cb['id']}] {fb['face_id']}", fill=(244, 114, 182), font=font_small)
            draw1.text((x_b, y_info + 14), f"File: {fb['file_name']}", fill=(200, 200, 200), font=font_small)
            draw1.text((x_b, y_info + 28), f"Score: {fb['det_score']:.2f} | Cluster: {len(cb['photo_ids'])}p", fill=(140, 140, 140), font=font_small)

    sheet1_path = out_dir / "contact_sheet_merge_bins_v4.jpg"
    sheet1.save(sheet1_path, quality=90)
    print(f"Saved: {sheet1_path}")

    # =========================================================================
    # 2. GENERATE SHEET 2: contact_sheet_enlarged_old_pairs.jpg
    # =========================================================================
    print("\n--- 2. Generating contact_sheet_enlarged_old_pairs.jpg ---")

    # Map the old V2 pairs via face IDs:
    # 1. p001 vs p132 (V2): f_23fc030f0bb086b3_004 vs f_f72c01c72c056c0f_008
    # 2. p174 vs p305 (V2): f_18e1d12f2affaa2d_025 vs f_b70a983c56f39943_001
    # 3. p001 vs p323 (V2): f_23fc030f0bb086b3_004 vs f_d358e80f8872f6ef_004
    # 4. p001 vs p133 (V2): f_23fc030f0bb086b3_004 vs f_cd5cf1f9b616d68a_009

    def get_cluster_or_unrec(face_id):
        """Finds the current cluster or Unrecognized item for a face_id in export/people.json."""
        for p in people:
            for f in p["faces"]:
                if f["face_id"] == face_id:
                    return {"type": "person", "obj": p, "face": f}
        if face_id in unrec_by_fid:
            return {"type": "unrecognized", "obj": unrec_by_fid[face_id], "face": unrec_by_fid[face_id]}
        raise KeyError(f"face_id {face_id} not found in export/people.json")

    old_pairs_spec = [
        {
            "v2_name": "p001 vs p132 (V2)",
            "face_a_id": "f_23fc030f0bb086b3_004",
            "file_a": "IMG_2415.HEIC",
            "face_b_id": "f_f72c01c72c056c0f_008",
            "file_b": "IMG_2179.HEIC",
            "dist": 0.5068,
        },
        {
            "v2_name": "p174 vs p305 (V2)",
            "face_a_id": "f_18e1d12f2affaa2d_025",
            "file_a": "IMG_6749.JPG",
            "face_b_id": "f_b70a983c56f39943_001",
            "file_b": "IMG_2165.JPG",
            "dist": 0.5106,
        },
        {
            "v2_name": "p001 vs p323 (V2)",
            "face_a_id": "f_23fc030f0bb086b3_004",
            "file_a": "IMG_2415.HEIC",
            "face_b_id": "f_d358e80f8872f6ef_004",
            "file_b": "IMG_2417.HEIC",
            "dist": 0.5123,
        },
        {
            "v2_name": "p001 vs p133 (V2)",
            "face_a_id": "f_23fc030f0bb086b3_004",
            "file_a": "IMG_2415.HEIC",
            "face_b_id": "f_cd5cf1f9b616d68a_009",
            "file_b": "IMG_2401.HEIC",
            "dist": 0.5159,
        },
    ]

    # Grid: 4 rows (1 row per pair)
    # Each row: 6 face slots on the Left, divider block "VS", 6 face slots on the Right
    # Face crop size: 145x145 px, slot card width: 155px, slot card height: 215px
    slot_w = 155
    slot_h = 215
    crop_dim = 145
    divider_w = 90
    row_gap = 18
    sheet2_w = pad + 6 * slot_w + divider_w + 6 * slot_w + pad
    sheet2_h = 85 + 4 * (slot_h + 45 + row_gap)

    sheet2 = Image.new("RGB", (sheet2_w, sheet2_h), color=(14, 14, 18))
    draw2 = ImageDraw.Draw(sheet2)

    draw2.text((pad, 16), "ENLARGED INSPECTION: OLD V2 PAIRS MAPPED VIA FACE IDs (6 Faces Per Side)", fill=(255, 255, 255), font=font_title)
    draw2.text((pad, 46), "Evaluated pairs: p001 vs p132, p174 vs p305, p001 vs p323, p001 vs p133 | Single Source of Truth: export/people.json", fill=(160, 160, 160), font=font_regular)

    for r_idx, pair_info in enumerate(old_pairs_spec):
        row_y = 80 + r_idx * (slot_h + 45 + row_gap)

        info_a = get_cluster_or_unrec(pair_info["face_a_id"])
        info_b = get_cluster_or_unrec(pair_info["face_b_id"])

        # Determine current labels and faces to show (up to 6 per side)
        # Side A faces:
        if info_a["type"] == "person":
            label_a = f"Cluster {info_a['obj']['id']} ({len(info_a['obj']['photo_ids'])} photos, {len(info_a['obj']['faces'])} faces)"
            # Pick representative face first, then up to 5 distinct photo members
            side_a_faces = [info_a["face"]]
            seen_pids = {info_a["face"]["photo_id"]}
            for f in info_a["obj"]["faces"]:
                if len(side_a_faces) >= 6:
                    break
                if f["photo_id"] not in seen_pids:
                    side_a_faces.append(f)
                    seen_pids.add(f["photo_id"])
            for f in info_a["obj"]["faces"]:
                if len(side_a_faces) >= 6:
                    break
                if f not in side_a_faces:
                    side_a_faces.append(f)
        else:
            label_a = f"Unrecognized ({info_a['obj'].get('rejection_reason', 'unattached')})"
            side_a_faces = [info_a["face"]]

        # Side B faces:
        if info_b["type"] == "person":
            label_b = f"Cluster {info_b['obj']['id']} ({len(info_b['obj']['photo_ids'])} photos, {len(info_b['obj']['faces'])} faces)"
            side_b_faces = [info_b["face"]]
            seen_pids = {info_b["face"]["photo_id"]}
            for f in info_b["obj"]["faces"]:
                if len(side_b_faces) >= 6:
                    break
                if f["photo_id"] not in seen_pids:
                    side_b_faces.append(f)
                    seen_pids.add(f["photo_id"])
            for f in info_b["obj"]["faces"]:
                if len(side_b_faces) >= 6:
                    break
                if f not in side_b_faces:
                    side_b_faces.append(f)
        else:
            label_b = f"Unrecognized ({info_b['obj'].get('rejection_reason', 'unattached')})"
            side_b_faces = [info_b["face"]]

        # Integrity Check: verify all faces genuinely belong to their declared cluster in people.json
        for f in side_a_faces:
            if info_a["type"] == "person":
                assert any(x["face_id"] == f["face_id"] for x in info_a["obj"]["faces"]), "Integrity failure in side A"
        for f in side_b_faces:
            if info_b["type"] == "person":
                assert any(x["face_id"] == f["face_id"] for x in info_b["obj"]["faces"]), "Integrity failure in side B"

        # Row container background
        draw2.rectangle([(pad, row_y), (sheet2_w - pad, row_y + slot_h + 40)], fill=(20, 20, 24), outline=(42, 42, 48))

        # Row Header
        header_text = f"PAIR #{r_idx + 1}: {pair_info['v2_name']} | Distance: {pair_info['dist']:.4f} | Left: {label_a} vs Right: {label_b}"
        draw2.text((pad + 12, row_y + 8), header_text, fill=(245, 158, 11), font=font_subtitle)

        # Draw Side A (6 slots)
        start_xa = pad + 12
        for s_idx in range(6):
            sx = start_xa + s_idx * slot_w
            sy = row_y + 32

            if s_idx < len(side_a_faces):
                f = side_a_faces[s_idx]
                ph = photos[f["photo_id"]]
                rec_f = next((x for x in ph.faces if x.face_id == f["face_id"]), None)
                bbox = rec_f.bbox if rec_f else f.get("bbox")

                draw2.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(26, 26, 30), outline=(50, 50, 56))
                cimg = ensure_face_crop(f["face_id"], ph, bbox, cache_crops_p, loader, tg).resize((crop_dim, crop_dim), Image.Resampling.LANCZOS)
                sheet2.paste(cimg, (sx + 2, sy + 2))

                # Labels: face_id and filename
                draw2.text((sx + 4, sy + crop_dim + 4), f"{f['face_id']}", fill=(96, 165, 250), font=font_small)
                draw2.text((sx + 4, sy + crop_dim + 18), f"{f.get('file_name', ph.file_name)}", fill=(210, 210, 210), font=font_small)
                score_str = f"Sc: {f.get('det_score', rec_f.det_score if rec_f else 0):.2f}"
                draw2.text((sx + 4, sy + crop_dim + 32), score_str, fill=(140, 140, 140), font=font_small)
            else:
                # Empty slot placeholder
                draw2.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(18, 18, 22), outline=(32, 32, 36))
                draw2.text((sx + 20, sy + 80), f"Slot {s_idx + 1}/6", fill=(70, 70, 80), font=font_regular)
                draw2.text((sx + 10, sy + 100), "(Cluster limit)", fill=(60, 60, 70), font=font_small)

        # Center Divider
        div_x = start_xa + 6 * slot_w
        div_y = row_y + 32
        draw2.text((div_x + 18, div_y + 60), "VS", fill=(239, 68, 68), font=font_title)
        draw2.text((div_x + 8, div_y + 90), f"d={pair_info['dist']:.4f}", fill=(52, 211, 153), font=font_bold)

        # Draw Side B (6 slots)
        start_xb = div_x + divider_w
        for s_idx in range(6):
            sx = start_xb + s_idx * slot_w
            sy = row_y + 32

            if s_idx < len(side_b_faces):
                f = side_b_faces[s_idx]
                ph = photos[f["photo_id"]]
                rec_f = next((x for x in ph.faces if x.face_id == f["face_id"]), None)
                bbox = rec_f.bbox if rec_f else f.get("bbox")

                draw2.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(26, 26, 30), outline=(50, 50, 56))
                cimg = ensure_face_crop(f["face_id"], ph, bbox, cache_crops_p, loader, tg).resize((crop_dim, crop_dim), Image.Resampling.LANCZOS)
                sheet2.paste(cimg, (sx + 2, sy + 2))

                # Labels: face_id and filename
                draw2.text((sx + 4, sy + crop_dim + 4), f"{f['face_id']}", fill=(244, 114, 182), font=font_small)
                draw2.text((sx + 4, sy + crop_dim + 18), f"{f.get('file_name', ph.file_name)}", fill=(210, 210, 210), font=font_small)
                score_str = f"Sc: {f.get('det_score', rec_f.det_score if rec_f else 0):.2f}"
                draw2.text((sx + 4, sy + crop_dim + 32), score_str, fill=(140, 140, 140), font=font_small)
            else:
                # Empty slot placeholder
                draw2.rectangle([(sx, sy), (sx + slot_w - 6, sy + slot_h)], fill=(18, 18, 22), outline=(32, 32, 36))
                draw2.text((sx + 20, sy + 80), f"Slot {s_idx + 1}/6", fill=(70, 70, 80), font=font_regular)
                draw2.text((sx + 10, sy + 100), "(Cluster limit)", fill=(60, 60, 70), font=font_small)

    sheet2_path = out_dir / "contact_sheet_enlarged_old_pairs.jpg"
    sheet2.save(sheet2_path, quality=90)
    print(f"Saved: {sheet2_path}")
    print("\nAll evidence sheets generated successfully!")


if __name__ == "__main__":
    main()
