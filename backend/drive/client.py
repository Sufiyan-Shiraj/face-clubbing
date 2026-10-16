"""Google Drive API v3 client with bounded parallelism, thumbnail resizing, fallback, retry/backoff, and resumable caching."""

from __future__ import annotations
import json
import os
import re
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
import requests

from backend.drive.config import sanitize_message_for_logs, mask_api_key

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"


class DriveError(Exception):
    """Base exception for Google Drive operations."""
    pass


class DriveAuthError(DriveError):
    """Authentication or invalid API key error."""
    pass


class DrivePermissionError(DriveError):
    """Private folder or inaccessible resource error."""
    pass


class DriveQuotaError(DriveError):
    """Quota or rate limit exceeded error."""
    pass


@dataclass
class DriveFile:
    """Metadata for a file hosted on Google Drive."""
    id: str
    name: str
    mime_type: str
    modified_time: str
    size: int = 0
    thumbnail_link: Optional[str] = None
    download_url: str = field(init=False)

    def __post_init__(self):
        # Format required by SPEC 8.2 and Phase 6: https://drive.google.com/uc?id=<ID>&export=download
        self.download_url = f"https://drive.google.com/uc?id={self.id}&export=download"


@dataclass
class DriveListResult:
    """Summary of a Drive folder listing operation."""
    files: List[DriveFile]
    total_files_in_folder: int
    image_count: int
    skipped_folders_count: int
    skipped_non_images_count: int
    skipped_videos_count: int = 0
    scanned_folder_names: List[str] = field(default_factory=list)
    non_image_sample_names: List[str] = field(default_factory=list)


SUPPORTED_IMAGE_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".webp",
    ".heic", ".heif", ".hif", ".avif",
    ".bmp", ".tiff", ".tif"
)

SUPPORTED_IMAGE_MIMES = (
    "image/jpeg", "image/png", "image/webp",
    "image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence",
    "image/bmp", "image/tiff", "image/x-adobe-dng"
)

VIDEO_EXTENSIONS = (
    ".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm", ".wmv",
    ".flv", ".3gp", ".mts", ".m2ts", ".ts", ".vob", ".ogv", ".qt"
)


def is_video_file(name: str, mime_type: str) -> bool:
    """Check if the given file is a video."""
    if mime_type.startswith("video/") or mime_type in ("application/mp4", "application/x-matroska"):
        return True
    return name.lower().endswith(VIDEO_EXTENSIONS)


def is_image_file(name: str, mime_type: str) -> bool:
    """Check if the given file is a supported image (including HEIC / HEIF)."""
    if is_video_file(name, mime_type):
        return False
    if mime_type.startswith("image/") or mime_type in SUPPORTED_IMAGE_MIMES:
        return True
    return name.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)


def resize_thumbnail_link(link: str, target_size: int = 1000) -> str:
    """
    Adjust Google Drive thumbnailLink dimension parameter to target size (default =s1000).
    Example: https://lh3.googleusercontent.com/u/0/d/xyz=s220 -> ...=s1000
    """
    if not link:
        return link
    if "=s" in link:
        return re.sub(r"=s\d+", f"=s{target_size}", link)
    # If ends in slash or raw URL, append size parameter
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}sz=s{target_size}"


