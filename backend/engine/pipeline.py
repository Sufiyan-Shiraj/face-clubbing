"""Orchestrates the full PhotoSorter engine pipeline."""

from __future__ import annotations
import gc
import json
import datetime
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
import numpy as np

from backend.engine.models import EngineResult, PhotoRecord
from backend.engine.scanner import PhotoScanner
from backend.engine.loader import ImageLoader
from backend.engine.cache import EmbeddingCache
from backend.engine.detector import FaceDetector
from backend.engine.clusterer import FaceClusterer
from backend.engine.exporter import BundleExporter


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
    flip_average: bool = False
    include_maybe: bool = False
    suggestions_path: Optional[str | Path] = None
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None


def run_pipeline(config: EngineConfig) -> EngineResult:
    """
    Executes the end-to-end PhotoSorter engine:
    Scan -> Detect & Embed (with caching) -> Cluster -> Export Bundle.
    """
    input_p = Path(config.input_path).resolve()
    out_p = Path(config.output_dir).resolve()
    cache_p = Path(config.cache_dir).resolve() if config.cache_dir else out_p.parent / f"{out_p.name}.work"
    cache_thumbs_p = cache_p / "thumbs"
    cache_crops_p = cache_p / "crops"
    cache_thumbs_p.mkdir(parents=True, exist_ok=True)
    cache_crops_p.mkdir(parents=True, exist_ok=True)

    def notify(payload: Dict[str, Any]):
        if config.progress_callback:
            config.progress_callback(payload)

    # 1. Scan photos
    notify({"stage": "scanning", "message": f"Scanning input: {input_p}"})
    with PhotoScanner(input_p) as scanner:
        scanned_photos = scanner.scan()
        total_photos = len(scanned_photos)
        if total_photos == 0:
            raise ValueError(f"No supported photos found in: {input_p}")

        notify({
            "stage": "scanned",
            "total": total_photos,
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
            photo_id = item.photo_id

            if cache.has(photo_id):
                record = cache.get(photo_id)
                if record:
                    record.original_path = str(item.file_path)
                    record.file_name = item.file_name
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
                    notify({"stage": "model_init", "message": "Initializing InsightFace model..."})
                    detector = FaceDetector(
                        model_name="buffalo_l",
                        min_det_score=config.min_det_score,
                        min_face_size=config.min_face_size,
                        max_yaw=config.max_yaw,
                        max_image_dim=config.max_image_dim,
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
                    download_url=None,
                    faces=faces,
                )
                cache.save(record)
                photos[photo_id] = record

            # Compute ETA
            elapsed = time.time() - start_time
            processed = idx + 1
            avg_per_photo = elapsed / processed
            eta_seconds = (total_photos - processed) * avg_per_photo

            notify({
                "stage": "processing",
                "current": processed,
                "total": total_photos,
                "photo_id": photo_id,
                "file_name": item.file_name,
                "faces_found": len(photos[photo_id].faces),
                "eta_seconds": round(eta_seconds, 1),
                "message": f"[{processed}/{total_photos}] {item.file_name} ({len(photos[photo_id].faces)} faces)",
            })

        # 4. Clustering (with optional flip_average)
        if config.flip_average:
            notify({"stage": "flip_averaging", "message": "Applying flip-averaged embeddings..."})
            for photo in photos.values():
                for face in photo.faces:
                    if face.embedding_flipped is not None:
                        face.embedding = face.embedding_flipped

        notify({"stage": "clustering", "message": "Clustering faces by person with second-pass merge..."})
        clusterer = FaceClusterer(
            distance_threshold=config.distance_threshold,
            seed_min_face_size=config.seed_min_face_size or config.min_face_size,
            seed_max_yaw=config.seed_max_yaw,
            seed_min_det_score=config.seed_min_det_score,
            second_pass_merge=config.second_pass_merge,
            merge_threshold=config.merge_threshold,
            maybe_threshold=config.maybe_threshold,
            same_photo_merge_max=config.same_photo_merge_max,
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
        notify({"stage": "exporting", "message": f"Generating static export bundle in {out_p}..."})
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
            "message": "Export complete!",
            "output_dir": str(out_p),
            "people_count": len(people),
        })

        return result
