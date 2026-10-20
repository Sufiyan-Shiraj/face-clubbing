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
        out_dir_str = str(output_dir or "export")
        if out_dir_str.startswith("http://") or out_dir_str.startswith("https://") or "drive.google.com" in out_dir_str:
            out_dir_str = "export"
        self.output_dir = Path(out_dir_str).resolve()
        self.cache_dir = Path(cache_dir).resolve() if cache_dir else None
        self.thumbs_dir = self.output_dir / "thumbs"
        self.faces_dir = self.output_dir / "faces"
        self.thumb_gen = ThumbnailGenerator(thumb_size=thumb_size, face_crop_size=face_crop_size)

    def _resolve_thumb(self, photo_id: str, record: PhotoRecord, thumb_dest: Path, cache_thumbs: Optional[Path]) -> None:
        if thumb_dest.exists():
            return
        if cache_thumbs and (cache_thumbs / f"{photo_id}.jpg").exists():
            shutil.copy2(cache_thumbs / f"{photo_id}.jpg", thumb_dest)
            return
        if self.cache_dir and (self.cache_dir / "thumbs" / f"{photo_id}.jpg").exists():
            shutil.copy2(self.cache_dir / "thumbs" / f"{photo_id}.jpg", thumb_dest)
            return
        if self.cache_dir:
            sibling_base = self.cache_dir.name.removesuffix(".work")
            cand1 = self.cache_dir.parent / sibling_base / "thumbs" / f"{photo_id}.jpg"
            if cand1.exists():
                shutil.copy2(cand1, thumb_dest)
                return
            cand2 = self.cache_dir.parent / f"{sibling_base}.work" / "thumbs" / f"{photo_id}.jpg"
            if cand2.exists():
                shutil.copy2(cand2, thumb_dest)
                return
        # Also check root export.work if available
        repo_work_thumb = self.output_dir.parent / "export.work" / "thumbs" / f"{photo_id}.jpg"
        if repo_work_thumb.exists():
            shutil.copy2(repo_work_thumb, thumb_dest)
            return
        if record.original_path and Path(record.original_path).exists():
            try:
                self.thumb_gen.generate_photo_thumbnail(
                    image_path=record.original_path,
                    output_path=thumb_dest,
                )
                return
            except Exception:
                pass
        # Fallback if original photo temp directory was cleaned up
        from PIL import Image
        fallback = Image.new("RGB", (self.thumb_gen.thumb_size, self.thumb_gen.thumb_size), color=(30, 30, 35))
        thumb_dest.parent.mkdir(parents=True, exist_ok=True)
        fallback.save(thumb_dest, "JPEG")

    def _resolve_face(
        self,
        face_id: str,
        face_dest: Path,
        cache_crops: Optional[Path],
        orig_photo: Optional[PhotoRecord] = None,
        bbox: Optional[list] = None,
    ) -> None:
        # Strictly resolve by unique face_id (never by ephemeral person_id)
        if cache_crops and (cache_crops / f"{face_id}.jpg").exists():
            shutil.copy2(cache_crops / f"{face_id}.jpg", face_dest)
            return
        if self.cache_dir and (self.cache_dir / "crops" / f"{face_id}.jpg").exists():
            shutil.copy2(self.cache_dir / "crops" / f"{face_id}.jpg", face_dest)
            return
        if self.cache_dir and (self.cache_dir / "faces" / f"{face_id}.jpg").exists():
            shutil.copy2(self.cache_dir / "faces" / f"{face_id}.jpg", face_dest)
            return
        sibling_base = self.cache_dir.name.removesuffix(".work") if self.cache_dir else None
        if sibling_base and self.cache_dir:
            cand = self.cache_dir.parent / f"{sibling_base}.work" / "crops" / f"{face_id}.jpg"
            if cand.exists():
                shutil.copy2(cand, face_dest)
                return
        # Also check root export.work if available
        repo_work_crop = self.output_dir.parent / "export.work" / "crops" / f"{face_id}.jpg"
        if repo_work_crop.exists():
            shutil.copy2(repo_work_crop, face_dest)
            return
        if orig_photo and orig_photo.original_path and Path(orig_photo.original_path).exists() and bbox:
            try:
                self.thumb_gen.generate_square_face_crop(
                    image_path=orig_photo.original_path,
                    bbox=bbox,
                    output_path=face_dest,
                )
                return
            except Exception:
                pass
        # Fallback if original photo temp directory was cleaned up
        from PIL import Image
        fallback = Image.new("RGB", (self.thumb_gen.face_crop_size, self.thumb_gen.face_crop_size), color=(40, 45, 55))
        face_dest.parent.mkdir(parents=True, exist_ok=True)
        fallback.save(face_dest, "JPEG")

    def export(
        self,
        result: EngineResult,
        title: str = "Event Gallery",
        subtitle: str = "Grouped by Person",
        config_override: Optional[Dict[str, Any]] = None,
        include_maybe: Optional[bool] = None,
        generate_html: bool = False,
        cleanup_temp: bool = True,
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

            self._resolve_thumb(photo_id, record, thumb_dest, cache_thumbs)

            drive_url = getattr(record, "drive_url", None)
            if not drive_url and getattr(record, "drive_file_id", None):
                drive_url = f"https://drive.google.com/file/d/{record.drive_file_id}/view"
            share_url = getattr(record, "share_url", None)
            if not share_url and getattr(record, "drive_file_id", None):
                share_url = f"https://drive.google.com/file/d/{record.drive_file_id}/view?usp=sharing"

            photos_json[photo_id] = {
                "name": record.file_name,
                "thumb": thumb_rel,
                "download": record.download_url,
                "download_url": record.download_url,
                "drive_url": drive_url,
                "share_url": share_url,
                "drive_file_id": getattr(record, "drive_file_id", None),
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

            orig_photo = result.photos.get(person.rep_face.photo_id)
            self._resolve_face(
                face_id=person.rep_face.face_id,
                face_dest=face_dest,
                cache_crops=cache_crops,
                orig_photo=orig_photo,
                bbox=person.rep_face.bbox,
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
                        "file_name": result.photos[f.photo_id].file_name if f.photo_id in result.photos else f.photo_id,
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
            face_rel = item.get("face", f"faces/{face_obj.face_id}.jpg")
            face_dest = self.output_dir / face_rel

            orig_photo = result.photos.get(face_obj.photo_id)
            self._resolve_face(
                face_id=face_obj.face_id,
                face_dest=face_dest,
                cache_crops=cache_crops,
                orig_photo=orig_photo,
                bbox=face_obj.bbox,
            )

            unrecognized_faces_json.append({
                "face_id": face_obj.face_id,
                "photo_id": item["photo_id"],
                "file_name": result.photos[face_obj.photo_id].file_name if face_obj.photo_id in result.photos else item["photo_id"],
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

        # Clean orphaned thumbnails from previous failed/mixed exports
        thumbs_dir = self.output_dir / "thumbs"
        if thumbs_dir.exists():
            valid_thumb_stems = set(photos_json.keys())
            for t_file in thumbs_dir.glob("*.jpg"):
                if t_file.stem not in valid_thumb_stems:
                    try:
                        t_file.unlink()
                    except Exception:
                        pass

        # Clean orphaned face crops
        faces_dir = self.output_dir / "faces"
        if faces_dir.exists():
            valid_face_stems = set()
            for p in people_json:
                valid_face_stems.add(p["id"])
                for f in p["faces"]:
                    valid_face_stems.add(f["face_id"])
                    if f.get("face"):
                        valid_face_stems.add(Path(f["face"]).stem)
            for f in people_payload["unrecognized"]["faces"]:
                if isinstance(f, dict):
                    if f.get("face_id"):
                        valid_face_stems.add(f["face_id"])
                    if f.get("face"):
                        valid_face_stems.add(Path(f["face"]).stem)
            for f_file in faces_dir.glob("*.jpg"):
                if f_file.stem not in valid_face_stems:
                    try:
                        f_file.unlink()
                    except Exception:
                        pass

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
                "accent": "#fa7175",
                "font": "JetBrains Mono",
                "footer": "Published with CatLog — Who was at the event?",
                "show_labels": True,
                "include_maybe": False,
                "hide_single_photo_default": False,
                "theme": "t-dark",
            }
            if config_override:
                default_config.update(config_override)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)

        # 6. Generate Standalone HTML Gallery (index.html & gallery.html) if requested
        if generate_html:
            try:
                from backend.engine.standalone_html import generate_standalone_gallery_html
                cfg_dict = {}
                if config_path.exists():
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            cfg_dict = json.load(f)
                    except Exception:
                        cfg_dict = {}
                if not cfg_dict and "default_config" in locals():
                    cfg_dict = default_config
                standalone_html = generate_standalone_gallery_html(people_payload, cfg_dict)
                (self.output_dir / "index.html").write_text(standalone_html, encoding="utf-8")
                (self.output_dir / "gallery.html").write_text(standalone_html, encoding="utf-8")

                # Copy built viewer assets if available
                viewer_assets = Path(__file__).resolve().parent.parent.parent / "viewer" / "dist" / "assets"
                if viewer_assets.exists() and viewer_assets.is_dir():
                    target_assets = self.output_dir / "assets"
                    target_assets.mkdir(parents=True, exist_ok=True)
                    for af in viewer_assets.iterdir():
                        if af.is_file():
                            shutil.copy2(af, target_assets / af.name)
            except Exception as e:
                print(f"[exporter] Warning: Failed to generate standalone HTML: {e}")

        # 7. Clean up temporary working directory once exported
        if cleanup_temp:
            temp_dirs_to_clean = set()
            temp_dir = getattr(result, "temp_dir", None)
            if temp_dir:
                temp_dirs_to_clean.add(Path(temp_dir))
            if self.cache_dir and self.cache_dir.name.endswith("_temp"):
                temp_dirs_to_clean.add(self.cache_dir)

            for t_p in temp_dirs_to_clean:
                if t_p.exists() and t_p.is_dir():
                    try:
                        shutil.rmtree(t_p, ignore_errors=True)
                    except Exception:
                        pass

        # 8. Verify Bundle Integrity
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
