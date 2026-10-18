"""Robust model weights downloader and integrity verifier for InsightFace models (SPEC 9 & 13)."""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable

BUFFALO_L_URL = "https://github.com/deepinsight/insightface/releases/download/model-zoo/buffalo_l.zip"
BUFFALO_L_ZIP_SIZE = 288621354

# Known specifications for buffalo_l ONNX components
BUFFALO_L_ONNX_SPECS: Dict[str, Dict[str, Any]] = {
    "1k3d68.onnx": {
        "size": 143607619,
        "sha256": "df5c06b8a0c12e422b2ed8947b8869faa4105387f199c477af038aa01f9a45cc",
    },
    "2d106det.onnx": {
        "size": 5030888,
        "sha256": "f001b856447c413801ef5c42091ed0cd516fcd21f2d6b79635b1e733a7109dbf",
    },
    "det_10g.onnx": {
        "size": 16923827,
        "sha256": "5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91",
    },
    "genderage.onnx": {
        "size": 1322532,
        "sha256": "4fde69b1c810857b88c64a335084f1c3fe8f01246c9a191b48c7bb756d6652fb",
    },
    "w600k_r50.onnx": {
        "size": 174383860,
        "sha256": "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43",
    },
}


def verify_model_dir(target_dir: Path | str, specs: Optional[Dict[str, Dict[str, Any]]] = None) -> Tuple[bool, Optional[str]]:
    """
    Verifies that target_dir exists and contains all required ONNX model files
    with exact matching sizes and SHA-256 hashes.
    """
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        return False, f"Directory does not exist: {target}"

    spec_map = specs or BUFFALO_L_ONNX_SPECS
    for filename, expected in spec_map.items():
        file_path = target / filename
        if not file_path.exists():
            return False, f"Missing model file: {filename}"

        stat = file_path.stat()
        if stat.st_size != expected["size"]:
            return False, f"File {filename} size mismatch: expected {expected['size']}, got {stat.st_size}"

        expected_hash = expected.get("sha256")
        if expected_hash:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(256 * 1024):
                    h.update(chunk)
            digest = h.hexdigest().lower()
            if digest != expected_hash.lower():
                return False, f"File {filename} SHA-256 mismatch: expected {expected_hash}, got {digest}"

    return True, None