class DriveClient:
    """Google Drive API v3 read-only client."""

    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        if not api_key or not api_key.strip():
            raise DriveAuthError(
                "Google Drive API key is required. Please set it in Settings or set the DRIVE_API_KEY environment variable."
            )
        self.api_key = api_key.strip()
        self.session = session or requests.Session()

    def _handle_api_error_response(self, resp: requests.Response) -> None:
        """Parse Google Drive error JSON and raise appropriate domain exception."""
        error_msg = f"HTTP {resp.status_code}"
        reason = ""
        try:
            raw_json = resp.json()
            if isinstance(raw_json, dict):
                err_json = raw_json.get("error", {})
                if isinstance(err_json, dict):
                    msg = err_json.get("message")
                    if msg:
                        error_msg = str(msg)
                    errors = err_json.get("errors", [])
                    if errors and isinstance(errors, list) and isinstance(errors[0], dict):
                        reason = str(errors[0].get("reason", ""))
        except Exception:
            pass

        sanitized_msg = sanitize_message_for_logs(error_msg)

        if resp.status_code == 400 or "API key not valid" in sanitized_msg or reason == "badRequest":
            raise DriveAuthError(f"Invalid Google Drive API key: {sanitized_msg}")

        if resp.status_code == 403:
            if reason in ("dailyLimitExceeded", "userRateLimitExceeded", "rateLimitExceeded", "quotaExceeded"):
                raise DriveQuotaError(
                    f"Google Drive API quota exceeded. ({sanitized_msg}). Please verify your quota in Google Cloud Console."
                )
            if reason == "accessNotConfigured":
                raise DriveAuthError(
                    "Google Drive API is not enabled for this key. Please enable 'Google Drive API' in Google Cloud Console."
                )
            raise DrivePermissionError(
                f"Google Drive folder is private or inaccessible ({sanitized_msg}). "
                "Ensure the folder is shared with 'Anyone with the link' (Viewer access)."
            )

        if resp.status_code == 404:
            raise DrivePermissionError(
                f"Google Drive folder was not found ({sanitized_msg}). "
                "Ensure the folder link is correct and shared with 'Anyone with the link'."
            )

        raise DriveError(f"Google Drive API error ({resp.status_code}): {sanitized_msg}")

    def list_folder_images(
        self,
        folder_id: str,
        cancel_check: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        recursive: bool = True,
        max_depth: int = 10,
        stop_after_images: Optional[int] = None,
    ) -> DriveListResult:
        """
        List all image files inside a public Google Drive folder with pagination.
        Recursively traverses subfolders and shortcuts when recursive=True.
        Skips non-images and explicitly ignores video files, reporting counts.
        """
        files: List[DriveFile] = []
        total_items = 0
        skipped_folders = 0
        skipped_videos = 0
        skipped_non_images = 0
        scanned_folder_names: List[str] = []
        non_image_sample_names: List[str] = []

        folders_to_visit: List[Tuple[str, int]] = [(folder_id, 0)]
        visited_folders: set[str] = {folder_id}
        url = f"{DRIVE_API_BASE}/files"

        while folders_to_visit:
            cur_fid, depth = folders_to_visit.pop(0)
            page_token: Optional[str] = None
            query = f"'{cur_fid}' in parents and trashed = false"

            while True:
                if cancel_check and cancel_check():
                    raise InterruptedError("Listing cancelled by user")

                params: Dict[str, Any] = {
                    "key": self.api_key,
                    "q": query,
                    "pageSize": 100,
                    "fields": "nextPageToken, files(id, name, mimeType, modifiedTime, size, thumbnailLink, shortcutDetails)",
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true",
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = self._request_with_retry("GET", url, params=params)
                if resp.status_code != 200:
                    self._handle_api_error_response(resp)

                data = resp.json()
                raw_files = data.get("files", [])

                for item in raw_files:
                    total_items += 1
                    mime_type = item.get("mimeType", "")
                    name = item.get("name", "")
                    item_id = item["id"]

                    # 1. Google Drive subfolder
                    if mime_type == "application/vnd.google-apps.folder":
                        skipped_folders += 1
                        scanned_folder_names.append(name)
                        if recursive and depth < max_depth and item_id not in visited_folders:
                            visited_folders.add(item_id)
                            folders_to_visit.append((item_id, depth + 1))
                        continue

                    # 2. Google Drive shortcut
                    if mime_type == "application/vnd.google-apps.shortcut":
                        shortcut_details = item.get("shortcutDetails", {})
                        target_id = shortcut_details.get("targetId")
                        target_mime = shortcut_details.get("targetMimeType", "")
                        if target_mime == "application/vnd.google-apps.folder":
                            skipped_folders += 1
                            scanned_folder_names.append(name)
                            if recursive and target_id and depth < max_depth and target_id not in visited_folders:
                                visited_folders.add(target_id)
                                folders_to_visit.append((target_id, depth + 1))
                            continue
                        elif target_id and target_mime:
                            mime_type = target_mime
                            item_id = target_id

                    # 3. Video file -> explicitly ignore
                    if is_video_file(name, mime_type):
                        skipped_videos += 1
                        continue

                    # 4. Supported image (JPEG, PNG, HEIC, HEIF, WebP, etc.)
                    if is_image_file(name, mime_type):
                        df = DriveFile(
                            id=item_id,
                            name=name,
                            mime_type=mime_type,
                            modified_time=item.get("modifiedTime", ""),
                            size=int(item.get("size", 0)),
                            thumbnail_link=item.get("thumbnailLink"),
                        )
                        files.append(df)
                        if stop_after_images and len(files) >= stop_after_images:
                            break
                    else:
                        skipped_non_images += 1
                        if len(non_image_sample_names) < 5:
                            non_image_sample_names.append(name)

                if stop_after_images and len(files) >= stop_after_images:
                    break

                if progress_callback:
                    video_str = f", {skipped_videos} videos skipped" if skipped_videos > 0 else ""
                    progress_callback({
                        "stage": "listing",
                        "current": len(files),
                        "total": total_items,
                        "message": f"Found {len(files)} photos (scanned {total_items} items across {skipped_folders} folders{video_str})...",
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            if stop_after_images and len(files) >= stop_after_images:
                break

        return DriveListResult(
            files=files,
            total_files_in_folder=total_items,
            image_count=len(files),
            skipped_folders_count=skipped_folders,
            skipped_non_images_count=skipped_non_images,
            skipped_videos_count=skipped_videos,
            scanned_folder_names=scanned_folder_names,
            non_image_sample_names=non_image_sample_names,
        )

    def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 4,
        base_delay: float = 1.0,
        **kwargs,
    ) -> requests.Response:
        """Execute HTTP request with exponential backoff and jitter on 403, 429, 5xx."""
        attempt = 0
        last_resp = None

        while attempt <= max_retries:
            try:
                if method.upper() == "GET":
                    resp = self.session.get(url, timeout=kwargs.pop("timeout", 30), **kwargs)
                else:
                    resp = self.session.request(method, url, timeout=kwargs.pop("timeout", 30), **kwargs)
                last_resp = resp

                if resp.status_code in (429, 500, 502, 503, 504):
                    # Transient error, retry
                    pass
                elif resp.status_code == 403:
                    # Check if 403 is a rate limit error (rateLimitExceeded / userRateLimitExceeded)
                    is_rate_limit = False
                    try:
                        err_data = resp.json().get("error", {})
                        for err in err_data.get("errors", []):
                            if err.get("reason") in ("userRateLimitExceeded", "rateLimitExceeded"):
                                is_rate_limit = True
                                break
                    except Exception:
                        pass
                    if not is_rate_limit:
                        return resp  # Not a rate limit error (e.g. forbidden or permission)
                else:
                    return resp
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                if attempt == max_retries:
                    raise DriveError(f"Network error communicating with Google Drive: {e}")

            attempt += 1
            if attempt <= max_retries:
                # Exponential backoff with random jitter
                delay = min(16.0, base_delay * (2 ** (attempt - 1))) + random.uniform(0.0, 0.4)
                time.sleep(delay)

        if last_resp is not None:
            return last_resp
        raise DriveError("Drive request failed after maximum retries.")

    def download_thumbnails(
        self,
        files: List[DriveFile],
        cache_dir: Optional[Path | str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        max_workers: int = 4,
        dest_dir: Optional[Path | str] = None,
    ) -> List[Tuple[DriveFile, Path]]:
        """
        Download size-limited thumbnails (=s1000) for all photos with bounded parallelism.
        Falls back to alt=media if no thumbnailLink or if thumbnail download fails.
        Resumable: skips files already present with identical file ID and modifiedTime.
        """
        actual_dir = cache_dir or dest_dir
        if not actual_dir:
            raise ValueError("cache_dir or dest_dir must be provided")
        cache_path = Path(actual_dir).resolve()
        cache_path.mkdir(parents=True, exist_ok=True)
        manifest_file = cache_path / "manifest.json"

        # Load manifest
        manifest: Dict[str, Dict[str, Any]] = {}
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                manifest = {}

        manifest_lock = threading.Lock()
        results: List[Tuple[DriveFile, Path]] = []
        total = len(files)
        completed_count = 0
        start_time = time.time()

        def _download_single(df: DriveFile) -> Tuple[DriveFile, Path]:
            nonlocal completed_count
            if cancel_check and cancel_check():
                raise InterruptedError("Download cancelled by user")

            # Safe local filename
            safe_name = re.sub(r'[^\w\.-]', '_', df.name)
            target_path = cache_path / f"{df.id}_{safe_name}"

            # Resumable check: if file exists and manifest entry matches modified_time
            with manifest_lock:
                entry = manifest.get(df.id)
                if (
                    entry
                    and entry.get("modified_time") == df.modified_time
                    and target_path.exists()
                    and target_path.stat().st_size > 0
                ):
                    completed_count += 1
                    return df, target_path

            # Attempt 1: Download resized thumbnail if link is available
            downloaded = False
            content = None

            if df.thumbnail_link:
                resized_url = resize_thumbnail_link(df.thumbnail_link, target_size=1000)
                try:
                    resp = self._request_with_retry("GET", resized_url, timeout=20)
                    if resp.status_code == 200 and len(resp.content) > 100:
                        content = resp.content
                        downloaded = True
                except Exception:
                    downloaded = False

            # Attempt 2: Fall back to original file content via Drive API alt=media
            if not downloaded:
                fallback_url = f"{DRIVE_API_BASE}/files/{df.id}"
                params = {"alt": "media", "key": self.api_key}
                resp = self._request_with_retry("GET", fallback_url, params=params, timeout=40)
                if resp.status_code == 200 and len(resp.content) > 100:
                    content = resp.content
                    downloaded = True
                else:
                    self._handle_api_error_response(resp)

            if not downloaded or not content:
                raise DriveError(f"Failed to download photo {df.name} (id: {df.id}) from Google Drive.")

            # Write file atomically via temp file
            tmp_target = target_path.with_suffix(".tmp")
            with open(tmp_target, "wb") as f:
                f.write(content)
            tmp_target.replace(target_path)

            with manifest_lock:
                manifest[df.id] = {
                    "file_name": df.name,
                    "modified_time": df.modified_time,
                    "size": len(content),
                    "local_path": target_path.name,
                }
                completed_count += 1
                cur = completed_count

            # Progress notification
            if progress_callback:
                elapsed = time.time() - start_time
                avg_time = elapsed / cur if cur > 0 else 0.0
                eta = round(avg_time * (total - cur), 1) if cur < total else 0.0
                pct = round((cur / total) * 100.0, 1) if total > 0 else 100.0
                progress_callback({
                    "stage": "downloading",
                    "current": cur,
                    "total": total,
                    "percent": pct,
                    "file_name": df.name,
                    "eta_seconds": eta,
                    "message": f"Downloading photos: [{cur}/{total}] {df.name}",
                })

            return df, target_path

        # Execute with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(_download_single, df): df for df in files}
            for future in as_completed(future_to_file):
                if cancel_check and cancel_check():
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise InterruptedError("Download cancelled by user")
                df, path = future.result()
                results.append((df, path))

        # Save updated manifest
        try:
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception:
            pass

        # Sort results to match original ordering of files
        id_order = {df.id: i for i, df in enumerate(files)}
        results.sort(key=lambda pair: id_order.get(pair[0].id, 0))

        return results
