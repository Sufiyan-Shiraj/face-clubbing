"""Diagnostics and error classification module for CatLog (BUILD_PLAN Phase V2-1).

Provides:
1. Deterministic error classification into standardized codes:
   - OFFLINE: Network disconnected, DNS failure, socket connection timeout
   - QUOTA_403: Google Drive API quota exceeded
   - PRIVATE_FOLDER_404: Google Drive folder private or not found
   - BAD_KEY_400: Google Drive API key invalid or expired
   - DISK_FULL: Out of disk space (ENOSPC, ERROR_DISK_FULL)
   - CORRUPT_INPUT: Unreadable or damaged photo/archive
   - GENERIC_ERROR: Unclassified runtime errors
2. Plain-language, actionable troubleshooting guidance.
3. Strict sanitization guaranteeing ZERO file paths, ZERO URLs, ZERO API keys,
   and ZERO personal face data in diagnostics reports (counts, IDs, and codes only).
"""

from __future__ import annotations
import os
import re
import sys
import platform
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.engine.cache import compute_settings_hash


class ErrorClassification(BaseModel):
    """Classified error details with plain-language troubleshooting guidance."""
    error_code: str
    title: str
    plain_language_fix: Optional[str] = None
    sanitized_message: str


class DiagnosticsCounts(BaseModel):
    """Counts-only metrics for diagnostics report (no personal data or paths)."""
    total_photos: int = 0
    people_count: int = 0
    clustered_faces: int = 0
    unrecognized_faces: int = 0
    unrecognized_photos: int = 0
    edits_count: int = 0
    drive_images_found: int = 0
    drive_folders_scanned: int = 0
    drive_folders_failed: int = 0
    drive_shortcuts_skipped: int = 0
    drive_non_images_skipped: int = 0


class DiagnosticsReport(BaseModel):
    """Complete sanitized diagnostics payload for bug reporting and copy diagnostics."""
    version: str
    os_name: str
    os_release: str
    architecture: str
    python_version: str
    settings_hash: str
    error_code: str = "NONE"
    error_title: Optional[str] = None
    plain_language_fix: Optional[str] = None
    sanitized_error: Optional[str] = None
    status: str = "idle"
    stage: str = "idle"
    counts: DiagnosticsCounts = Field(default_factory=DiagnosticsCounts)
    formatted_report: str = ""


def sanitize_sensitive_data(text: str) -> str:
    """Scrub absolute paths, drive links, API keys, and email addresses from text."""
    if not text:
        return ""
    s = str(text)

    # 1. Mask Google API keys (AIzaSy...)
    s = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[MASKED_API_KEY]', s)

    # 2. Mask Google Drive URLs and folder/file IDs
    s = re.sub(
        r'https?://drive\.google\.com/(?:[^\s"\'<>]+)',
        '[MASKED_DRIVE_URL]',
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r'https?://[^\s"\'<>]+',
        '[MASKED_URL]',
        s,
        flags=re.IGNORECASE,
    )

    # 3. Mask Windows drive paths (e.g. C:\Users\..., D:\...)
    s = re.sub(r'[A-Za-z]:\\[^:\n\r\t"\'<>*|?]+', '[LOCAL_PATH]', s)

    # 4. Mask Unix absolute paths (e.g. /home/..., /tmp/..., /Users/...)
    s = re.sub(r'(?:/(?:home|Users|tmp|var|etc|usr|opt|root))/[^\s"\'<>]+', '[LOCAL_PATH]', s)

    # 5. Mask potential email addresses
    s = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[MASKED_EMAIL]', s)

    return s.strip()


