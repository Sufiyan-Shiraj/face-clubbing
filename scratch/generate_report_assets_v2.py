import sys
import json
import math
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

from backend.engine.cache import EmbeddingCache
from backend.engine.clusterer import FaceClusterer
from backend.engine.thumbnails import ThumbnailGenerator, select_representative_face

ASSETS_DIR = Path("report_assets_v2")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Load font
try:
    FONT = ImageFont.truetype("arial.ttf", 15)
    FONT_SM = ImageFont.truetype("arial.ttf", 12)
    FONT_LG = ImageFont.truetype("arialbd.ttf", 18)
except Exception:
    FONT = ImageFont.load_default()
    FONT_SM = ImageFont.load_default()
    FONT_LG = ImageFont.load_default()

def draw_tile(
    face_img: Image.Image,
    line1: str,
    line2: str = "",
    line3: str = "",
    tile_w: int = 240,
    tile_h: int = 310,
    img_size: int = 210,
) -> Image.Image:
    tile = Image.new("RGB", (tile_w, tile_h), (25, 28, 36))
    draw = ImageDraw.Draw(tile)

    # Resize face image to fit
    resized = face_img.resize((img_size, img_size), Image.Resampling.LANCZOS)
    x_offset = (tile_w - img_size) // 2
    tile.paste(resized, (x_offset, 12))

    # Draw border around face
    draw.rectangle(
        [x_offset - 1, 11, x_offset + img_size, 12 + img_size],
        outline=(60, 68, 85),
        width=1,
    )

    # Text lines
    y = 12 + img_size + 8
    if line1:
        draw.text((10, y), line1, fill=(240, 240, 245), font=FONT_SM)
        y += 18
    if line2:
        draw.text((10, y), line2, fill=(160, 175, 205), font=FONT_SM)
        y += 18
    if line3:
        draw.text((10, y), line3, fill=(130, 210, 160), font=FONT_SM)

    return tile

def make_grid(
    tiles: List[Image.Image],
    cols: int = 4,
    title: str = "",
    bg_color: Tuple[int, int, int] = (15, 17, 23),
) -> Image.Image:
    if not tiles:
        return Image.new("RGB", (400, 200), bg_color)

    tile_w, tile_h = tiles[0].size
    n = len(tiles)
    cols = min(cols, n)
    rows = math.ceil(n / cols)

    header_h = 55 if title else 20
    grid_w = cols * tile_w + (cols + 1) * 12
    grid_h = header_h + rows * tile_h + (rows + 1) * 12

    grid = Image.new("RGB", (grid_w, grid_h), bg_color)
    draw = ImageDraw.Draw(grid)

    if title:
        draw.text((16, 16), title, fill=(255, 255, 255), font=FONT_LG)

    for idx, t in enumerate(tiles):
        r = idx // cols
        c = idx % cols
        x = 12 + c * (tile_w + 12)
        y = header_h + r * (tile_h + 12)
        grid.paste(t, (x, y))

    return grid


