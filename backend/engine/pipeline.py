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
    DriveAuthError,
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
    face_crop_size: int = 256
    event_title: str = "Event Gallery"
    event_subtitle: str = "Photos grouped by person"
    second_pass_merge: bool = True
    merge_threshold: float = 0.50
    maybe_threshold: float = 0.65
    same_photo_merge_max: float = 0.40
    attach_distance_cap: float = 0.45
    flip_average: bool = False
    include_maybe: bool = False
    replay_edits: bool = False
    model_root: Optional[str] = None
    suggestions_path: Optional[str | Path] = None
    drive_api_key: Optional[str] = None
    scan_subfolders: bool = True
    max_subfolder_depth: int = 5
    follow_shortcuts: bool = False
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    cancel_check: Optional[Callable[[], bool]] = None
    cleanup_temp: bool = True
    sources: Optional[List[Dict[str, Any]]] = None


def run_pipeline(config: EngineConfig) -> EngineResult:
    """
    Executes the end-to-end PhotoSorter engine:
    Scan -> Detect & Embed (with caching) -> Cluster -> Export Bundle.
    """
    out_dir_str = str(config.output_dir or "export")
    if out_dir_str.startswith("http://") or out_dir_str.startswith("https://") or "drive.google.com" in out_dir_str:
        out_dir_str = "export"
    out_p = Path(out_dir_str).resolve()

    def notify(payload: Dict[str, Any]):
        if config.cancel_check and config.cancel_check():
            raise InterruptedError("Job cancelled by user")
        if config.progress_callback:
            config.progress_callback(payload)

    sources_list: List[Dict[str, Any]] = []
    if config.sources and len(config.sources) > 0:
        for s_idx, s in enumerate(config.sources):
            src_dict = dict(s)
            p_val = str(src_dict.get("path_or_url") or src_dict.get("path") or "").strip()
            src_dict["path_or_url"] = p_val
            k_val = src_dict.get("kind") or src_dict.get("source_type")
            if not k_val:
                k_val = "drive" if is_drive_folder_input(p_val) else ("zip" if p_val.lower().endswith(".zip") else "local")
            src_dict["kind"] = k_val
            src_dict["id"] = src_dict.get("id") or f"src_{s_idx+1:02d}"
            src_dict["status"] = "pending"
            src_dict["photo_count"] = 0
            src_dict["error"] = None
            sources_list.append(src_dict)
    else:
        input_str = str(config.input_path) if config.input_path else ""
        is_drive_input = is_drive_folder_input(input_str)
        s_kind = "drive" if is_drive_input else ("zip" if input_str.lower().endswith(".zip") else "local")
        sources_list.append({
            "id": "src_01",
            "kind": s_kind,
            "path_or_url": input_str,
            "label": None,
            "quality": "original",
            "status": "pending",
            "photo_count": 0,
            "error": None,
        })

    folder_name: Optional[str] = None
    primary_src = sources_list[0]
    p_str = primary_src.get("path_or_url", "")
    if primary_src.get("kind") == "drive" or is_drive_folder_input(p_str):
        try:
            folder_id = parse_drive_folder_id(p_str)
            api_key = config.drive_api_key or get_drive_api_key()
            if api_key:
                client = DriveClient(api_key=api_key)
                folder_name = client.get_folder_name(folder_id)
        except Exception:
            pass
        if not folder_name:
            folder_name = config.event_title if config.event_title and config.event_title not in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery") else "drive"
    elif p_str:
        inp_p = Path(p_str).resolve()
        if inp_p.is_file() and inp_p.suffix.lower() == ".zip":
            folder_name = inp_p.stem
        elif config.event_title and config.event_title not in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery"):
            folder_name = config.event_title
        elif inp_p.is_dir() and inp_p.name and inp_p.name not in (".", ""):
            folder_name = inp_p.name

    if not folder_name:
        folder_name = config.event_title if config.event_title and config.event_title not in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery") else "project"

    safe_project_name = re.sub(r'[\\/*?:"<>|]', "", folder_name).strip() or "project"

    # Temporary project folder named <name>_temp (all temp files saved here and deleted once exported)
    project_temp_p = out_p.parent / f"{safe_project_name}_temp"
    project_temp_p.mkdir(parents=True, exist_ok=True)

    cache_p = Path(config.cache_dir).resolve() if config.cache_dir else project_temp_p
    cache_thumbs_p = cache_p / "thumbs"
    cache_crops_p = cache_p / "crops"
    cache_thumbs_p.mkdir(parents=True, exist_ok=True)
    cache_crops_p.mkdir(parents=True, exist_ok=True)

    scanned_photos: List[ScannedPhoto] = []
    seen_photo_ids: set[str] = set()
    seen_drive_file_ids: set[str] = set()
    failed_sources_count = 0
    total_sources = len(sources_list)
    drive_summary_aggregate = None

    for s_idx, src in enumerate(sources_list):
        s_id = src.get("id") or f"src_{s_idx+1:02d}"
        src["id"] = s_id
        s_path = str(src.get("path_or_url") or src.get("path") or "").strip()
        src["path_or_url"] = s_path
        s_kind = src.get("kind") or src.get("source_type") or ("drive" if is_drive_folder_input(s_path) else ("zip" if s_path.lower().endswith(".zip") else "local"))
        src["kind"] = s_kind
        s_label = src.get("label") or (Path(s_path).name if s_path else f"Source {s_idx+1}")
        src["label"] = s_label

        notify({
            "stage": "scanning",
            "current": s_idx,
            "total": total_sources,
            "percent": round((s_idx / max(1, total_sources)) * 5.0, 1),
            "message": f"Scanning source [{s_idx+1}/{total_sources}]: {s_label}...",
        })

        if s_kind == "drive" or is_drive_folder_input(s_path):
            try:
                folder_id = parse_drive_folder_id(s_path)
                api_key = config.drive_api_key or get_drive_api_key()
                if not api_key:
                    raise DriveAuthError(
                        "Google Drive API key is required. Please set it in Settings or set the DRIVE_API_KEY environment variable."
                    )
                client = DriveClient(api_key=api_key)
                src_folder_name = client.get_folder_name(folder_id) or s_label
                drive_cache_p = cache_p / "photos"
                drive_cache_p.mkdir(parents=True, exist_ok=True)

                list_res = client.list_folder_images(
                    folder_id=folder_id,
                    cancel_check=config.cancel_check,
                    progress_callback=notify,
                    recursive=config.scan_subfolders,
                    max_depth=config.max_subfolder_depth,
                    include_shortcuts=config.follow_shortcuts,
                )
                if list_res.image_count == 0 and total_sources == 1:
                    raise ValueError(f"No image files found in Google Drive folder '{folder_id}'.")

                drive_summary_aggregate = list_res.summary

                downloaded_items = client.download_thumbnails(
                    files=list_res.files,
                    cache_dir=drive_cache_p,
                    progress_callback=lambda p: notify({**p, "percent": min(5.0, round(1.0 + (p.get("current", 0) / max(1, list_res.image_count)) * 4.0, 1))}),
                    cancel_check=config.cancel_check,
                )

                src_count = 0
                for df, local_p in downloaded_items:
                    photo_id = compute_file_hash(local_p)
                    if photo_id in seen_photo_ids or df.id in seen_drive_file_ids:
                        continue
                    seen_photo_ids.add(photo_id)
                    seen_drive_file_ids.add(df.id)
                    rel_display_path = f"{df.folder_path}/{df.name}" if getattr(df, "folder_path", "") else df.name
                    scanned_photos.append(
                        ScannedPhoto(
                            photo_id=photo_id,
                            file_path=local_p,
                            file_name=df.name,
                            relative_path=rel_display_path,
                            download_url=df.download_url,
                            drive_file_id=df.id,
                            drive_url=getattr(df, "drive_url", f"https://drive.google.com/file/d/{df.id}/view"),
                            share_url=getattr(df, "share_url", f"https://drive.google.com/file/d/{df.id}/view?usp=sharing"),
                            source_id=s_id,
                            source_label=s_label,
                        )
                    )
                    src_count += 1
                src["status"] = "completed"
                src["photo_count"] = src_count
            except Exception as e:
                src["status"] = "failed"
                src["error"] = str(e)
                failed_sources_count += 1
                if total_sources == 1:
                    raise e
        else:
            try:
                if not s_path:
                    raise ValueError(f"Source '{s_label}' has empty or unspecified path.")
                input_p = Path(s_path).resolve()
                if not input_p.exists():
                    raise FileNotFoundError(f"Input path does not exist: {input_p}")
                with PhotoScanner(input_p, temp_dir=cache_p / "photos") as scanner:
                    scanned = scanner.scan(
                        scan_subfolders=config.scan_subfolders,
                        max_subfolder_depth=config.max_subfolder_depth,
                        follow_shortcuts=config.follow_shortcuts,
                    )
                    src_count = 0
                    for item in scanned:
                        if item.photo_id in seen_photo_ids:
                            continue
                        seen_photo_ids.add(item.photo_id)
                        item.source_id = s_id
                        item.source_label = s_label
                        scanned_photos.append(item)
                        src_count += 1
                    src["status"] = "completed"
                    src["photo_count"] = src_count
            except Exception as e:
                src["status"] = "failed"
                src["error"] = str(e)
                failed_sources_count += 1
                if total_sources == 1:
                    raise e

    total_photos = len(scanned_photos)
    if total_photos == 0:
        errs = [f"{s.get('label', s.get('path_or_url'))}: {s.get('error', 'no images found')}" for s in sources_list]
        raise ValueError(f"No valid photos found across {total_sources} source(s): {'; '.join(errs)}")

    notify({
        "stage": "scanned",
        "current": 0,
        "total": total_photos,
        "percent": 5.0,
        "message": f"Found {total_photos} photos across {total_sources - failed_sources_count} active source(s).",
    })

    # 2. Setup Cache, Loader, Detector, and Thumb Generator
    from backend.engine.cache import EmbeddingCache, compute_settings_hash
    settings_hash = compute_settings_hash(
        model_name="buffalo_l",
        det_size=(640, 640),
        min_det_score=config.min_det_score,
        min_face_size=config.min_face_size,
        max_yaw=config.max_yaw,
        max_image_dim=config.max_image_dim,
        flip_average=config.flip_average,
    )
    cache = EmbeddingCache(cache_p, settings_hash=settings_hash)
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
                if getattr(item, "relative_path", None):
                    record.relative_path = item.relative_path
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
                    "percent": 5.0,
                    "message": "Initializing InsightFace model...",
                })
                def on_detector_progress(p: Dict[str, Any]):
                    # Scale model download smoothly between 0.0% and 5.0%
                    p_pct = p.get("percent", 0.0)
                    scaled_pct = round((p_pct / 100.0) * 5.0, 1)
                    notify({
                        **p,
                        "percent": scaled_pct,
                    })

                detector = FaceDetector(
                    model_name="buffalo_l",
                    model_root=config.model_root,
                    min_det_score=config.min_det_score,
                    min_face_size=config.min_face_size,
                    max_yaw=config.max_yaw,
                    max_image_dim=config.max_image_dim,
                    progress_callback=on_detector_progress,
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
                relative_path=getattr(item, "relative_path", item.file_name),
                faces=faces,
                source_id=getattr(item, "source_id", None),
                source_label=getattr(item, "source_label", None),
            )
            cache.save(record)
            photos[photo_id] = record

        # Compute ETA
        elapsed = time.time() - start_time
        processed = idx + 1
        avg_per_photo = elapsed / processed
        eta_seconds = (total_photos - processed) * avg_per_photo

        # Processing (reading faces) takes up 5% to 65% (60% of total bar)
        pct = round(5.0 + (processed / total_photos) * 60.0, 1) if total_photos > 0 else 5.0
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
        notify({"stage": "flip_averaging", "current": total_photos, "total": total_photos, "percent": 68.0, "message": "Applying flip-averaged embeddings..."})
        for photo in photos.values():
            for face in photo.faces:
                if face.embedding_flipped is not None:
                    face.embedding = face.embedding_flipped

    notify({"stage": "clustering", "current": total_photos, "total": total_photos, "percent": 72.0, "message": "Clustering faces by person with second-pass merge..."})
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
    unapplied = []
    if config.replay_edits and edits_path.exists():
        notify({"stage": "applying_edits", "percent": 84.0, "message": f"Applying organizer edits from {edits_path}..."})
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
            "percent": 86.0,
            "applied": edit_stats.get("applied", 0),
            "unapplied": len(unapplied),
            "unapplied_edits": unapplied,
            "message": f"Applied {edit_stats.get('applied', 0)} edits ({len(unapplied)} unapplied).",
        })

    source_title = None
    is_drive = primary_src.get("kind") == "drive" or is_drive_folder_input(primary_src.get("path_or_url", ""))
    if is_drive:
        source_title = folder_name
    elif config.input_path:
        p = Path(config.input_path)
        if p.is_file() and p.suffix.lower() == ".zip":
            source_title = p.stem
        elif p.is_dir() or p.name:
            source_title = p.name

    result = EngineResult(
        photos=photos,
        people=people,
        unrecognized=unrecognized,
        distance_threshold=config.distance_threshold,
        id_map=clusterer.id_map,
        temp_dir=str(project_temp_p),
        drive_folder_name=folder_name if (primary_src.get("kind") == "drive" or is_drive_folder_input(primary_src.get("path_or_url", ""))) else None,
        source_title=source_title,
        unapplied_edits=unapplied,
        drive_summary=drive_summary_aggregate,
        sources=sources_list,
    )

    notify({
        "stage": "clustered",
        "percent": 82.0,
        "people_count": len(people),
        "unrecognized_photos": len(unrecognized.photo_ids),
        "unrecognized_faces": len(unrecognized.faces),
        "maybe_groups_count": len(clusterer.maybe_groups),
        "message": f"Formed {len(people)} people clusters ({len(clusterer.maybe_groups)} connected maybe groups). {len(unrecognized.photo_ids)} photos in Unrecognized.",
    })

    # 5. Export Bundle
    export_title = config.event_title
    if (not export_title or export_title in ("CatLog Gallery", "Face Clubbing Gallery", "Event Gallery")) and source_title:
        export_title = source_title

    notify({"stage": "exporting", "current": total_photos, "total": total_photos, "percent": 88.0, "message": f"Generating static export bundle in {out_p}..."})
    exporter = BundleExporter(
        output_dir=out_p,
        cache_dir=cache_p,
        thumb_size=config.thumb_size,
        face_crop_size=config.face_crop_size,
    )
    exported_out = exporter.export(
        result=result,
        title=export_title or "CatLog Gallery",
        subtitle=config.event_subtitle,
        config_override={"include_maybe": config.include_maybe},
        include_maybe=config.include_maybe,
        cleanup_temp=config.cleanup_temp,
    )
    result.export_dir = str(exported_out)

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


