"""Google Drive folder URL and ID parsing and validation."""

from __future__ import annotations
import re
from urllib.parse import urlparse, parse_qs

# Drive folder IDs are typically 25 to 55 alphanumeric characters (with _ and -)
DRIVE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{20,60}$")


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