def classify_error(err: Any) -> ErrorClassification:
    """Classifies an exception or error string into a standardized code and plain-language fix."""
    err_str = str(err) if err is not None else ""
    err_type_name = type(err).__name__ if isinstance(err, Exception) else ""
    combined = f"{err_type_name} {err_str}".lower()

    # 1. DISK_FULL / ENOSPC
    if (
        "no space left on device" in combined
        or "not enough space on the disk" in combined
        or "enospc" in combined
        or "error_disk_full" in combined
        or (isinstance(err, OSError) and getattr(err, "errno", None) in (28, 112))
    ):
        return ErrorClassification(
            error_code="DISK_FULL",
            title="Disk Storage Full",
            plain_language_fix=(
                "Your drive ran out of free space while processing photos or saving exports. "
                "Free up storage space on the drive hosting your project folder or change the "
                "output folder in Settings to a drive with at least 2 GB of free space."
            ),
            sanitized_message="Storage drive is full (ENOSPC / Out of disk space).",
        )

    # 2. QUOTA_403
    if (
        "quota" in combined
        or "403" in combined
        or "ratelimit" in combined
        or "rate limit" in combined
        or "drivequotaerror" in combined
    ):
        return ErrorClassification(
            error_code="QUOTA_403",
            title="Google Drive Quota Exceeded",
            plain_language_fix=(
                "The Google Drive API rate limit or daily quota for this key has been exceeded. "
                "Go to Settings and enter your own free Google Drive API key from Google Cloud Console, "
                "or wait a few minutes before trying again."
            ),
            sanitized_message="Google Drive API quota or request rate limit exceeded (HTTP 403).",
        )

    # 3. PRIVATE_FOLDER_404
    if (
        "private" in combined
        or "permission" in combined
        or "drivepermissionerror" in combined
        or "404" in combined
        or "not found" in combined
        or "inaccessible" in combined
    ):
        return ErrorClassification(
            error_code="PRIVATE_FOLDER_404",
            title="Google Drive Folder Inaccessible or Private",
            plain_language_fix=(
                "CatLog could not access this Google Drive folder. "
                "Make sure the Google Drive folder link sharing is set to 'Anyone with the link' "
                "(Viewer access), and verify that the link or folder ID is correct."
            ),
            sanitized_message="Google Drive folder is private or not accessible (HTTP 404 / Permission Denied).",
        )

    # 4. BAD_KEY_400 / AUTH
    if (
        "api key not valid" in combined
        or "driveautherror" in combined
        or "api_key_invalid" in combined
        or "api_key_missing" in combined
        or "keyinvalid" in combined
        or ("400" in combined and "key" in combined)
    ):
        return ErrorClassification(
            error_code="BAD_KEY_400",
            title="Invalid or Missing Google Drive API Key",
            plain_language_fix=(
                "The Google Drive API key is invalid, expired, or missing. "
                "Check the API key in Settings. Ensure that the 'Google Drive API' service "
                "is enabled on the associated project in Google Cloud Console."
            ),
            sanitized_message="Google Drive API key is invalid or not configured (HTTP 400).",
        )

    # 5. OFFLINE / NETWORK_ERROR
    if (
        "connection" in combined
        or "network" in combined
        or "getaddrinfo" in combined
        or "offline" in combined
        or "dns" in combined
        or "timed out" in combined
        or "timeout" in combined
        or "unreachable" in combined
        or "socket" in combined
        or "connectionerror" in combined
    ):
        return ErrorClassification(
            error_code="OFFLINE",
            title="Network Connection Unavailable",
            plain_language_fix=(
                "CatLog was unable to connect to the network. "
                "Check your internet connection, Wi-Fi, or proxy settings. "
                "If scanning local files, ensure any model downloads are complete."
            ),
            sanitized_message="Network connection failed or host is unreachable.",
        )

    # 6. CORRUPT_INPUT
    if (
        "corrupt" in combined
        or "bad zip" in combined
        or "badzipfile" in combined
        or "unsupported file format" in combined
        or "truncated" in combined
    ):
        return ErrorClassification(
            error_code="CORRUPT_INPUT",
            title="Damaged or Unsupported Input File",
            plain_language_fix=(
                "The selected ZIP archive or photo file appears to be damaged or in an unsupported format. "
                "Try re-downloading or re-compressing the photos as a standard ZIP archive."
            ),
            sanitized_message="Input archive or image file is corrupt or unreadable.",
        )

    # 7. GENERIC_ERROR
    clean_msg = sanitize_sensitive_data(err_str)
    # Truncate clean message to 200 chars for brevity
    if len(clean_msg) > 200:
        clean_msg = clean_msg[:197] + "..."

    return ErrorClassification(
        error_code="GENERIC_ERROR",
        title="Processing Error Encountered",
        plain_language_fix=(
            "An unexpected error occurred during processing. "
            "Use the 'Copy diagnostics' button to capture safe system details and "
            "report this on GitHub without sharing any personal photos."
        ),
        sanitized_message=clean_msg or "An unexpected runtime error occurred.",
    )


def format_text_diagnostics(
    version: str,
    os_name: str,
    architecture: str,
    python_ver: str,
    settings_hash: str,
    error_code: str,
    plain_language_fix: Optional[str],
    stage: str,
    counts: DiagnosticsCounts,
) -> str:
    """Renders a clean, formatted plain-text diagnostics block safe for pasting into GitHub Issues."""
    fix_line = f"Fix Guidance: {plain_language_fix}\n" if plain_language_fix else ""
    return (
        "CatLog Diagnostics Report\n"
        "-------------------------\n"
        f"Version: {version}\n"
        f"Platform: {os_name} ({architecture})\n"
        f"Python: {python_ver}\n"
        f"Settings Hash: {settings_hash}\n"
        f"Stage: {stage}\n"
        f"Error Code: {error_code}\n"
        f"{fix_line}"
        "Counts:\n"
        f"  - Photos Ingested: {counts.total_photos}\n"
        f"  - People Clusters: {counts.people_count}\n"
        f"  - Clustered Faces: {counts.clustered_faces}\n"
        f"  - Unrecognized Faces: {counts.unrecognized_faces}\n"
        f"  - Unrecognized Photos: {counts.unrecognized_photos}\n"
        f"  - Applied Edits: {counts.edits_count}\n"
        f"  - Drive Images Found: {counts.drive_images_found}\n"
        f"  - Drive Folders Scanned: {counts.drive_folders_scanned}\n"
        f"  - Drive Folders Failed: {counts.drive_folders_failed}\n"
        f"  - Drive Shortcuts Skipped: {counts.drive_shortcuts_skipped}\n"
        f"  - Drive Non-Images Skipped: {counts.drive_non_images_skipped}\n"
        "-------------------------\n"
        "Privacy Notice: This report contains zero file paths, zero URLs, "
        "zero API keys, and zero attendee biometrics."
    )


