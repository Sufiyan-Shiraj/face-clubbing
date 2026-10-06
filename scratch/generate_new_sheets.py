import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backend.engine.cache import EmbeddingCache
from backend.engine.loader import ImageLoader
from backend.engine.thumbnails import ThumbnailGenerator

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

def get_face_tile_256(face_id, photo_record, bbox, cache_crops_p, loader, tg, tile_size=260):
    cpath = cache_crops_p / f"{face_id}.jpg"
    if not cpath.exists():
        rgb, _, _, pil_img = loader.load_image(photo_record.original_path)
        tg.generate_square_face_crop_from_image(pil_img, bbox, cpath)
    im = Image.open(cpath).convert("RGB")
    if im.size != (tile_size, tile_size):
        im = im.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
    return im

def main():
    cache_dir = Path("export/.cache").resolve()
    cache_crops_p = cache_dir / "crops"
    cache = EmbeddingCache(cache_dir)
    records = cache.load_all()

    loader = ImageLoader()
    tg = ThumbnailGenerator(thumb_size=400, face_crop_size=256)

    people_data = json.load(open("export/people.json"))
    sug_data = json.load(open("export/.cache/suggestions.json"))
    out_dir = Path("report_assets_v4").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # SHEET 1: contact_sheet_split_pairs_reconciliation.jpg
    # Target faces:
    # 1. f_23fc030f0bb086b3_004 (IMG_2415)
    # 2. f_d358e80f8872f6ef_004 (IMG_2417)
    # 3. f_72100be076f21ac7_002 (IMG_2161)
    # 4. f_f72c01c72c056c0f_008 (IMG_2179)
    # 5. f_cd5cf1f9b616d68a_009 (IMG_2401)
    # 6. f_7739152de91187cf_010 (IMG_2400)
    # -------------------------------------------------------------------------
    print("\n=== Generating Sheet 1: contact_sheet_split_pairs_reconciliation.jpg ===")
    target_fids = [
        "f_23fc030f0bb086b3_004",
        "f_d358e80f8872f6ef_004",
        "f_72100be076f21ac7_002",
        "f_f72c01c72c056c0f_008",
        "f_cd5cf1f9b616d68a_009",
        "f_7739152de91187cf_010",
    ]

    faces_meta = []
    for fid in target_fids:
        pid = fid.split("_")[1]
        rec = records[pid]
        f_obj = next(f for f in rec.faces if f.face_id == fid)
        faces_meta.append({
            "face_id": fid,
            "photo_id": pid,
            "file_name": rec.file_name,
            "det_score": f_obj.det_score,
            "bbox": f_obj.bbox,
            "embedding": f_obj.embedding,
            "record": rec,
        })

    # 6x6 pairwise cosine distance matrix
    matrix_6x6 = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            matrix_6x6[i][j] = float(1.0 - np.dot(faces_meta[i]["embedding"], faces_meta[j]["embedding"]))

    # Layout for Sheet 1:
    # Width: 1800 px
    # Top banner: Header, title, description
    # Row of 6 cards: 6 x 280px + gaps
    tile_size = 260
    card_w = 280
    card_h = 420
    margin = 40
    gap = 20
    sheet1_w = margin * 2 + 6 * card_w + 5 * gap
    header_h = 160
    table_h = 360
    sheet1_h = header_h + card_h + table_h + 60

    img1 = Image.new("RGB", (sheet1_w, sheet1_h), color=(15, 23, 42))
    draw1 = ImageDraw.Draw(img1)

    # Header
    draw1.text((margin, 35), "Split Pairs Face Reconciliation & Pairwise Embedding Analysis", font=get_font(28, bold=True), fill=(248, 250, 252))
    draw1.text((margin, 75), "Comparison of 6 disputed faces from IMG_2415, IMG_2417, IMG_2161, IMG_2179, IMG_2401, IMG_2400 auto-merged into p001", font=get_font(15, bold=False), fill=(148, 163, 184))
    draw1.text((margin, 105), "Note: Unverified by engine - requires human organizer verification. Tile dimensions: 260x260 px.", font=get_font(13, bold=False), fill=(203, 213, 225))

    # Render 6 face cards
    for idx, f in enumerate(faces_meta):
        x = margin + idx * (card_w + gap)
        y = header_h
        # Card background
        draw1.rounded_rectangle([x, y, x + card_w, y + card_h], radius=12, fill=(30, 41, 59), outline=(51, 65, 85), width=2)
        # Face crop (260x260)
        tile = get_face_tile_256(f["face_id"], f["record"], f["bbox"], cache_crops_p, loader, tg, tile_size=tile_size)
        img1.paste(tile, (x + 10, y + 10))
        # Text details
        ty = y + tile_size + 20
        draw1.text((x + 12, ty), f"Face #{idx+1}: {f['file_name']}", font=get_font(14, bold=True), fill=(241, 245, 249))
        draw1.text((x + 12, ty + 24), f"ID: {f['face_id']}", font=get_font(11, bold=False), fill=(148, 163, 184))
        draw1.text((x + 12, ty + 42), f"Det Score: {f['det_score']:.4f}", font=get_font(12, bold=False), fill=(226, 232, 240))
        bbox_str = f"[{f['bbox'][0]:.1f}, {f['bbox'][1]:.1f}, {f['bbox'][2]:.1f}, {f['bbox'][3]:.1f}]"
        draw1.text((x + 12, ty + 60), f"BBox: {bbox_str}", font=get_font(11, bold=False), fill=(148, 163, 184))

    # Render 6x6 Table at the bottom
    ty_table = header_h + card_h + 40
    draw1.text((margin, ty_table), "Pairwise Embedding Cosine Distance Matrix (6x6 Table of Numbers):", font=get_font(18, bold=True), fill=(248, 250, 252))
    
    col_w = 230
    row_h = 36
    t_start_x = margin
    t_start_y = ty_table + 40

    # Table Header Row
    headers = ["Face ID / Photo"] + [f"#{i+1}: {faces_meta[i]['file_name']}" for i in range(6)]
    draw1.rectangle([t_start_x, t_start_y, t_start_x + 7 * col_w, t_start_y + row_h], fill=(51, 65, 85))
    for c_idx, htext in enumerate(headers):
        tx = t_start_x + c_idx * col_w + 10
        draw1.text((tx, t_start_y + 8), htext, font=get_font(12, bold=True), fill=(255, 255, 255))

    # Table Data Rows
    for r_idx in range(6):
        ry = t_start_y + (r_idx + 1) * row_h
        row_bg = (30, 41, 59) if r_idx % 2 == 0 else (24, 33, 47)
        draw1.rectangle([t_start_x, ry, t_start_x + 7 * col_w, ry + row_h], fill=row_bg, outline=(51, 65, 85), width=1)
        # Row header
        row_title = f"#{r_idx+1}: {faces_meta[r_idx]['file_name']} ({faces_meta[r_idx]['face_id'][:12]}...)"
        draw1.text((t_start_x + 10, ry + 9), row_title, font=get_font(11, bold=True), fill=(226, 232, 240))
        # Cells
        for c_idx in range(6):
            dist_val = matrix_6x6[r_idx][c_idx]
            cx = t_start_x + (c_idx + 1) * col_w + 10
            # Highlight diagonal or low distance
            if r_idx == c_idx:
                txt_color = (148, 163, 184)
            elif dist_val < 0.50:
                txt_color = (74, 222, 128)  # green for match < 0.50
            else:
                txt_color = (248, 113, 113)  # red/amber for >= 0.50
            draw1.text((cx, ry + 9), f"{dist_val:.4f}", font=get_font(13, bold=(r_idx != c_idx)), fill=txt_color)

    sheet1_path = out_dir / "contact_sheet_split_pairs_reconciliation.jpg"
    img1.save(sheet1_path, quality=95)
    print(f"Saved: {sheet1_path} ({img1.size})")

    # -------------------------------------------------------------------------
    # SHEET 2: contact_sheet_collision_audit.jpg
    # Clusters with faces > photos:
    # 1. p014 (22 photos, 24 faces): 2 colliding pairs:
    #    - IMG_2093.HEIC: f_e25688a0ee978709_006 & f_e25688a0ee978709_003 (dist: 0.6478)
    #    - IMG_2225.JPG: f_de8394820ab47c98_008 & f_de8394820ab47c98_006 (dist: 0.8006)
    # 2. p041 (9 photos, 11 faces): 1 colliding triplet:
    #    - IMG_20260304_002918.jpg: f_4a9b927f5789cd69_001, 005, 007
    #      (d(1,5)=0.2321, d(1,7)=0.1237, d(5,7)=0.2878)
    # 3. p062 (3 photos, 4 faces): 1 colliding pair:
    #    - IMG_20260304_080950.jpg: f_df7e608ffd3212b2_013 & f_df7e608ffd3212b2_008 (dist: 0.5349)
    # Tiles at least 250px (260x260).
    # -------------------------------------------------------------------------
    print("\n=== Generating Sheet 2: contact_sheet_collision_audit.jpg ===")
    collision_groups = [
        {
            "cluster_id": "p014",
            "cluster_photos": 22,
            "cluster_faces": 24,
            "photo_id": "e25688a0ee978709",
            "filename": "IMG_2093.HEIC",
            "faces": [
                {"fid": "f_e25688a0ee978709_006", "score": 0.5604, "bbox": [388.7, 1275.5, 572.7, 1625.3]},
                {"fid": "f_e25688a0ee978709_003", "score": 0.7247, "bbox": [2897.1, 466.4, 3085.0, 704.5]},
            ],
            "distance_info": "Pairwise Distance: 0.6478"
        },
        {
            "cluster_id": "p014",
            "cluster_photos": 22,
            "cluster_faces": 24,
            "photo_id": "de8394820ab47c98",
            "filename": "IMG_2225.JPG",
            "faces": [
                {"fid": "f_de8394820ab47c98_008", "score": 0.6617, "bbox": [464.5, 1456.3, 608.3, 1750.0]},
                {"fid": "f_de8394820ab47c98_006", "score": 0.7501, "bbox": [2752.2, 1323.8, 2867.5, 1442.9]},
            ],
            "distance_info": "Pairwise Distance: 0.8006"
        },
        {
            "cluster_id": "p041",
            "cluster_photos": 9,
            "cluster_faces": 11,
            "photo_id": "4a9b927f5789cd69",
            "filename": "IMG_20260304_002918.jpg",
            "faces": [
                {"fid": "f_4a9b927f5789cd69_001", "score": 0.9110, "bbox": [118.8, 1492.0, 207.3, 1601.5]},
                {"fid": "f_4a9b927f5789cd69_005", "score": 0.8767, "bbox": [890.7, 1596.6, 976.2, 1718.1]},
                {"fid": "f_4a9b927f5789cd69_007", "score": 0.8728, "bbox": [914.4, 158.0, 1004.6, 271.4]},
            ],
            "distance_info": "d(001, 005) = 0.2321 | d(001, 007) = 0.1237 | d(005, 007) = 0.2878"
        },
        {
            "cluster_id": "p062",
            "cluster_photos": 3,
            "cluster_faces": 4,
            "photo_id": "df7e608ffd3212b2",
            "filename": "IMG_20260304_080950.jpg",
            "faces": [
                {"fid": "f_df7e608ffd3212b2_013", "score": 0.5846, "bbox": [794.4, 1221.0, 814.4, 1245.8]},
                {"fid": "f_df7e608ffd3212b2_008", "score": 0.7093, "bbox": [533.7, 1556.4, 558.5, 1587.2]},
            ],
            "distance_info": "Pairwise Distance: 0.5349"
        },
    ]

    # Layout for Sheet 2:
    # 4 rows (one per colliding photo)
    # Row 1: p014 in IMG_2093 (2 faces)
    # Row 2: p014 in IMG_2225 (2 faces)
    # Row 3: p041 in IMG_20260304_002918 (3 faces)
    # Row 4: p062 in IMG_20260304_080950 (2 faces)
    # Width: 1200 px
    sheet2_w = 1200
    row_height = 360
    header2_h = 140
    sheet2_h = header2_h + len(collision_groups) * row_height + 40

    img2 = Image.new("RGB", (sheet2_w, sheet2_h), color=(15, 23, 42))
    draw2 = ImageDraw.Draw(img2)

    # Header
    draw2.text((margin, 30), "Same-Photo Collision Audit Contact Sheet", font=get_font(26, bold=True), fill=(248, 250, 252))
    draw2.text((margin, 68), "Full audit of 3 clusters with faces > photos: p014 (24f/22p), p041 (11f/9p), p062 (4f/3p) - 5 extra co-occurring faces", font=get_font(14, bold=False), fill=(148, 163, 184))
    draw2.text((margin, 95), "Displays photo ID, filename, face ID, det_score, bbox, and pairwise embedding distance. Tiles >= 250px.", font=get_font(13, bold=False), fill=(203, 213, 225))

    for g_idx, cg in enumerate(collision_groups):
        gy = header2_h + g_idx * row_height
        # Section background
        draw2.rounded_rectangle([margin, gy, sheet2_w - margin, gy + row_height - 20], radius=12, fill=(30, 41, 59), outline=(51, 65, 85), width=2)
        
        # Section header text
        sec_title = f"Case #{g_idx+1}: Cluster {cg['cluster_id']} ({cg['cluster_photos']} photos, {cg['cluster_faces']} faces) | Photo: {cg['filename']} (ID: {cg['photo_id']})"
        draw2.text((margin + 18, gy + 14), sec_title, font=get_font(15, bold=True), fill=(241, 245, 249))
        draw2.text((margin + 18, gy + 38), cg["distance_info"], font=get_font(13, bold=True), fill=(56, 189, 248))

        # Render face tiles in this collision case
        for f_idx, f_info in enumerate(cg["faces"]):
            fx = margin + 18 + f_idx * (tile_size + 24)
            fy = gy + 64
            rec = records[cg["photo_id"]]
            tile = get_face_tile_256(f_info["fid"], rec, f_info["bbox"], cache_crops_p, loader, tg, tile_size=250)
            img2.paste(tile, (fx, fy))
            # Text below tile
            draw2.text((fx, fy + 256), f"Face ID: {f_info['fid']}", font=get_font(11, bold=True), fill=(248, 250, 252))
            draw2.text((fx, fy + 274), f"Score: {f_info['score']:.4f} | BBox: {[round(x,1) for x in f_info['bbox']]}", font=get_font(10, bold=False), fill=(148, 163, 184))

    sheet2_path = out_dir / "contact_sheet_collision_audit.jpg"
    img2.save(sheet2_path, quality=95)
    print(f"Saved: {sheet2_path} ({img2.size})")

    # -------------------------------------------------------------------------
    # SHEET 3: contact_sheet_maybe_bin_0.58_0.60.jpg
    # Every maybe link in 0.58-0.60 bin (7 links):
    # 1. p140 (1p) <-> p141 (1p), d = 0.5848
    # 2. p004 (36p) <-> p145 (1p), d = 0.5854
    # 3. p006 (29p) <-> p174 (1p), d = 0.5992
    # 4. p009 (27p) <-> p055 (5p), d = 0.5933
    # 5. p030 (14p) <-> p119 (1p), d = 0.5907
    # 6. p033 (12p) <-> p073 (2p), d = 0.5978
    # 7. p047 (7p) <-> p134 (1p), d = 0.5837
    # Cluster IDs, photo counts, face_ids, filenames. NO true/false labels.
    # Tiles at least 250px.
    # -------------------------------------------------------------------------
    print("\n=== Generating Sheet 3: contact_sheet_maybe_bin_0.58_0.60.jpg ===")
    people_by_id = {p["id"]: p for p in people_data["people"]}
    maybe_7_links = [
        {"ca": "p140", "cb": "p141", "dist": 0.5848},
        {"ca": "p004", "cb": "p145", "dist": 0.5854},
        {"ca": "p006", "cb": "p174", "dist": 0.5992},
        {"ca": "p009", "cb": "p055", "dist": 0.5933},
        {"ca": "p030", "cb": "p119", "dist": 0.5907},
        {"ca": "p033", "cb": "p073", "dist": 0.5978},
        {"ca": "p047", "cb": "p134", "dist": 0.5837},
    ]

    sheet3_w = 1200
    row3_h = 360
    header3_h = 140
    sheet3_h = header3_h + len(maybe_7_links) * row3_h + 40

    img3 = Image.new("RGB", (sheet3_w, sheet3_h), color=(15, 23, 42))
    draw3 = ImageDraw.Draw(img3)

    # Header
    draw3.text((margin, 30), "Candidate Merge Links in Distance Bin [0.58, 0.60]", font=get_font(26, bold=True), fill=(248, 250, 252))
    draw3.text((margin, 68), "All 7 pairwise suggestions in suggestions.json with top-5 centroid distance 0.58 to 0.60", font=get_font(14, bold=False), fill=(148, 163, 184))
    draw3.text((margin, 95), "Organizer inspection sheet: Cluster IDs, photo counts, face IDs, and filenames. NO subjective true/false labels.", font=get_font(13, bold=False), fill=(203, 213, 225))

    for l_idx, l in enumerate(maybe_7_links):
        ly = header3_h + l_idx * row3_h
        pa = people_by_id[l["ca"]]
        pb = people_by_id[l["cb"]]

        # Rep face for each side
        fa = pa["faces"][0]
        fb = pb["faces"][0]
        rec_a = records[fa["photo_id"]]
        rec_b = records[fb["photo_id"]]

        draw3.rounded_rectangle([margin, ly, sheet3_w - margin, ly + row3_h - 20], radius=12, fill=(30, 41, 59), outline=(51, 65, 85), width=2)

        # Header info for this link
        link_title = f"Suggestion #{l_idx+1}: {l['ca']} ({len(pa['photos'])} photos) <---> {l['cb']} ({len(pb['photos'])} photos)  |  Centroid Distance: {l['dist']:.4f}"
        draw3.text((margin + 18, ly + 14), link_title, font=get_font(15, bold=True), fill=(241, 245, 249))

        # Render Side A
        tile_a = get_face_tile_256(fa["face_id"], rec_a, fa["bbox"], cache_crops_p, loader, tg, tile_size=250)
        ax = margin + 20
        ay = ly + 46
        img3.paste(tile_a, (ax, ay))
        draw3.text((ax, ay + 254), f"Side A: {l['ca']} ({rec_a.file_name})", font=get_font(12, bold=True), fill=(226, 232, 240))
        draw3.text((ax, ay + 272), f"Face ID: {fa['face_id']}", font=get_font(10, bold=False), fill=(148, 163, 184))

        # Middle arrow / badge
        mid_x = ax + 250 + 60
        mid_y = ay + 110
        draw3.rounded_rectangle([mid_x, mid_y, mid_x + 160, mid_y + 44], radius=8, fill=(51, 65, 85))
        draw3.text((mid_x + 18, mid_y + 12), f"d = {l['dist']:.4f}", font=get_font(16, bold=True), fill=(56, 189, 248))

        # Render Side B
        bx = mid_x + 160 + 60
        by = ly + 46
        tile_b = get_face_tile_256(fb["face_id"], rec_b, fb["bbox"], cache_crops_p, loader, tg, tile_size=250)
        img3.paste(tile_b, (bx, by))
        draw3.text((bx, by + 254), f"Side B: {l['cb']} ({rec_b.file_name})", font=get_font(12, bold=True), fill=(226, 232, 240))
        draw3.text((bx, by + 272), f"Face ID: {fb['face_id']}", font=get_font(10, bold=False), fill=(148, 163, 184))

    sheet3_path = out_dir / "contact_sheet_maybe_bin_0.58_0.60.jpg"
    img3.save(sheet3_path, quality=95)
    print(f"Saved: {sheet3_path} ({img3.size})")

if __name__ == "__main__":
    main()
