"""Orchestrates the full PhotoSorter engine pipeline."""

from __future__ import annotations
import gc
import json
import datetime
import sys
import time
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
import numpy as np

from backend.engine.models import EngineResult, PhotoRecord
from backend.engine.scanner import PhotoScanner, ScannedPhoto, compute_file_hash
from backend.engine.loader import ImageLoader
from backend.engine.cache import EmbeddingCache
from backend.engine.detector import FaceDetector
from backend.engine.clusterer import FaceClusterer
from backend.engine.exporter import BundleExporter
from backend.drive import (
    is_drive_folder_input,
    parse_drive_folder_id,
    get_drive_api_key,
    DriveClient,
    DriveError,
    DriveAuthError,
    DrivePermissionError,
    DriveQuotaError,
)


@dataclass
class EngineConfig:
    input_path: str | Path
    output_dir: str | Path = "export"
    cache_dir: Optional[str | Path] = None
    distance_threshold: float = 0.5
    min_det_score: float = 0.5
    min_face_size: int = 64
    max_yaw: float = 70.0
    seed_min_face_size: int = 64
    seed_max_yaw: float = 60.0
    seed_min_det_score: float = 0.70
    max_image_dim: int = 1600
    thumb_size: int = 400
    face_crop_size: int = 384
    event_title: str = "Event Gallery"
    event_subtitle: str = "Photos grouped by person"
    second_pass_merge: bool = True
    merge_threshold: float = 0.50
    maybe_threshold: float = 0.65
    same_photo_merge_max: float = 0.40
    attach_distance_cap: float = 0.45
    flip_average: bool = False
    include_maybe: bool = False
    model_root: Optional[str] = None
    suggestions_path: Optional[str | Path] = None
    drive_api_key: Optional[str] = None
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    cancel_check: Optional[Callable[[], bool]] = None