def run_incremental_pipeline(
    config: EngineConfig,
    new_source: Dict[str, Any],
    work_dir: Optional[Path | str] = None,
    export_dir: Optional[Path | str] = None,
    frozen_mode: bool = True,
    existing_result: Optional[EngineResult] = None,
) -> Tuple[EngineResult, Dict[str, Any]]:
    """
    Executes an incremental ingestion pipeline for a new source into an existing project.

    Workflow:
    1. Creates an atomic snapshot in work_dir/snapshots for instant undo.
    2. Loads existing people, unrecognized, photos, manifest, and cached embeddings.
    3. Scans ONLY the new source, automatically deduplicating against existing photos.
    4. Detects and embeds faces ONLY for new photos.
    5. Executes FaceClusterer.cluster_incremental in frozen mode (0 pre-existing membership change).
    6. Replays existing organizer edits (edits.json) to preserve custom names and manual assignments.
    7. Updates manifest.json (sources + photo_origins) and writes what_changed.json.
    8. Exports updated people.json and newly generated thumbnails/crops.
    9. Returns (updated_result, what_changed_report).
    """
    from backend.engine.snapshots import create_snapshot
    from backend.engine.models import PersonCluster, UnrecognizedGroup, PhotoRecord, FaceDetection
    from backend.engine.cache import EmbeddingCache, compute_settings_hash
    from backend.engine.thumbnails import ThumbnailGenerator

    out_p = Path(export_dir or config.output_dir or "export").resolve()
    work_p = Path(work_dir or config.cache_dir or "export.work").resolve()
    cache_p = Path(config.cache_dir).resolve() if config.cache_dir else work_p
    cache_thumbs_p = cache_p / "thumbs"
    cache_crops_p = cache_p / "crops"
    cache_thumbs_p.mkdir(parents=True, exist_ok=True)
    cache_crops_p.mkdir(parents=True, exist_ok=True)

    def notify(payload: Dict[str, Any]):
        if config.cancel_check and config.cancel_check():
            raise InterruptedError("Job cancelled by user")
        if config.progress_callback:
            config.progress_callback(payload)

    # 1. Snapshot creation for instant rollback
    notify({"stage": "snapshot", "percent": 2.0, "message": "Creating project snapshot before incremental scan..."})
    snap_meta = create_snapshot(
        work_dir=work_p,
        export_dir=out_p,
        label=f"Before adding {new_source.get('label') or new_source.get('path_or_url')}",
    )

    # 2. Load existing state
    existing_people: List[PersonCluster] = []
    existing_unrec: UnrecognizedGroup = UnrecognizedGroup(photo_ids=[], faces=[])
    existing_photos: Dict[str, PhotoRecord] = {}
    existing_sources: List[Dict[str, Any]] = []
    existing_origins: Dict[str, str] = {}

    settings_hash = compute_settings_hash(
        model_name="buffalo_l",
        det_size=(640, 640),
        min_det_score=config.min_det_score,
        min_face_size=config.min_face_size,
        max_yaw=config.max_yaw,
        max_image_dim=config.max_image_dim,
        flip_average=config.flip_average,
    )
    cache = EmbeddingCache(cache_p, settings_hash=settings_hash)

    if existing_result:
        existing_people = [
            PersonCluster(
                id=p.id,
                label=p.label,
                face_path=p.face_path,
                rep_face=p.rep_face,
                photo_ids=list(p.photo_ids),
                faces=list(p.faces),
                maybe_photos=list(p.maybe_photos),
                merged_from=list(p.merged_from),
                merged_from_numbering=p.merged_from_numbering,
            )
            for p in existing_result.people
        ]
        existing_unrec = UnrecognizedGroup(
            photo_ids=list(existing_result.unrecognized.photo_ids),
            faces=list(existing_result.unrecognized.faces),
        )
        existing_photos = dict(existing_result.photos)
        existing_sources = list(existing_result.sources or [])
    else:
        # Load from disk
        pj_candidates = [work_p / "people.json", out_p / "people.json"]
        loaded_pj = None
        for cand in pj_candidates:
            if cand.is_file():
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        loaded_pj = json.load(f)
                    break
                except Exception:
                    pass

        if loaded_pj:
            for p_dict in loaded_pj.get("people", []):
                p_faces = []
                # Attempt to retrieve face objects from cache if photo records exist
                p_pids = p_dict.get("photos") or p_dict.get("photo_ids", [])
                for pid in p_pids:
                    rec = cache.get(pid)
                    if rec:
                        existing_photos[pid] = rec
                        p_faces.extend(rec.faces)

                if not p_faces:
                    for pid in p_pids:
                        f_dummy = FaceDetection(
                            face_id=f"f_{pid}_01",
                            photo_id=pid,
                            bbox=[10.0, 10.0, 90.0, 90.0],
                            det_score=0.90,
                            embedding=np.zeros(512, dtype=np.float32),
                        )
                        f_dummy.embedding[0] = 1.0
                        p_faces.append(f_dummy)
                        if pid not in existing_photos:
                            existing_photos[pid] = PhotoRecord(
                                photo_id=pid,
                                original_path="",
                                file_name=f"{pid}.jpg",
                                width=1000,
                                height=1000,
                                faces=[f_dummy],
                            )

                # Find representative face object if available
                rep_face_obj = p_faces[0] if p_faces else None

                cluster = PersonCluster(
                    id=p_dict["id"],
                    label=p_dict.get("name") or p_dict.get("label"),
                    face_path=p_dict.get("face", f"faces/{p_dict['id']}.jpg"),
                    rep_face=rep_face_obj,
                    photo_ids=list(p_pids),
                    faces=p_faces,
                    maybe_photos=p_dict.get("maybe_photos", []),
                    merged_from=p_dict.get("merged_from", []),
                    merged_from_numbering=p_dict.get("merged_from_numbering", ""),
                )
                existing_people.append(cluster)

            unrec_data = loaded_pj.get("unrecognized", {})
            existing_unrec = UnrecognizedGroup(
                photo_ids=unrec_data.get("photo_ids", []),
                faces=unrec_data.get("faces", []),
            )

        # Load manifest
        mf_candidates = [work_p / "manifest.json", out_p / "manifest.json"]
        for cand in mf_candidates:
            if cand.is_file():
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                    existing_sources = m_data.get("sources", [])
                    existing_origins = m_data.get("photo_origins", {})
                    break
                except Exception:
                    pass

    # 3. Clean new source parameters
    s_path = str(new_source.get("path_or_url") or new_source.get("path") or "").strip()
    s_kind = new_source.get("kind") or ("drive" if is_drive_folder_input(s_path) else ("zip" if s_path.lower().endswith(".zip") else "local"))
    s_id = new_source.get("id") or f"src_{len(existing_sources)+1:02d}"
    s_label = new_source.get("label") or (Path(s_path).name if s_path else f"Source {len(existing_sources)+1}")

    new_source_clean = {
        "id": s_id,
        "kind": s_kind,
        "path_or_url": s_path,
        "label": s_label,
        "quality": "original",
        "status": "scanning",
        "photo_count": 0,
        "error": None,
        "added_at": datetime.datetime.now().astimezone().isoformat(),
    }

    notify({"stage": "scanning", "percent": 5.0, "message": f"Scanning new source '{s_label}'..."})

    # 4. Scan new source & Deduplicate
    scanned_photos: List[ScannedPhoto] = []
    seen_new_ids: set[str] = set()
    skipped_duplicates = 0

    if s_kind == "drive" or is_drive_folder_input(s_path):
        folder_id = parse_drive_folder_id(s_path)
        api_key = config.drive_api_key or get_drive_api_key()
        if not api_key:
            raise DriveAuthError("Google Drive API key is required to scan Drive folder.")
        client = DriveClient(api_key=api_key)
        drive_cache_p = cache_p / "photos"
        drive_cache_p.mkdir(parents=True, exist_ok=True)

        list_res = client.list_folder_images(
            folder_id=folder_id,
            cancel_check=config.cancel_check,
            progress_callback=notify,
            recursive=config.scan_subfolders,
            max_depth=config.max_subfolder_depth,
            include_shortcuts=config.follow_shortcuts,
        )
        downloaded = client.download_thumbnails(
            files=list_res.files,
            cache_dir=drive_cache_p,
            progress_callback=lambda p: notify({**p, "percent": min(15.0, round(5.0 + (p.get("current", 0) / max(1, list_res.image_count)) * 10.0, 1))}),
            cancel_check=config.cancel_check,
        )
        for df, local_p in downloaded:
            pid = compute_file_hash(local_p)
            if pid in existing_photos or pid in seen_new_ids:
                skipped_duplicates += 1
                continue
            seen_new_ids.add(pid)
            rel_display_path = f"{df.folder_path}/{df.name}" if getattr(df, "folder_path", "") else df.name
            scanned_photos.append(
                ScannedPhoto(
                    photo_id=pid,
                    file_path=local_p,
                    file_name=df.name,
                    relative_path=rel_display_path,
                    download_url=df.download_url,
                    drive_file_id=df.id,
                    drive_url=getattr(df, "drive_url", f"https://drive.google.com/file/d/{df.id}/view"),
                    share_url=getattr(df, "share_url", f"https://drive.google.com/file/d/{df.id}/view?usp=sharing"),
                    source_id=s_id,
                    source_label=s_label,
                )
            )
    else:
        input_p = Path(s_path).resolve()
        if not input_p.exists():
            raise FileNotFoundError(f"Source path does not exist: {input_p}")
        with PhotoScanner(input_p, temp_dir=cache_p / "photos") as scanner:
            scanned = scanner.scan(
                scan_subfolders=config.scan_subfolders,
                max_subfolder_depth=config.max_subfolder_depth,
                follow_shortcuts=config.follow_shortcuts,
            )
            for item in scanned:
                if item.photo_id in existing_photos or item.photo_id in seen_new_ids:
                    skipped_duplicates += 1
                    continue
                seen_new_ids.add(item.photo_id)
                item.source_id = s_id
                item.source_label = s_label
                scanned_photos.append(item)

    new_source_clean["photo_count"] = len(scanned_photos)
    new_source_clean["status"] = "completed"

    notify({
        "stage": "scanned",
        "percent": 18.0,
        "message": f"Found {len(scanned_photos)} new photos ({skipped_duplicates} duplicate photos skipped).",
    })

    # 5. Detect and Embed ONLY New Photos
    loader = ImageLoader(max_dimension=config.max_image_dim)
    thumb_gen = ThumbnailGenerator(thumb_size=config.thumb_size, face_crop_size=config.face_crop_size)
    detector: Optional[FaceDetector] = None

    new_photos: Dict[str, PhotoRecord] = {}
    total_new = len(scanned_photos)
    start_time = time.time()

    for idx, item in enumerate(scanned_photos):
        if config.cancel_check and config.cancel_check():
            raise InterruptedError("Job cancelled by user")
        pid = item.photo_id

        if cache.has(pid):
            record = cache.get(pid)
            if record:
                record.original_path = str(item.file_path)
                record.file_name = item.file_name
                record.source_id = s_id
                record.source_label = s_label
                new_photos[pid] = record
        else:
            if detector is None:
                detector = FaceDetector(
                    model_name="buffalo_l",
                    model_root=config.model_root,
                    min_det_score=config.min_det_score,
                    min_face_size=config.min_face_size,
                    max_yaw=config.max_yaw,
                    max_image_dim=config.max_image_dim,
                )

            rgb_img, orig_w, orig_h, pil_img = loader.load_image(item.file_path)
            faces = detector.detect_and_embed(orig_rgb=rgb_img, photo_id=pid)

            # Pre-generate and cache photo thumbnail & crops
            cached_thumb = cache_thumbs_p / f"{pid}.jpg"
            if not cached_thumb.exists():
                thumb_gen.generate_photo_thumbnail_from_image(pil_img, cached_thumb)
            for f in faces:
                cached_crop = cache_crops_p / f"{f.face_id}.jpg"
                if not cached_crop.exists():
                    thumb_gen.generate_square_face_crop_from_image(pil_img, f.bbox, cached_crop)

            del rgb_img, pil_img
            gc.collect()

            record = PhotoRecord(
                photo_id=pid,
                original_path=str(item.file_path),
                file_name=item.file_name,
                width=orig_w,
                height=orig_h,
                download_url=getattr(item, "download_url", None),
                drive_file_id=getattr(item, "drive_file_id", None),
                drive_url=getattr(item, "drive_url", None),
                share_url=getattr(item, "share_url", None),
                relative_path=getattr(item, "relative_path", item.file_name),
                faces=faces,
                source_id=s_id,
                source_label=s_label,
            )
            cache.save(record)
            new_photos[pid] = record

        processed = idx + 1
        pct = round(20.0 + (processed / max(1, total_new)) * 50.0, 1)
        notify({
            "stage": "processing",
            "current": processed,
            "total": total_new,
            "percent": pct,
            "photo_id": pid,
            "file_name": item.file_name,
            "message": f"[{processed}/{total_new}] Ingesting {item.file_name} ({len(new_photos[pid].faces)} faces)",
        })

    # 6. Incremental Clustering under Frozen Mode
    notify({"stage": "clustering", "percent": 75.0, "message": "Clustering new faces into project (frozen mode)..."})
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

    updated_people, updated_unrec, diff_report = clusterer.cluster_incremental(
        existing_people=existing_people,
        existing_unrecognized=existing_unrec,
        existing_photos=existing_photos,
        new_photos=new_photos,
        frozen_mode=frozen_mode,
    )

    diff_report["skipped_duplicate_photos"] = skipped_duplicates
    diff_report["source_id"] = s_id
    diff_report["source_label"] = s_label

    # 7. Edit Replay (SPEC 6.3)
    edits_path = work_p / "edits.json"
    unapplied = []
    all_combined_photos = {**existing_photos, **new_photos}
    if config.replay_edits and edits_path.exists():
        notify({"stage": "applying_edits", "percent": 82.0, "message": f"Replaying organizer edits from {edits_path}..."})
        try:
            with open(edits_path, "r", encoding="utf-8") as f:
                edits_data = json.load(f)
            from backend.engine.edits import apply_edits
            updated_people, updated_unrec, unapplied, edit_stats = apply_edits(
                updated_people, updated_unrec, edits_data, all_combined_photos
            )
        except Exception as e:
            print(f"[run_incremental_pipeline] Warning: Edit replay failed: {e}")

    # 8. Update Project Manifest v2
    all_sources = list(existing_sources) + [new_source_clean]
    for pid in new_photos:
        existing_origins[pid] = s_id

    manifest_path_work = work_p / "manifest.json"
    manifest_path_exp = out_p / "manifest.json"
    manifest_payload = {
        "schema_version": 2,
        "project_name": getattr(config, "event_title", None) or "Project",
        "created_at": datetime.datetime.now().astimezone().isoformat(),
        "updated_at": datetime.datetime.now().astimezone().isoformat(),
        "sources": all_sources,
        "total_photos": len(all_combined_photos),
        "total_people": len(updated_people),
        "photo_origins": existing_origins,
    }
    for m_path in [manifest_path_work, manifest_path_exp]:
        try:
            m_path.parent.mkdir(parents=True, exist_ok=True)
            with open(m_path, "w", encoding="utf-8") as f:
                json.dump(manifest_payload, f, indent=2)
        except Exception:
            pass

    # 9. Write what_changed.json
    for wc_p in [work_p / "what_changed.json", out_p / "what_changed.json"]:
        try:
            wc_p.parent.mkdir(parents=True, exist_ok=True)
            with open(wc_p, "w", encoding="utf-8") as f:
                json.dump(diff_report, f, indent=2)
        except Exception:
            pass

    # 10. Bundle Export Update
    notify({"stage": "exporting", "percent": 88.0, "message": "Updating export bundle and thumbnails..."})
    result = EngineResult(
        photos=all_combined_photos,
        people=updated_people,
        unrecognized=updated_unrec,
        distance_threshold=config.distance_threshold,
        id_map=clusterer.id_map,
        sources=all_sources,
        unapplied_edits=unapplied,
        export_dir=str(out_p),
    )

    exporter = BundleExporter(
        output_dir=out_p,
        cache_dir=cache_p,
        thumb_size=config.thumb_size,
        face_crop_size=config.face_crop_size,
    )
    exported_out = exporter.export(
        result=result,
        title=config.event_title or "CatLog Gallery",
        subtitle=config.event_subtitle,
        config_override={"include_maybe": config.include_maybe},
        include_maybe=config.include_maybe,
        cleanup_temp=False,
    )
    result.export_dir = str(exported_out)

    # Copy people.json to work_p as well
    if (out_p / "people.json").is_file():
        try:
            shutil.copy2(out_p / "people.json", work_p / "people.json")
        except Exception:
            pass

    # 11. Auto-save project entry in projects.json
    try:
        from backend.api.projects import save_recent_project
        save_recent_project(
            work_dir=work_p,
            export_path=out_p,
            counts={"people": len(updated_people), "photos": len(all_combined_photos)},
            sources=all_sources,
            schema_version=2,
        )
    except Exception as e:
        print(f"[run_incremental_pipeline] Warning: Failed to update recent project: {e}")

    notify({
        "stage": "complete",
        "percent": 100.0,
        "message": f"Incremental addition complete! Added {len(new_photos)} photos, formed {len(diff_report['new_people_ids'])} new people.",
    })

    return result, diff_report

