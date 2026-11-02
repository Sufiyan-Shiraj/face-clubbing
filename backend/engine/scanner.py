"""Scans local folders or zip files for images and generates stable photo IDs."""

from __future__ import annotations
import hashlib
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Set, Tuple

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".heic", ".heif", ".bmp", ".tiff", ".tif"
}

IGNORED_SYSTEM_NAMES = {
    ".ds_store", "thumbs.db", "desktop.ini", ".gitignore", ".gitattributes", ".localized", "icon\r"
}


@dataclass
class ScannedPhoto:
    photo_id: str
    file_path: Path
    file_name: str
    relative_path: str
    download_url: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_url: Optional[str] = None
    share_url: Optional[str] = None
    source_id: Optional[str] = None
    source_label: Optional[str] = None
    folder_path: Optional[str] = None
    album: Optional[str] = None


def compute_file_hash(path: Path | str, chunk_size: int = 65536) -> str:
    """Compute a stable SHA256 hex digest for a file (truncated to 16 hex chars)."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def _is_system_ignored(path_or_name: str | Path) -> bool:
    name = Path(path_or_name).name.lower()
    if name in IGNORED_SYSTEM_NAMES or name.startswith("._") or name.startswith(".git"):
        return True
    return False


class PhotoScanner:
    """Scans directories or zip archives for photo files, with nested zip unpacking and unsupported file tracking."""

    def __init__(self, input_path: str | Path, temp_dir: Optional[Path | str] = None):
        self.input_path = Path(input_path).resolve()
        self.custom_temp_dir = Path(temp_dir).resolve() if temp_dir else None
        self.temp_dir: Optional[Path] = None
        self._owns_temp_dir: bool = False
        self.unsupported_files: Dict[str, int] = {}
        self.unsupported_count: int = 0
        self.extracted_nested_zips: List[str] = []
        self._visited_zips: Set[Path] = set()

    def __enter__(self) -> PhotoScanner:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_temp_dir:
            self.cleanup()

    def cleanup(self) -> None:
        """Remove any temporary extracted directories created internally."""
        if self._owns_temp_dir and self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            self.temp_dir = None

    def _get_or_create_temp_dir(self) -> Path:
        """Returns or lazily creates a temporary directory for extraction."""
        if self.temp_dir is None:
            if self.custom_temp_dir:
                self.temp_dir = self.custom_temp_dir / "extracted"
                self.temp_dir.mkdir(parents=True, exist_ok=True)
                self._owns_temp_dir = False
            else:
                self.temp_dir = Path(tempfile.mkdtemp(prefix="photosorter_zip_"))
                self._owns_temp_dir = True
        return self.temp_dir

    def _extract_nested_archives(self, base_dir: Path, max_depth: int = 3) -> None:
        """Recursively unpack any nested zip files within base_dir up to max_depth."""
        if not base_dir.exists():
            return
        depth = 0
        while depth < max_depth:
            found_any = False
            zip_candidates: List[Path] = []
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".zip"):
                        zf = (Path(root) / f).resolve()
                        if zf not in self._visited_zips and zipfile.is_zipfile(zf):
                            zip_candidates.append(zf)

            if not zip_candidates:
                break

            for zf in zip_candidates:
                found_any = True
                self._visited_zips.add(zf)
                self.extracted_nested_zips.append(zf.name)
                target = zf.parent / f"{zf.stem}_extracted"
                target.mkdir(parents=True, exist_ok=True)
                try:
                    with zipfile.ZipFile(zf, "r") as z:
                        z.extractall(target)
                except Exception:
                    pass

                # If archive is within our temp directory, remove the zip to avoid duplicate scans
                if self.temp_dir and (self.temp_dir in zf.parents or zf == self.temp_dir):
                    try:
                        zf.unlink()
                    except Exception:
                        pass
                elif self._owns_temp_dir:
                    try:
                        zf.unlink()
                    except Exception:
                        pass

            depth += 1
            if not found_any:
                break

    def get_unsupported_summary(self) -> Dict[str, Any]:
        """Return a structured dictionary summarizing unsupported files and extracted archives."""
        return {
            "total_unsupported": self.unsupported_count,
            "extensions": dict(sorted(self.unsupported_files.items())),
            "extracted_nested_zips": list(self.extracted_nested_zips),
        }

    def scan(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        scan_subfolders: bool = True,
        max_subfolder_depth: int = 5,
        follow_shortcuts: bool = False,
    ) -> List[ScannedPhoto]:
        """Scan input path (folder or zip) and return list of ScannedPhoto objects."""
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input path does not exist: {self.input_path}")

        source_dir = self.input_path
        scan_roots: List[Tuple[Path, Path]] = []  # (dir_to_scan, base_rel_dir)

        if self.input_path.is_file():
            if zipfile.is_zipfile(self.input_path):
                temp_p = self._get_or_create_temp_dir()
                with zipfile.ZipFile(self.input_path, "r") as z:
                    z.extractall(temp_p)
                source_dir = temp_p
                self._extract_nested_archives(source_dir, max_depth=3)
                scan_roots.append((source_dir, source_dir))
            else:
                # Single photo file
                ext = self.input_path.suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    photo_id = compute_file_hash(self.input_path)
                    res = [
                        ScannedPhoto(
                            photo_id=photo_id,
                            file_path=self.input_path,
                            file_name=self.input_path.name,
                            relative_path=self.input_path.name,
                        )
                    ]
                    if progress_callback:
                        progress_callback(1, 1, self.input_path.name)
                    return res
                else:
                    ext_str = f"'{ext}'" if ext else "no file extension"
                    raise ValueError(
                        f"File '{self.input_path.name}' is an unsupported format ({ext_str}). "
                        f"Supported image formats are: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
                    )
        else:
            # input_path is a directory
            source_dir = self.input_path
            # Check for zip archives inside user folder to unpack into temp
            dir_zips: List[Path] = []
            for root, _, files in os.walk(source_dir):
                for f in files:
                    if f.lower().endswith(".zip"):
                        zf = (Path(root) / f).resolve()
                        if zipfile.is_zipfile(zf):
                            dir_zips.append(zf)

            if dir_zips:
                temp_p = self._get_or_create_temp_dir()
                for zf in dir_zips:
                    self._visited_zips.add(zf)
                    self.extracted_nested_zips.append(zf.name)
                    target = temp_p / f"{zf.stem}_extracted"
                    target.mkdir(parents=True, exist_ok=True)
                    try:
                        with zipfile.ZipFile(zf, "r") as z:
                            z.extractall(target)
                    except Exception:
                        pass
                self._extract_nested_archives(temp_p, max_depth=3)

            scan_roots.append((source_dir, source_dir))
            if self.temp_dir and self.temp_dir.exists() and self.temp_dir != source_dir:
                scan_roots.append((self.temp_dir, self.temp_dir))

        candidate_files: List[Tuple[Path, str, Path]] = []  # (file_path, file_name, base_dir)

        for s_root, b_rel in scan_roots:
            if not scan_subfolders:
                try:
                    for entry in os.scandir(s_root):
                        if entry.is_file():
                            if _is_system_ignored(entry.name):
                                continue
                            ep = Path(entry.path).resolve()
                            if ep in self._visited_zips:
                                continue
                            ext = Path(entry.name).suffix.lower()
                            if ext in SUPPORTED_EXTENSIONS:
                                candidate_files.append((ep, entry.name, b_rel))
                            else:
                                ext_key = ext if ext else "(no extension)"
                                self.unsupported_files[ext_key] = self.unsupported_files.get(ext_key, 0) + 1
                                self.unsupported_count += 1
                except Exception:
                    pass
            else:
                for root, dirs, files in os.walk(s_root, followlinks=follow_shortcuts):
                    try:
                        rel = Path(root).relative_to(s_root)
                        depth = len(rel.parts)
                    except ValueError:
                        depth = 0

                    if depth >= max_subfolder_depth:
                        dirs.clear()

                    for file in files:
                        if _is_system_ignored(file):
                            continue
                        f_path = (Path(root) / file).resolve()
                        if f_path in self._visited_zips:
                            continue

                        ext = Path(file).suffix.lower()
                        if ext in SUPPORTED_EXTENSIONS:
                            candidate_files.append((f_path, file, b_rel))
                        else:
                            ext_key = ext if ext else "(no extension)"
                            self.unsupported_files[ext_key] = self.unsupported_files.get(ext_key, 0) + 1
                            self.unsupported_count += 1

        total_candidates = len(candidate_files)
        scanned: List[ScannedPhoto] = []
        for idx, (file_path, file, base_dir) in enumerate(candidate_files):
            try:
                rel_path = file_path.relative_to(base_dir).as_posix()
            except ValueError:
                rel_path = file_path.name

            folder_p = Path(rel_path).parent.as_posix()
            folder_path = folder_p if folder_p and folder_p != "." else None

            photo_id = compute_file_hash(file_path)
            scanned.append(
                ScannedPhoto(
                    photo_id=photo_id,
                    file_path=file_path,
                    file_name=file,
                    relative_path=rel_path,
                    folder_path=folder_path,
                    album=folder_path,
                )
            )
            if progress_callback:
                progress_callback(idx + 1, total_candidates, file)

        # Sort stably by relative path
        scanned.sort(key=lambda x: x.relative_path)
        return scanned