def ensure_model_available(
    model_name: str = "buffalo_l",
    model_root: Optional[str | Path] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    download_url: Optional[str] = None,
    check_fallback: bool = True,
) -> Path:
    """
    Ensures model directory exists and passes verification.
    1. Checks target directory; if valid, returns immediately.
    2. If files exist but fail verification (corrupt/truncated), deletes them.
    3. If fallback directory exists and is valid, copies from fallback.
    4. Downloads archive to .part file, verifying size and hashes.
    5. On any download/verify failure, removes partial files.
    6. Renames only on successful complete download, extracts and re-verifies.
    """
    root_p = Path(model_root or (Path.home() / ".photosorter")).resolve()
    target_dir = root_p / "models" / model_name
    models_parent = target_dir.parent
    models_parent.mkdir(parents=True, exist_ok=True)

    # 1. Check existing target
    if target_dir.exists():
        valid, reason = verify_model_dir(target_dir)
        if valid:
            return target_dir
        # Corrupt stored model: report and clean up
        msg = f"Stored model files in {target_dir} failed verification ({reason}). Removing and re-downloading..."
        print(f"[models_downloader] {msg}")
        if progress_callback:
            progress_callback({
                "stage": "model_verify_failed",
                "message": msg,
            })
        shutil.rmtree(target_dir, ignore_errors=True)

    # 2. Check fallback directory (e.g. ~/.insightface/models/buffalo_l)
    if check_fallback:
        fallback_dir = Path.home() / ".insightface" / "models" / model_name
        if fallback_dir.exists():
            valid, _ = verify_model_dir(fallback_dir)
            if valid:
                try:
                    shutil.copytree(fallback_dir, target_dir)
                    v_copy, _ = verify_model_dir(target_dir)
                    if v_copy:
                        return target_dir
                except Exception:
                    shutil.rmtree(target_dir, ignore_errors=True)

    # 3. Download via atomic .part file
    url = download_url or BUFFALO_L_URL
    zip_path = models_parent / f"{model_name}.zip"
    part_path = models_parent / f"{model_name}.zip.part"

    if part_path.exists():
        try:
            part_path.unlink()
        except OSError:
            pass

    expected_zip_size = BUFFALO_L_ZIP_SIZE
    downloaded_bytes = 0

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PhotoSorter-Engine/1.0 (+https://github.com/Sufiyan-Shiraj/face-clubbing)"},
    )

    try:
        if progress_callback:
            progress_callback({
                "stage": "model_download",
                "current": 0,
                "total": expected_zip_size,
                "percent": 0.0,
                "progress": 0.0,
                "message": f"Connecting to download {model_name} model (~{expected_zip_size / (1024*1024):.1f} MB)...",
            })

        with urllib.request.urlopen(req, timeout=30) as resp:
            content_len = resp.headers.get("Content-Length")
            if content_len:
                try:
                    expected_zip_size = int(content_len)
                except ValueError:
                    pass

            with open(part_path, "wb") as f_part:
                while True:
                    chunk = resp.read(128 * 1024)
                    if not chunk:
                        break
                    f_part.write(chunk)
                    downloaded_bytes += len(chunk)

                    if progress_callback:
                        pct = round((downloaded_bytes / expected_zip_size) * 100.0, 1) if expected_zip_size > 0 else 0.0
                        mb_cur = downloaded_bytes / (1024 * 1024)
                        mb_tot = expected_zip_size / (1024 * 1024)
                        progress_callback({
                            "stage": "model_download",
                            "current": downloaded_bytes,
                            "total": expected_zip_size,
                            "percent": pct,
                            "progress": round(downloaded_bytes / expected_zip_size, 4) if expected_zip_size > 0 else 0.0,
                            "message": f"Downloading {model_name} ({mb_cur:.1f} / {mb_tot:.1f} MB, {pct}%)...",
                        })

        # Verify completed zip size
        actual_size = part_path.stat().st_size
        if expected_zip_size > 0 and actual_size != expected_zip_size:
            raise ValueError(
                f"Downloaded model size mismatch: expected {expected_zip_size} bytes, got {actual_size} bytes"
            )

        # Atomic rename only when complete
        if zip_path.exists():
            zip_path.unlink()
        part_path.replace(zip_path)

    except Exception as e:
        # Delete partial file on failure
        if part_path.exists():
            try:
                part_path.unlink()
            except OSError:
                pass
        raise RuntimeError(
            f"InsightFace model '{model_name}' download failed ({e}). "
            f"Please ensure an active internet connection to download models to '{target_dir}', "
            f"or manually place verified ONNX files in that folder."
        ) from e

    # 4. Extract archive
    extract_tmp = models_parent / f"{model_name}_extract_tmp"
    shutil.rmtree(extract_tmp, ignore_errors=True)
    extract_tmp.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_tmp)

        # buffalo_l.zip extracts either directly or inside a buffalo_l folder
        nested = extract_tmp / model_name
        source_dir = nested if nested.exists() and nested.is_dir() else extract_tmp

        # Validate extracted files before finalizing
        valid, reason = verify_model_dir(source_dir)
        if not valid:
            raise ValueError(f"Extracted models failed verification: {reason}")

        # Move to target_dir
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.move(str(source_dir), str(target_dir))

    finally:
        shutil.rmtree(extract_tmp, ignore_errors=True)
        if zip_path.exists():
            try:
                zip_path.unlink()
            except OSError:
                pass

    # Final verification
    valid, reason = verify_model_dir(target_dir)
    if not valid:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise RuntimeError(f"Model directory verification failed after extraction: {reason}")

    return target_dir
