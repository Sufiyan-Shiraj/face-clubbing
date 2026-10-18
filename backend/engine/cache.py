"""Disk cache for photo face detections and embeddings to support resume and fast re-runs."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List
from backend.engine.models import PhotoRecord

CACHE_VERSION = 2


def compute_settings_hash(
    model_name: str = "buffalo_l",
    det_size: tuple[int, int] | List[int] = (640, 640),
    min_det_score: float = 0.5,
    min_face_size: int = 64,
    max_yaw: float = 70.0,
    max_image_dim: int = 1600,
    flip_average: bool = False,
) -> str:
    """Compute a deterministic hash of settings that affect face detection and embeddings."""
    payload = {
        "model_name": str(model_name),
        "det_size": list(det_size),
        "min_det_score": round(float(min_det_score), 4),
        "min_face_size": int(min_face_size),
        "max_yaw": round(float(max_yaw), 4),
        "max_image_dim": int(max_image_dim),
        "flip_average": bool(flip_average),
    }
    dumped = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:16]


class EmbeddingCache:
    """Manages reading and writing cached face embeddings per photo ID."""

    def __init__(
        self,
        cache_dir: Path | str,
        settings_hash: Optional[str] = None,
        cache_version: int = CACHE_VERSION,
        require_settings_match: bool = True,
    ):
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.settings_hash = settings_hash or compute_settings_hash()
        self.cache_version = cache_version
        self.require_settings_match = require_settings_match if settings_hash is not None else False

    def _file_path(self, photo_id: str) -> Path:
        return self.cache_dir / f"{photo_id}.json"

    def has(self, photo_id: str) -> bool:
        """Check if valid cached detection exists for given photo_id."""
        return self.get(photo_id) is not None

    def get(self, photo_id: str) -> Optional[PhotoRecord]:
        """Retrieve cached PhotoRecord if it exists and matches version/settings, otherwise None."""
        fpath = self._file_path(photo_id)
        if not fpath.exists():
            return None
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Check version
            if data.get("cache_version") != self.cache_version:
                return None
            # Check settings hash if configured
            if self.require_settings_match and data.get("settings_hash") != self.settings_hash:
                return None
            return PhotoRecord.from_dict(data)
        except Exception:
            return None

    def save(self, record: PhotoRecord) -> None:
        """Save a PhotoRecord and its detected faces/embeddings to cache."""
        fpath = self._file_path(record.photo_id)
        temp_fpath = fpath.with_suffix(".tmp")
        data = record.to_dict()
        data["cache_version"] = self.cache_version
        data["settings_hash"] = self.settings_hash
        with open(temp_fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_fpath.replace(fpath)

    def load_all(self) -> Dict[str, PhotoRecord]:
        """Load all valid cached records present in cache directory."""
        records: Dict[str, PhotoRecord] = {}
        for fpath in self.cache_dir.glob("*.json"):
            if fpath.stem in ("id_map", "suggestions", "edits", "config", "people", "cache_manifest"):
                continue
            photo_id = fpath.stem
            rec = self.get(photo_id)
            if rec:
                records[photo_id] = rec
        return records
