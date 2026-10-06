"""Scans local folders or zip files for images and generates stable photo IDs."""

from __future__ import annotations
import hashlib
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Generator

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".heic", ".heif", ".bmp", ".tiff", ".tif"
}


@dataclass
class ScannedPhoto:
    photo_id: str
    file_path: Path
    file_name: str
    relative_path: str


def compute_file_hash(path: Path | str, chunk_size: int = 65536) -> str:
    """Compute a stable SHA256 hex digest for a file (truncated to 16 hex chars)."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


class PhotoScanner:
    """Scans directories or zip archives for photo files."""

    def __init__(self, input_path: str | Path):
        self.input_path = Path(input_path).resolve()
        self.temp_dir: Optional[Path] = None

    def __enter__(self) -> PhotoScanner:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self) -> None:
        """Remove any temporary extracted directories."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            self.temp_dir = None

    def scan(self) -> List[ScannedPhoto]:
        """Scan input path (folder or zip) and return list of ScannedPhoto objects."""
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path does not exist: {self.input_path}")

        source_dir = self.input_path
        if self.input_path.is_file():
            if zipfile.is_zipfile(self.input_path):
                self.temp_dir = Path(tempfile.mkdtemp(prefix="photosorter_zip_"))
                with zipfile.ZipFile(self.input_path, "r") as z:
                    z.extractall(self.temp_dir)
                source_dir = self.temp_dir
            else:
                # Single photo file
                if self.input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    photo_id = compute_file_hash(self.input_path)
                    return [
                        ScannedPhoto(
                            photo_id=photo_id,
                            file_path=self.input_path,
                            file_name=self.input_path.name,
                            relative_path=self.input_path.name,
                        )
                    ]
                else:
                    raise ValueError(f"File {self.input_path} is neither a zip file nor a supported image.")

        scanned: List[ScannedPhoto] = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    file_path = Path(root) / file
                    try:
                        rel_path = file_path.relative_to(source_dir).as_posix()
                    except ValueError:
                        rel_path = file_path.name

                    photo_id = compute_file_hash(file_path)
                    scanned.append(
                        ScannedPhoto(
                            photo_id=photo_id,
                            file_path=file_path,
                            file_name=file,
                            relative_path=rel_path,
                        )
                    )

        # Sort stably by relative path
        scanned.sort(key=lambda x: x.relative_path)
        return scanned
