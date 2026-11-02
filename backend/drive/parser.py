"""Google Drive folder URL and ID parsing and validation."""

from __future__ import annotations
import re
from urllib.parse import urlparse, parse_qs

from typing import Optional, Dict

# Drive folder IDs are typically 25 to 55 alphanumeric characters (with _ and -)
DRIVE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{20,60}$")


def detect_unsupported_cloud_link(url_or_id: str) -> Optional[Dict[str, str]]:
    """
    Detect unsupported cloud service links (Google Photos, Dropbox, OneDrive, iCloud, Box)
    and return structured guidance detailing why it cannot be read and how to import photos.
    """
    if not url_or_id or not isinstance(url_or_id, str):
        return None

    s = url_or_id.strip().lower()

    # 1. Google Photos (photos.google.com, photos.app.goo.gl)
    if "photos.google.com" in s or "photos.app.goo.gl" in s:
        return {
            "service": "Google Photos",
            "code": "GOOGLE_PHOTOS_LINK",
            "title": "Google Photos Album Link Not Supported Directly",
            "message": (
                "Google Photos album links cannot be scanned directly because Google's Photos Library API "
                "restricts third-party access to albums not created by the application (effective March 2025). "
                "Please download your album as a ZIP file (or export to Google Drive) and select it as a "
                "local ZIP or Google Drive source in CatLog."
            ),
            "how_to_fix": (
                "In Google Photos, open the album, click More options (⋮) -> 'Download all' to download a ZIP file "
                "(or export to Google Drive), then choose 'Folder or Zip' here."
            ),
        }

    # 2. Dropbox (dropbox.com)
    if "dropbox.com" in s:
        return {
            "service": "Dropbox",
            "code": "DROPBOX_LINK",
            "title": "Dropbox Link Not Supported Directly",
            "message": (
                "Dropbox links cannot be accessed directly via URL. Please download or sync the folder "
                "to your computer, or export the photos to Google Drive."
            ),
            "how_to_fix": (
                "Download the Dropbox folder as a ZIP file or sync locally, then choose 'Folder or Zip' in CatLog."
            ),
        }

    # 3. OneDrive / SharePoint (onedrive.live.com, 1drv.ms, sharepoint.com)
    if "onedrive.live.com" in s or "1drv.ms" in s or "sharepoint.com" in s:
        return {
            "service": "OneDrive",
            "code": "ONEDRIVE_LINK",
            "title": "OneDrive Link Not Supported Directly",
            "message": (
                "OneDrive / SharePoint links cannot be accessed directly via URL. Please sync or download the folder "
                "to your computer, or export the photos to Google Drive."
            ),
            "how_to_fix": (
                "Download the OneDrive folder as a ZIP file or sync locally, then choose 'Folder or Zip' in CatLog."
            ),
        }

    # 4. Apple iCloud (icloud.com)
    if "icloud.com" in s:
        return {
            "service": "iCloud",
            "code": "ICLOUD_LINK",
            "title": "iCloud Link Not Supported Directly",
            "message": (
                "iCloud Shared Album links cannot be accessed directly via URL. Please download the photos "
                "to your computer or export them into a ZIP file."
            ),
            "how_to_fix": (
                "In the Photos app or iCloud.com, select the photos and download or export them to a local "
                "folder or ZIP file, then choose 'Folder or Zip' in CatLog."
            ),
        }

    # 5. Box (box.com)
    if "box.com" in s or "box.net" in s:
        return {
            "service": "Box",
            "code": "BOX_LINK",
            "title": "Box Link Not Supported Directly",
            "message": (
                "Box links cannot be accessed directly via URL. Please download or sync the folder to your computer."
            ),
            "how_to_fix": (
                "Download the Box folder as a ZIP file or sync locally, then choose 'Folder or Zip' in CatLog."
            ),
        }

    return None


def is_drive_folder_input(input_str: str) -> bool:
    """Check if the given string is a valid Google Drive folder URL or ID."""
    if not input_str or not isinstance(input_str, str):
        return False
    try:
        parse_drive_folder_id(input_str)
        return True
    except Exception:
        return False


def parse_drive_folder_id(url_or_id: str) -> str:
    """
    Extract and validate a Google Drive folder ID from a URL or raw ID string.

    Supported formats:
    - https://drive.google.com/drive/folders/<FOLDER_ID>
    - https://drive.google.com/drive/u/<NUM>/folders/<FOLDER_ID>
    - https://drive.google.com/drive/mobile/folders/<FOLDER_ID>
    - https://drive.google.com/open?id=<FOLDER_ID>
    - https://drive.google.com/folderview?id=<FOLDER_ID>
    - Raw ID: <FOLDER_ID> (20-60 alphanumeric characters, dashes, underscores)

    Raises:
        ValueError: If input is invalid, not a Drive folder, or a file link.
    """
    if not url_or_id or not isinstance(url_or_id, str):
        raise ValueError("Google Drive link or ID cannot be empty.")

    s = url_or_id.strip()
    if not s:
        raise ValueError("Google Drive link or ID cannot be empty.")

    # 0. Check for known unsupported cloud service links first (Google Photos, Dropbox, etc.)
    cloud_info = detect_unsupported_cloud_link(s)
    if cloud_info:
        raise ValueError(cloud_info["message"])

    # 1. Reject Drive file links with clear guidance
    if "drive.google.com/file/d/" in s:
        raise ValueError(
            "Detected a Google Drive file link, not a folder link. "
            "Please provide the link to the containing folder instead."
        )
    if "docs.google.com" in s:
        raise ValueError("Detected a Google Docs/Sheets link. Please provide a Google Drive folder link.")

    # 2. Check for URL format
    if s.startswith("http://") or s.startswith("https://"):
        parsed = urlparse(s)
        if "drive.google.com" not in parsed.netloc:
            raise ValueError(f"Not a Google Drive URL: '{parsed.netloc}'")

        path = parsed.path
        query = parse_qs(parsed.query)

        # Check for query param 'id' (e.g. /open?id=... or /folderview?id=...)
        if "id" in query and query["id"]:
            candidate = query["id"][0].strip()
            if DRIVE_ID_PATTERN.match(candidate):
                return candidate
            raise ValueError(f"Invalid Google Drive folder ID in URL query: '{candidate}'")

        # Check for /folders/<ID> in path
        match = re.search(r"/folders/([a-zA-Z0-9_-]+)", path)
        if match:
            candidate = match.group(1).strip()
            if DRIVE_ID_PATTERN.match(candidate):
                return candidate
            raise ValueError(f"Invalid Google Drive folder ID in URL path: '{candidate}'")

        raise ValueError(
            f"Could not extract a folder ID from Google Drive URL: '{s}'. "
            "Expected format: 'https://drive.google.com/drive/folders/<ID>'"
        )

    # 3. Direct raw ID check
    # Strip any accidentally pasted query strings
    if "?" in s:
        s = s.split("?")[0]
    s = s.rstrip("/")

    if DRIVE_ID_PATTERN.match(s):
        return s

    raise ValueError(
        f"Invalid Google Drive folder ID: '{s}'. "
        "Drive folder IDs are typically 25 to 55 alphanumeric characters (with '-' and '_')."
    )