def generate_all_v2_assets():
    print("=" * 60)
    print("GENERATING REPORT_ASSETS_V2 CONTACT SHEETS")
    print("=" * 60)

    cache = EmbeddingCache("export/.cache")
    photos = cache.load_all()
    crops_dir = Path("export/.cache/crops")
    thumb_gen = ThumbnailGenerator()

    # 1. Top 10 Clusters at threshold 0.50
    cl_050 = FaceClusterer(distance_threshold=0.50)
    people_050, unrec_050 = cl_050.cluster(photos)

    for rank, person in enumerate(people_050[:10], start=1):
        tiles = []
        for face in person.faces[:20]:
            crop_p = crops_dir / f"{face.face_id}.jpg"
            if crop_p.exists():
                face_img = Image.open(crop_p)
            else:
                orig_p = photos[face.photo_id].original_path
                temp_p = Path(f"scratch/temp_{face.face_id}.jpg")
                thumb_gen.generate_square_face_crop(orig_p, face.bbox, temp_p)
                face_img = Image.open(temp_p)

            orig_w = int(round(face.bbox[2] - face.bbox[0]))
            orig_h = int(round(face.bbox[3] - face.bbox[1]))
            full_filename = photos[face.photo_id].file_name

            tile = draw_tile(
                face_img=face_img,
                line1=full_filename, # Full filename, never truncated!
                line2=f"Size: {orig_w}x{orig_h}px (orig)",
                line3=f"Det score: {face.det_score:.3f}",
            )
            tiles.append(tile)

        grid = make_grid(
            tiles=tiles,
            cols=4,
            title=f"Cluster {person.id} (Rank #{rank}) - {len(person.photo_ids)} Photos, {len(person.faces)} Faces",
        )
        out_file = ASSETS_DIR / f"cluster_top{rank:02d}.jpg"
        grid.save(out_file, format="JPEG", quality=90)
        print(f"Generated {out_file.name}")

    # 2. Merge-Diff Sheet (threshold 0.50 vs 0.60)
    # Shows every pair of 0.50 clusters that merge at 0.60 (up to 30 pairs)
    print("\nComputing Merge-Diff (0.50 vs 0.60)...")
    cl_060 = FaceClusterer(distance_threshold=0.60)
    people_060, _ = cl_060.cluster(photos)

    # Map face_id -> 0.50 cluster_id
    face_to_050 = {}
    for p in people_050:
        for f in p.faces:
            face_to_050[f.face_id] = p.id

    merge_pairs = []
    for p60 in people_060:
        sub_050_clusters = defaultdict(list)
        for f in p60.faces:
            cid_050 = face_to_050.get(f.face_id)
            if cid_050:
                sub_050_clusters[cid_050].append(f)

        if len(sub_050_clusters) >= 2:
            sorted_subs = sorted(sub_050_clusters.keys(), key=lambda cid: len(sub_050_clusters[cid]), reverse=True)
            # Pair the dominant sub-cluster with each secondary sub-cluster that merged
            base_cid = sorted_subs[0]
            for other_cid in sorted_subs[1:]:
                merge_pairs.append({
                    "merged_id_060": p60.id,
                    "cid_a": base_cid,
                    "faces_a": sub_050_clusters[base_cid],
                    "cid_b": other_cid,
                    "faces_b": sub_050_clusters[other_cid],
                })

    print(f"Found {len(merge_pairs)} cluster merge pairs between 0.50 and 0.60.")
    # Build side-by-side comparison tiles
    merge_tiles = []
    for idx, mp in enumerate(merge_pairs[:30]):
        # Representative face for A
        fa = max(mp["faces_a"], key=lambda f: f.det_score)
        fb = max(mp["faces_b"], key=lambda f: f.det_score)

        img_a = Image.open(crops_dir / f"{fa.face_id}.jpg") if (crops_dir / f"{fa.face_id}.jpg").exists() else Image.new("RGB", (256, 256))
        img_b = Image.open(crops_dir / f"{fb.face_id}.jpg") if (crops_dir / f"{fb.face_id}.jpg").exists() else Image.new("RGB", (256, 256))

        # Side-by-side composite tile
        pair_tile = Image.new("RGB", (440, 290), (30, 33, 44))
        draw_p = ImageDraw.Draw(pair_tile)

        ra = img_a.resize((180, 180), Image.Resampling.LANCZOS)
        rb = img_b.resize((180, 180), Image.Resampling.LANCZOS)
        pair_tile.paste(ra, (15, 15))
        pair_tile.paste(rb, (245, 15))

        draw_p.rectangle([14, 14, 195, 195], outline=(80, 120, 200), width=2)
        draw_p.rectangle([244, 14, 425, 195], outline=(220, 100, 100), width=2)

        # Labels
        draw_p.text((15, 205), f"{mp['cid_a']} ({len(mp['faces_a'])} faces)", fill=(160, 200, 255), font=FONT)
        draw_p.text((15, 225), photos[fa.photo_id].file_name, fill=(200, 200, 200), font=FONT_SM)

        draw_p.text((245, 205), f"{mp['cid_b']} ({len(mp['faces_b'])} faces)", fill=(255, 170, 170), font=FONT)
        draw_p.text((245, 225), photos[fb.photo_id].file_name, fill=(200, 200, 200), font=FONT_SM)

        draw_p.text((15, 255), f"--> Merged into 0.60 Cluster {mp['merged_id_060']}", fill=(255, 220, 100), font=FONT)
        merge_tiles.append(pair_tile)

    if merge_tiles:
        merge_grid = make_grid(
            tiles=merge_tiles,
            cols=2,
            title=f"Merge-Diff: Clusters Separate at 0.50 that Merge at 0.60 ({len(merge_tiles)} Pairs Shown)",
        )
        merge_out = ASSETS_DIR / "merge_diff_0.50_vs_0.60.jpg"
        merge_grid.save(merge_out, format="JPEG", quality=90)
        print(f"Generated {merge_out.name}")

    # 3. Unrecognized Faces Comparison (V2 vs V1)
    print("\nGenerating Unrecognized Comparison...")
    all_unrec_v2 = [f for p in photos.values() for f in p.faces if not f.is_good_quality]
    sample_v2 = all_unrec_v2[:20]

    tiles_unrec_v2 = []
    for f in sample_v2:
        crop_p = crops_dir / f"{f.face_id}.jpg"
        if crop_p.exists():
            fimg = Image.open(crop_p)
        else:
            orig_p = photos[f.photo_id].original_path
            temp_p = Path(f"scratch/temp_unrec_{f.face_id}.jpg")
            thumb_gen.generate_square_face_crop(orig_p, f.bbox, temp_p)
            fimg = Image.open(temp_p)

        orig_w = int(round(f.bbox[2] - f.bbox[0]))
        orig_h = int(round(f.bbox[3] - f.bbox[1]))
        full_fn = photos[f.photo_id].file_name

        tile = draw_tile(
            face_img=fimg,
            line1=full_fn,
            line2=f"Size: {orig_w}x{orig_h}px (orig)",
            line3=f"{f.rejection_reason}",
        )
        tiles_unrec_v2.append(tile)

    grid_unrec_v2 = make_grid(
        tiles=tiles_unrec_v2,
        cols=4,
        title="V2 Unrecognized Faces (Measured in Original Pixels, Threshold < 64px or Score < 0.50)",
    )
    unrec_out = ASSETS_DIR / "unrecognized_faces_v2.jpg"
    grid_unrec_v2.save(unrec_out, format="JPEG", quality=90)
    print(f"Generated {unrec_out.name}")

    # Also build side-by-side with old run if export_old exists
    old_unrec_dir = Path("export_old/faces")
    if old_unrec_dir.exists():
        old_u_files = sorted(list(old_unrec_dir.glob("u*.jpg")))[:20]
        tiles_unrec_old = []
        for uf in old_u_files:
            fimg = Image.open(uf)
            tile = draw_tile(
                face_img=fimg,
                line1=uf.name,
                line2="V1 Unrecognized Crop",
                line3="Old 35px downscaled filter",
            )
            tiles_unrec_old.append(tile)
        grid_unrec_old = make_grid(
            tiles=tiles_unrec_old,
            cols=4,
            title="V1 Unrecognized Faces (Old Run, 35px Downscaled Filter)",
        )
        old_out = ASSETS_DIR / "unrecognized_faces_v1_old.jpg"
        grid_unrec_old.save(old_out, format="JPEG", quality=90)
        print(f"Generated {old_out.name}")

    print("\nALL V2 CONTACT SHEETS GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    generate_all_v2_assets()
