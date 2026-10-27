"""Robust model weights downloader and integrity verifier for InsightFace models (SPEC 9 & 13)."""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import threading
import time
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
    force_download: bool = False,
) -> Path:
    """
    Ensures model directory exists and passes verification.
    1. Checks target directory; if valid and not force_download, returns immediately.
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

    if not force_download:
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
    else:
        # Force re-download / update: clean existing target directory
        if target_dir.exists():
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

    meta = {
        "model_name": model_name,
        "version": "1.0.0",
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "update_available": False,
        "latest_version": "1.0.0",
        "update_message": "Models verified and ready.",
        "files": list(BUFFALO_L_ONNX_SPECS.keys()),
    }
    try:
        (target_dir / "model_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except Exception:
        pass

    return target_dir


def get_model_target_dir(model_name: str = "buffalo_l", model_root: Optional[str | Path] = None) -> Path:
    """Returns canonical storage directory for model weights."""
    root_p = Path(model_root or (Path.home() / ".photosorter")).resolve()
    return root_p / "models" / model_name


def get_model_status(
    model_name: str = "buffalo_l",
    model_root: Optional[str | Path] = None,
    check_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Checks if model ONNX files are downloaded, verified, and ready.
    Also returns version and update availability information.
    """
    target_dir = get_model_target_dir(model_name=model_name, model_root=model_root)

    chosen_dir = None
    valid = False
    reason = None

    if target_dir.exists() and target_dir.is_dir():
        valid, reason = verify_model_dir(target_dir)
        if valid:
            chosen_dir = target_dir

    if not valid and check_fallback:
        fallback_dir = Path.home() / ".insightface" / "models" / model_name
        if fallback_dir.exists() and fallback_dir.is_dir():
            v_fallback, _ = verify_model_dir(fallback_dir)
            if v_fallback:
                valid = True
                chosen_dir = fallback_dir
                reason = None

    installed_files = []
    missing_files = []
    total_size = 0

    if chosen_dir and chosen_dir.exists():
        for fname, spec in BUFFALO_L_ONNX_SPECS.items():
            fp = chosen_dir / fname
            if fp.exists():
                installed_files.append(fname)
                total_size += fp.stat().st_size
            else:
                missing_files.append(fname)
    else:
        missing_files = list(BUFFALO_L_ONNX_SPECS.keys())

    meta = {}
    meta_path = (chosen_dir or target_dir) / "model_meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    update_available = meta.get("update_available", False)
    if os.environ.get("CATLOG_MOCK_MODEL_UPDATE") == "1":
        update_available = True

    status_str = "ready" if valid else ("missing" if not (target_dir.exists() or (check_fallback and (Path.home() / ".insightface" / "models" / model_name).exists())) else "corrupt")
    if valid and update_available:
        status_str = "update_available"

    return {
        "model_name": model_name,
        "installed": valid,
        "valid": valid,
        "status": status_str,
        "target_dir": str(chosen_dir or target_dir),
        "missing_files": missing_files,
        "installed_files": installed_files,
        "total_size_bytes": total_size or BUFFALO_L_ZIP_SIZE,
        "version": meta.get("version", "1.0.0"),
        "latest_version": meta.get("latest_version", "1.1.0" if update_available else "1.0.0"),
        "update_available": update_available,
        "update_message": meta.get("update_message"),
        "reason": reason,
    }