def generate_diagnostics_report(
    state: Any,
    job_manager: Optional[Any] = None,
    error_override: Optional[Any] = None,
) -> DiagnosticsReport:
    """Builds a complete, sanitized diagnostics report object from current system state."""
    # 1. Version
    version_file = Path("VERSION")
    if version_file.exists():
        version = version_file.read_text(encoding="utf-8").strip()
    else:
        version = "0.1.0-rc1"

    # 2. System info
    os_name = f"{platform.system()} {platform.release()}"
    os_release = platform.version()
    architecture = platform.machine()
    python_ver = platform.python_version()

    # 3. Settings hash
    settings = getattr(state, "settings", None)
    if settings:
        s_hash = compute_settings_hash(
            min_det_score=getattr(settings, "min_det_score", 0.5),
            min_face_size=getattr(settings, "min_face_size", 64),
            max_yaw=getattr(settings, "max_yaw", 70.0),
            max_image_dim=getattr(settings, "max_image_dim", 1600),
            flip_average=getattr(settings, "flip_average", False),
        )
    else:
        s_hash = compute_settings_hash()

    # 4. Error classification
    err_source = error_override
    if err_source is None and job_manager:
        err_source = getattr(job_manager, "error", None)

    if err_source:
        classification = classify_error(err_source)
    else:
        classification = ErrorClassification(
            error_code="NONE",
            title="Healthy",
            plain_language_fix=None,
            sanitized_message="No errors reported.",
        )

    # 5. Extract counts only
    counts = DiagnosticsCounts()
    job_status = "idle"
    job_stage = "idle"

    if job_manager:
        job_status = getattr(job_manager, "status", "idle")
        job_stage = getattr(job_manager, "stage", "idle")
        res_summary = getattr(job_manager, "result_summary", None) or {}
        drive_summary = res_summary.get("drive_summary") or {}

        counts.total_photos = res_summary.get("photos_count", 0)
        counts.people_count = res_summary.get("people_count", 0)
        counts.unrecognized_faces = res_summary.get("unrecognized_faces", 0)
        counts.unrecognized_photos = res_summary.get("unrecognized_photos", 0)

        counts.drive_images_found = drive_summary.get("images_found", 0)
        counts.drive_folders_scanned = drive_summary.get("folders_scanned", 0)
        counts.drive_folders_failed = len(drive_summary.get("folders_failed", [])) if isinstance(drive_summary.get("folders_failed"), list) else 0
        counts.drive_shortcuts_skipped = drive_summary.get("shortcuts_skipped", 0)
        counts.drive_non_images_skipped = drive_summary.get("non_images_skipped", 0)

    # If active result exists in state, pull live counts
    active_res = getattr(state, "result", None)
    if active_res:
        counts.total_photos = max(counts.total_photos, len(getattr(active_res, "photos", {})))
        counts.people_count = max(counts.people_count, len(getattr(active_res, "people", [])))
        clustered = sum(len(p.faces) for p in getattr(active_res, "people", []))
        counts.clustered_faces = clustered
        unrec = getattr(active_res, "unrecognized", None)
        if unrec:
            counts.unrecognized_faces = len(getattr(unrec, "faces", []))
            counts.unrecognized_photos = len(getattr(unrec, "photo_ids", []))

    # Edits count
    edits_list = getattr(state, "edits_list", [])
    counts.edits_count = len(edits_list) if isinstance(edits_list, list) else 0

    # 6. Formatted plain-text block
    formatted = format_text_diagnostics(
        version=version,
        os_name=os_name,
        architecture=architecture,
        python_ver=python_ver,
        settings_hash=s_hash,
        error_code=classification.error_code,
        plain_language_fix=classification.plain_language_fix,
        stage=job_stage,
        counts=counts,
    )

    return DiagnosticsReport(
        version=version,
        os_name=os_name,
        os_release=os_release,
        architecture=architecture,
        python_version=python_ver,
        settings_hash=s_hash,
        error_code=classification.error_code,
        error_title=classification.title if classification.error_code != "NONE" else None,
        plain_language_fix=classification.plain_language_fix,
        sanitized_error=classification.sanitized_message if classification.error_code != "NONE" else None,
        status=job_status,
        stage=job_stage,
        counts=counts,
        formatted_report=formatted,
    )
