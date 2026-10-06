"""Disk cache for photo face detections and embeddings to support resume and fast re-runs."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict
from backend.engine.models import PhotoRecord


class EmbeddingCache:
    """Manages reading and writing cached face embeddings per photo ID."""

    def __init__(self, cache_dir: Path | str):
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, photo_id: str) -> Path:
        return self.cache_dir / f"{photo_id}.json"

    def has(self, photo_id: str) -> bool:
        """Check if cached detection exists for given photo_id."""
        return self._file_path(photo_id).exists()

    def get(self, photo_id: str) -> Optional[PhotoRecord]:
        """Retrieve cached PhotoRecord if it exists, otherwise None."""
        fpath = self._file_path(photo_id)
        if not fpath.exists():
            return None
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PhotoRecord.from_dict(data)
        except Exception:
            return None

    def save(self, record: PhotoRecord) -> None:
        """Save a PhotoRecord and its detected faces/embeddings to cache."""
        fpath = self._file_path(record.photo_id)
        temp_fpath = fpath.with_suffix(".tmp")
        with open(temp_fpath, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)
        temp_fpath.replace(fpath)

    def load_all(self) -> Dict[str, PhotoRecord]:
        """Load all cached records present in cache directory."""
        records: Dict[str, PhotoRecord] = {}
        for fpath in self.cache_dir.glob("*.json"):
            photo_id = fpath.stem
            rec = self.get(photo_id)
            if rec:
                records[photo_id] = rec
        return records
