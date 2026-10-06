"""Exports the engine results into the static viewer bundle according to the SPEC schema."""

from __future__ import annotations
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import shutil
from backend.engine.models import EngineResult, PersonCluster, UnrecognizedGroup
from backend.engine.thumbnails import ThumbnailGenerator, select_representative_face


class BundleExporter:
    """Exports people.json, config.json, thumbs/, and faces/."""

    def __init__(
        self,
        output_dir: Path | str,
        cache_dir: Optional[Path | str] = None,
        thumb_size: int = 400,
        face_crop_size: int = 256,
    ):
        self.output_dir = Path(output_dir).resolve()
        self.cache_dir = Path(cache_dir).resolve() if cache_dir else None
        self.thumbs_dir = self.output_dir / "thumbs"
        self.faces_dir = self.output_dir / "faces"
        self.thumb_gen = ThumbnailGenerator(thumb_size=thumb_size, face_crop_size=face_crop_size)

    def export(
        self,
        result: EngineResult,
        title: str = "Event Gallery",
        subtitle: str = "Grouped by Person",
        config_override: Optional[Dict[str, Any]] = None,
        include_maybe: Optional[bool] = None,
    ) -> Path:
        """
        Creates the complete export bundle.

        Returns:
            Path to the output directory.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.faces_dir.mkdir(parents=True, exist_ok=True)

        cache_thumbs = self.cache_dir / "thumbs" if self.cache_dir else None
        cache_crops = self.cache_dir / "crops" if self.cache_dir else None

        # 1. Generate Photo Thumbnails and build photos dict for people.json
        photos_json: Dict[str, Any] = {}
        for photo_id, record in result.photos.items():
            thumb_rel = f"thumbs/{photo_id}.jpg"
            thumb_dest = self.output_dir / thumb_rel

            # Use cached thumbnail if present
            if not thumb_dest.exists():
                cached_thumb = cache_thumbs / f"{photo_id}.jpg" if cache_thumbs else None
                if cached_thumb and cached_thumb.exists():
                    shutil.copy2(cached_thumb, thumb_dest)
                else:
                    self.thumb_gen.generate_photo_thumbnail(
                        image_path=record.original_path,
                        output_path=thumb_dest,
                    )

            photos_json[photo_id] = {
                "name": record.file_name,
                "thumb": thumb_rel,
                "download": record.download_url,
                "width": record.width,
                "height": record.height,
            }

        # 2. Process People Clusters and generate representative square face crops
        people_json = []
        for person in result.people:
            # Pick representative face if not assigned
            if person.rep_face is None:
                person.rep_face = select_representative_face(person.faces)

            face_rel = f"faces/{person.id}.jpg"
            face_dest = self.output_dir / face_rel

            # Copy from crop cache if present, else crop from original image
            cached_crop = cache_crops / f"{person.rep_face.face_id}.jpg" if cache_crops else None
            if cached_crop and cached_crop.exists():
                shutil.copy2(cached_crop, face_dest)
            else:
                orig_photo = result.photos[person.rep_face.photo_id]
                self.thumb_gen.generate_square_face_crop(
                    image_path=orig_photo.original_path,
                    bbox=person.rep_face.bbox,
                    output_path=face_dest,
                )

            # Determine include_maybe flag
            should_include_maybe = False
            if include_maybe is not None:
                should_include_maybe = include_maybe
            elif config_override and "include_maybe" in config_override:
                should_include_maybe = bool(config_override["include_maybe"])

            people_json.append({
                "id": person.id,
                "label": person.label,
                "face": face_rel,
                "photo_ids": person.photo_ids,
                "photos": person.photo_ids,
                "faces": [
                    {
                        "face_id": f.face_id,
                        "photo_id": f.photo_id,
                        "file_name": result.photos[f.photo_id].file_name,
                        "det_score": round(float(f.det_score), 4),
                        "bbox": f.bbox,
                    }
                    for f in person.faces
                ],
                "merged_from": person.merged_from if person.merged_from else [person.id],
                "merged_from_numbering": person.merged_from_numbering if person.merged_from_numbering else f"pre-merge {len(result.people)}",
                "maybe_photos": [
                    {
                        "photo_id": m["photo_id"],
                        "source_cluster": m["source_cluster"],
                        "distance": round(float(m["distance"]), 4),
                    }
                    for m in person.maybe_photos
                ] if should_include_maybe else [],
            })

        # 3. Process Unrecognized group face crops
        unrecognized_faces_json = []
        internal_unrec_items = getattr(result.unrecognized, "_face_items", [])
        for item in internal_unrec_items:
            face_obj = item["face_obj"]
            face_rel = item["face"]
            face_dest = self.output_dir / face_rel

            cached_crop = cache_crops / f"{face_obj.face_id}.jpg" if cache_crops else None
            if cached_crop and cached_crop.exists():
                shutil.copy2(cached_crop, face_dest)
            else:
                orig_photo = result.photos[face_obj.photo_id]
                self.thumb_gen.generate_square_face_crop(
                    image_path=orig_photo.original_path,
                    bbox=face_obj.bbox,
                    output_path=face_dest,
                )
            unrecognized_faces_json.append({
                "face_id": face_obj.face_id,
                "photo_id": item["photo_id"],
                "file_name": result.photos[face_obj.photo_id].file_name,
                "face": face_rel,
                "rejection_reason": face_obj.rejection_reason,
                "det_score": round(float(face_obj.det_score), 4),
            })

        # 4. Generate people.json
        now_iso = datetime.datetime.now().astimezone().isoformat()
        people_payload = {
            "version": 1,
            "generated_at": now_iso,
            "photos": photos_json,
            "people": people_json,
            "unrecognized": {
                "photo_ids": result.unrecognized.photo_ids,
                "faces": unrecognized_faces_json if unrecognized_faces_json else result.unrecognized.faces,
            },
        }

        people_path = self.output_dir / "people.json"
        with open(people_path, "w", encoding="utf-8") as f:
            json.dump(people_payload, f, indent=2)

        # 5. Generate config.json (preserve existing if present and not overridden)
        config_path = self.output_dir / "config.json"
        if not config_path.exists() or config_override:
            default_config = {
                "title": title,
                "subtitle": subtitle,
                "logo": None,
                "accent": "#2563eb",
                "font": "Inter",
                "footer": "Published with PhotoSorter",
                "show_labels": True,
                "include_maybe": False,
                "hide_single_photo_default": False,
            }
            if config_override:
                default_config.update(config_override)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)

        # 6. Verify Bundle Integrity
        self._verify_bundle(people_payload)
        return self.output_dir

    def _verify_bundle(self, people_payload: Dict[str, Any]) -> None:
        """Validates that the export conforms to the specification."""
        all_photos = set(people_payload["photos"].keys())
        covered_photos = set(people_payload["unrecognized"]["photo_ids"])
        for p in people_payload["people"]:
            covered_photos.update(p["photo_ids"])

        unaccounted = all_photos - covered_photos
        if unaccounted:
            raise ValueError(
                f"Export verification failed: {len(unaccounted)} photos are unaccounted for: {unaccounted}"
            )