def check_model_updates(
    model_name: str = "buffalo_l",
    model_root: Optional[str | Path] = None,
    simulate: bool = False,
    check_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Checks for newer model weight updates upstream.
    Sets update_available flag if remote version or headers indicate an update.
    """
    status = get_model_status(model_name=model_name, model_root=model_root, check_fallback=check_fallback)
    if not status["installed"]:
        return {
            "installed": False,
            "update_available": False,
            "version": "1.0.0",
            "latest_version": "1.0.0",
            "message": "Models are not installed. Download required.",
        }

    target_dir = get_model_target_dir(model_name=model_name, model_root=model_root)
    meta_path = target_dir / "model_meta.json"

    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    update_available = False
    latest_version = meta.get("version", "1.0.0")

    if simulate or os.environ.get("CATLOG_MOCK_MODEL_UPDATE") == "1":
        update_available = True
        latest_version = "1.1.0"
        message = "A new model update (buffalo_l v1.1.0) is available."
    else:
        try:
            req = urllib.request.Request(
                BUFFALO_L_URL,
                headers={"User-Agent": "PhotoSorter-Engine/1.0 (+https://github.com/Sufiyan-Shiraj/face-clubbing)"},
                method="HEAD",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                remote_etag = resp.headers.get("ETag")
                remote_lm = resp.headers.get("Last-Modified")
                stored_etag = meta.get("etag")
                if stored_etag and remote_etag and stored_etag != remote_etag:
                    update_available = True
                    latest_version = "1.0.1"
                    message = "A new update for buffalo_l models is available."
                else:
                    if remote_etag:
                        meta["etag"] = remote_etag
                    if remote_lm:
                        meta["last_modified"] = remote_lm
                    message = "Models are up to date (buffalo_l v1.0.0)."
        except Exception as e:
            message = f"Models verified locally. Remote check skipped ({e})."

    meta["update_available"] = update_available
    meta["latest_version"] = latest_version
    meta["update_message"] = message
    meta["last_checked"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except Exception:
        pass

    return {
        "installed": True,
        "update_available": update_available,
        "version": meta.get("version", "1.0.0"),
        "latest_version": latest_version,
        "message": message,
    }


class ModelDownloadManager:
    """Thread-safe manager for model weights download, progress tracking, and update checks."""

    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self.is_downloading: bool = False
        self.stage: str = "idle"  # "idle" | "connecting" | "downloading" | "extracting" | "verifying" | "completed" | "failed"
        self.percent: float = 0.0
        self.current_bytes: int = 0
        self.total_bytes: int = BUFFALO_L_ZIP_SIZE
        self.message: str = "Idle"
        self.error: Optional[str] = None
        self.model_name: str = "buffalo_l"
        self.model_root: Optional[str] = None

    def get_status(self, model_name: str = "buffalo_l", model_root: Optional[str | Path] = None) -> Dict[str, Any]:
        with self._lock:
            base = get_model_status(model_name=model_name, model_root=model_root)
            base.update({
                "is_downloading": self.is_downloading,
                "stage": self.stage,
                "percent": self.percent,
                "current_bytes": self.current_bytes,
                "total_bytes": self.total_bytes,
                "error": self.error,
            })
            if self.is_downloading:
                base["status"] = "downloading"
                base["message"] = self.message
            elif self.stage == "completed":
                base["message"] = "Models downloaded and verified successfully."
            elif self.stage == "failed":
                base["message"] = self.error or "Model download failed."
            return base

    def check_updates(self, model_name: str = "buffalo_l", model_root: Optional[str | Path] = None, simulate: bool = False, check_fallback: bool = True) -> Dict[str, Any]:
        return check_model_updates(model_name=model_name, model_root=model_root, simulate=simulate, check_fallback=check_fallback)

    def start_download(
        self,
        model_name: str = "buffalo_l",
        model_root: Optional[str | Path] = None,
        force: bool = False,
        download_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            if self.is_downloading:
                return self.get_status(model_name=model_name, model_root=model_root)

            self.is_downloading = True
            self.stage = "connecting"
            self.percent = 0.0
            self.current_bytes = 0
            self.total_bytes = BUFFALO_L_ZIP_SIZE
            self.message = f"Connecting to download {model_name}..."
            self.error = None
            self.model_name = model_name
            self.model_root = str(model_root) if model_root else None

            thread = threading.Thread(
                target=self._run_download,
                args=(model_name, model_root, force, download_url),
                daemon=True,
            )
            self._thread = thread
            thread.start()
            return self.get_status(model_name=model_name, model_root=model_root)

    def _run_download(
        self,
        model_name: str,
        model_root: Optional[str | Path],
        force: bool,
        download_url: Optional[str],
    ):
        def _cb(p: Dict[str, Any]):
            with self._lock:
                self.stage = p.get("stage", "downloading")
                self.percent = p.get("percent", self.percent)
                self.current_bytes = p.get("current", self.current_bytes)
                self.total_bytes = p.get("total", self.total_bytes)
                self.message = p.get("message", self.message)

        try:
            ensure_model_available(
                model_name=model_name,
                model_root=model_root,
                progress_callback=_cb,
                download_url=download_url,
                check_fallback=not force,
                force_download=force,
            )
            with self._lock:
                self.is_downloading = False
                self.stage = "completed"
                self.percent = 100.0
                self.current_bytes = self.total_bytes
                self.message = f"{model_name} models ready and verified."
                self.error = None
        except Exception as e:
            with self._lock:
                self.is_downloading = False
                self.stage = "failed"
                self.error = str(e)
                self.message = f"Download failed: {e}"


model_download_manager = ModelDownloadManager()