def run_pipeline(config: EngineConfig) -> EngineResult:
    """
    Executes the end-to-end PhotoSorter engine:
    Scan -> Detect & Embed (with caching) -> Cluster -> Export Bundle.
    """
    out_dir_str = str(config.output_dir or "export")
    if out_dir_str.startswith("http://") or out_dir_str.startswith("https://") or "drive.google.com" in out_dir_str:
        out_dir_str = "export"
    out_p = Path(out_dir_str).resolve()
    cache_p = Path(config.cache_dir).resolve() if config.cache_dir else out_p.parent / f"{out_p.name}.work"
    cache_thumbs_p = cache_p / "thumbs"
    cache_crops_p = cache_p / "crops"
    cache_thumbs_p.mkdir(parents=True, exist_ok=True)
    cache_crops_p.mkdir(parents=True, exist_ok=True)

    def notify(payload: Dict[str, Any]):
        if config.cancel_check and config.cancel_check():
            raise InterruptedError("Job cancelled by user")
        if config.progress_callback:
            config.progress_callback(payload)

    input_str = str(config.input_path)
    is_drive = is_drive_folder_input(input_str)

    if is_drive:
        folder_id = parse_drive_folder_id(input_str)
        api_key = config.drive_api_key or get_drive_api_key()
        if not api_key:
            raise DriveAuthError(
                "Google Drive API key is required. Please set it in Settings or set the DRIVE_API_KEY environment variable."
            )

        client = DriveClient(api_key=api_key)
        folder_name = client.get_folder_name(folder_id)
        if not folder_name:
            folder_name = config.event_title if config.event_title and config.event_title != "Event Gallery" else "drive"
        safe_folder_name = re.sub(r'[\\/*?:"<>|]', "", folder_name).strip() or "drive"

        # Temporary folder named <folder_name>_temp (deleted when bundle is exported)
        drive_cache_p = cache_p.parent / f"{safe_folder_name}_temp"
        drive_cache_p.mkdir(parents=True, exist_ok=True)

        notify({
            "stage": "listing",
            "current": 0,
            "total": 0,
            "percent": 0.5,
            "message": f"Listing images from Google Drive folder '{folder_name}'...",
        })

        list_res = client.list_folder_images(
            folder_id=folder_id,
            cancel_check=config.cancel_check,
            progress_callback=notify,
        )

        if list_res.image_count == 0:
            details = []
            if list_res.skipped_folders_count > 0:
                folders_sample = ", ".join(f"'{name}'" for name in list_res.scanned_folder_names[:4])
                details.append(f"searched {list_res.skipped_folders_count} subfolders ({folders_sample})")
            if list_res.skipped_videos_count > 0:
                details.append(f"ignored {list_res.skipped_videos_count} video files")
            if list_res.skipped_non_images_count > 0:
                files_sample = ", ".join(f"'{name}'" for name in list_res.non_image_sample_names[:3])
                details.append(f"skipped {list_res.skipped_non_images_count} non-image files like {files_sample}")
            detail_str = "; ".join(details) if details else "folder is empty"
            raise ValueError(
                f"No image files found in Google Drive folder '{folder_id}' ({detail_str}). "
                "Please verify that you provided the link to the folder containing photos."
            )

        notify({
            "stage": "downloading",
            "current": 0,
            "total": list_res.image_count,
            "percent": 1.0,
            "message": f"Downloading {list_res.image_count} photos from Google Drive...",
        })

        downloaded_items = client.download_thumbnails(
            files=list_res.files,
            cache_dir=drive_cache_p,
            progress_callback=notify,
            cancel_check=config.cancel_check,
        )

        scanned_photos = []
        for df, local_p in downloaded_items:
            photo_id = compute_file_hash(local_p)
            scanned_photos.append(
                ScannedPhoto(
                    photo_id=photo_id,
                    file_path=local_p,
                    file_name=df.name,
                    relative_path=local_p.name,
                    download_url=df.download_url,
                    drive_file_id=df.id,
                    drive_url=getattr(df, "drive_url", f"https://drive.google.com/file/d/{df.id}/view"),
                    share_url=getattr(df, "share_url", f"https://drive.google.com/file/d/{df.id}/view?usp=sharing"),
                )
            )

        total_photos = len(scanned_photos)
        notify({
            "stage": "scanned",
            "current": 0,
            "total": total_photos,
            "percent": 2.0,
            "message": f"Downloaded {total_photos} photos ready for face detection.",
        })
    else:
        input_p = Path(config.input_path).resolve()
        # 1. Scan photos
        notify({"stage": "scanning", "current": 0, "total": 0, "percent": 0.0, "message": f"Scanning input: {input_p}"})
        with PhotoScanner(input_p) as scanner:
            def on_scan_progress(cur: int, tot: int, fname: str):
                pct = round((cur / tot) * 2.0, 1) if tot > 0 else 0.0
                notify({
                    "stage": "scanning",
                    "current": cur,
                    "total": tot,
                    "percent": pct,
                    "file_name": fname,
                    "message": f"Scanning photos: [{cur}/{tot}] {fname}",
                })

            scanned_photos = scanner.scan(progress_callback=on_scan_progress)
            total_photos = len(scanned_photos)
            if total_photos == 0:
                raise ValueError(f"No supported photos found in: {input_p}")

            notify({
                "stage": "scanned",
                "current": 0,
                "total": total_photos,
                "percent": 2.0,
                "message": f"Found {total_photos} photos to process.",
            })

    # 2. Setup Cache, Loader, Detector, and Thumb Generator
    cache = EmbeddingCache(cache_p)
    loader = ImageLoader(max_dimension=config.max_image_dim)
    from backend.engine.thumbnails import ThumbnailGenerator
    thumb_gen = ThumbnailGenerator(thumb_size=config.thumb_size, face_crop_size=config.face_crop_size)
    detector: Optional[FaceDetector] = None

    photos: Dict[str, PhotoRecord] = {}

    # 3. Detect and Embed (with thumbnail & crop caching)
    start_time = time.time()
    for idx, item in enumerate(scanned_photos):
        if config.cancel_check and config.cancel_check():
            raise InterruptedError("Job cancelled by user")
        photo_id = item.photo_id

        if cache.has(photo_id):
            record = cache.get(photo_id)
            if record:
                record.original_path = str(item.file_path)
                record.file_name = item.file_name
                if getattr(item, "download_url", None):
                    record.download_url = item.download_url
                if getattr(item, "drive_file_id", None):
                    record.drive_file_id = item.drive_file_id
                if getattr(item, "drive_url", None):
                    record.drive_url = item.drive_url
                if getattr(item, "share_url", None):
                    record.share_url = item.share_url
                photos[photo_id] = record

                # Ensure thumbnail and crops are cached for fast exports
                cached_thumb = cache_thumbs_p / f"{photo_id}.jpg"
                crops_missing = any(
                    not (cache_crops_p / f"{f.face_id}.jpg").exists()
                    for f in record.faces
                )
                if not cached_thumb.exists() or crops_missing:
                    _, _, _, pil_img = loader.load_image(item.file_path)
                    if not cached_thumb.exists():
                        thumb_gen.generate_photo_thumbnail_from_image(pil_img, cached_thumb)
                    for f in record.faces:
                        cpath = cache_crops_p / f"{f.face_id}.jpg"
                        if not cpath.exists():
                            thumb_gen.generate_square_face_crop_from_image(pil_img, f.bbox, cpath)
                    del pil_img
                    gc.collect()
        else:
            if detector is None:
                notify({
                    "stage": "model_init",
                    "current": 0,
                    "total": total_photos,
                    "percent": 2.0,
                    "message": "Initializing InsightFace model...",
                })
                detector = FaceDetector(
                    model_name="buffalo_l",
                    model_root=config.model_root,
                    min_det_score=config.min_det_score,
                    min_face_size=config.min_face_size,
                    max_yaw=config.max_yaw,
                    max_image_dim=config.max_image_dim,
                    progress_callback=notify,
                )

            rgb_img, orig_w, orig_h, pil_img = loader.load_image(item.file_path)
            faces = detector.detect_and_embed(
                orig_rgb=rgb_img,
                photo_id=photo_id,
            )

            # Pre-generate and cache photo thumbnail from in-memory image
            cached_thumb = cache_thumbs_p / f"{photo_id}.jpg"
            if not cached_thumb.exists():
                thumb_gen.generate_photo_thumbnail_from_image(pil_img, cached_thumb)

            # Pre-generate and cache face crops from in-memory image
            for f in faces:
                cached_crop = cache_crops_p / f"{f.face_id}.jpg"
                if not cached_crop.exists():
                    thumb_gen.generate_square_face_crop_from_image(pil_img, f.bbox, cached_crop)

            # Free image memory immediately
            del rgb_img, pil_img
            gc.collect()

            record = PhotoRecord(
                photo_id=photo_id,
                original_path=str(item.file_path),
                file_name=item.file_name,
                width=orig_w,
                height=orig_h,
                download_url=getattr(item, "download_url", None),
                drive_file_id=getattr(item, "drive_file_id", None),
                drive_url=getattr(item, "drive_url", None),
                share_url=getattr(item, "share_url", None),
                faces=faces,
            )
            cache.save(record)
            photos[photo_id] = record

        # Compute ETA
        elapsed = time.time() - start_time
        processed = idx + 1
        avg_per_photo = elapsed / processed
        eta_seconds = (total_photos - processed) * avg_per_photo

        # Scale detection/embedding phase from 2% to 88% so subsequent stages (clustering, export) never go backwards
        pct = round(2.0 + (processed / total_photos) * 86.0, 1) if total_photos > 0 else 2.0
        face_ids_found = [f.face_id for f in photos[photo_id].faces if getattr(f, "face_id", None)]
        notify({
            "stage": "processing",
            "current": processed,
            "total": total_photos,
            "percent": pct,
            "photo_id": photo_id,
            "file_name": item.file_name,
            "faces_found": len(photos[photo_id].faces),
            "new_faces": face_ids_found,
            "eta_seconds": round(eta_seconds, 1),
            "message": f"[{processed}/{total_photos}] {item.file_name} ({len(photos[photo_id].faces)} faces)",
        })

    # 4. Clustering (with optional flip_average)
    if config.flip_average:
        notify({"stage": "flip_averaging", "current": total_photos, "total": total_photos, "percent": 90.0, "message": "Applying flip-averaged embeddings..."})
        for photo in photos.values():
            for face in photo.faces:
                if face.embedding_flipped is not None:
                    face.embedding = face.embedding_flipped

    notify({"stage": "clustering", "current": total_photos, "total": total_photos, "percent": 92.0, "message": "Clustering faces by person with second-pass merge..."})
    clusterer = FaceClusterer(
        distance_threshold=config.distance_threshold,
        seed_min_face_size=config.seed_min_face_size or config.min_face_size,
        seed_max_yaw=config.seed_max_yaw,
        seed_min_det_score=config.seed_min_det_score,
        second_pass_merge=config.second_pass_merge,
        merge_threshold=config.merge_threshold,
        maybe_threshold=config.maybe_threshold,
        same_photo_merge_max=config.same_photo_merge_max,
        attach_distance_cap=config.attach_distance_cap,
    )
    people, unrecognized = clusterer.cluster(photos)

    # 4b. Suggested merges / maybe groups (organizer-only; NEVER in public export bundle)
    sug_payload = {
        "version": 1,
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "threshold_range": [config.merge_threshold, config.maybe_threshold],
        "maybe_groups_count": len(clusterer.maybe_groups),
        "maybe_groups": clusterer.maybe_groups,
        "ambiguous_faces_count": len(clusterer.ambiguous_faces),
        "ambiguous_faces": clusterer.ambiguous_faces,
        "stats": clusterer.stats,
    }
    sug_path = Path(config.suggestions_path).resolve() if config.suggestions_path else cache_p / "suggestions.json"
    sug_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sug_path, "w", encoding="utf-8") as f:
        json.dump(sug_payload, f, indent=2)

    # Write id_map.json into work directory (organizer-only)
    id_map_path = cache_p / "id_map.json"
    with open(id_map_path, "w", encoding="utf-8") as f:
        json.dump(clusterer.id_map, f, indent=2)

    # 4c. Organizer edit replay (SPEC 6.3)
    edits_path = cache_p / "edits.json"
    if edits_path.exists():
        notify({"stage": "applying_edits", "message": f"Applying organizer edits from {edits_path}..."})
        with open(edits_path, "r", encoding="utf-8") as f:
            edits_data = json.load(f)
        from backend.engine.edits import apply_edits
        people, unrecognized, unapplied, edit_stats = apply_edits(people, unrecognized, edits_data, photos)
        if unapplied:
            print(f"\n[WARNING] {len(unapplied)} edits could not be applied:")
            for u in unapplied:
                print(f"  - {u.get('reason')}: {u.get('edit')}")
        notify({
            "stage": "edits_applied",
            "applied": edit_stats.get("applied", 0),
            "unapplied": len(unapplied),
            "message": f"Applied {edit_stats.get('applied', 0)} edits ({len(unapplied)} unapplied).",
        })

    result = EngineResult(
        photos=photos,
        people=people,
        unrecognized=unrecognized,
        distance_threshold=config.distance_threshold,
        id_map=clusterer.id_map,
        temp_dir=str(drive_cache_p) if is_drive else None,
        drive_folder_name=folder_name if is_drive else None,
    )

    notify({
        "stage": "clustered",
        "people_count": len(people),
        "unrecognized_photos": len(unrecognized.photo_ids),
        "unrecognized_faces": len(unrecognized.faces),
        "maybe_groups_count": len(clusterer.maybe_groups),
        "message": f"Formed {len(people)} people clusters ({len(clusterer.maybe_groups)} connected maybe groups). {len(unrecognized.photo_ids)} photos in Unrecognized.",
    })

    # 5. Export Bundle
    notify({"stage": "exporting", "current": total_photos, "total": total_photos, "percent": 96.0, "message": f"Generating static export bundle in {out_p}..."})
    exporter = BundleExporter(
        output_dir=out_p,
        cache_dir=cache_p,
        thumb_size=config.thumb_size,
        face_crop_size=config.face_crop_size,
    )
    exporter.export(
        result=result,
        title=config.event_title,
        subtitle=config.event_subtitle,
        config_override={"include_maybe": config.include_maybe},
        include_maybe=config.include_maybe,
    )

    notify({
        "stage": "complete",
        "current": total_photos,
        "total": total_photos,
        "percent": 100.0,
        "message": "Export complete!",
        "output_dir": str(out_p),
        "people_count": len(people),
    })

    return result
