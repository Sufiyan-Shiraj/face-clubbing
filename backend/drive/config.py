"""Google Drive configuration, local profile settings management, and API key masking."""

from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any


def get_user_settings_dir() -> Path:
    """Return the platform-appropriate user settings directory (~/.photosorter)."""
    user_home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    settings_dir = user_home / ".photosorter"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


def get_settings_file_path() -> Path:
    """Return path to ~/.photosorter/settings.json."""
    return get_user_settings_dir() / "settings.json"


def load_local_settings() -> Dict[str, Any]:
    """Load local app settings from ~/.photosorter/settings.json."""
    path = get_settings_file_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_local_settings(settings: Dict[str, Any]) -> None:
    """Save local app settings to ~/.photosorter/settings.json."""
    path = get_settings_file_path()
    try:
        current = load_local_settings()
        current.update(settings)
        # Write securely
        with open(path, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write settings to {path}: {e}")


def get_drive_api_key() -> Optional[str]:
    """
    Retrieve Google Drive API key.
    Precedence:
    1. DRIVE_API_KEY environment variable.
    2. drive_api_key stored in ~/.photosorter/settings.json.
    """
    env_key = os.environ.get("DRIVE_API_KEY", "").strip()
    if env_key:
        return env_key

    local_settings = load_local_settings()
    stored_key = local_settings.get("drive_api_key", "")
    if isinstance(stored_key, str) and stored_key.strip():
        return stored_key.strip()

    return None


def set_drive_api_key(api_key: str) -> None:
    """Save Google Drive API key to ~/.photosorter/settings.json."""
    clean_key = api_key.strip() if api_key else ""
    save_local_settings({"drive_api_key": clean_key})


def mask_api_key(key: Optional[str]) -> str:
    """
    Mask an API key for safe display in UI or logs.
    Example: AIzaSyD1234567890abcdef -> AIzaSy...cdef
    """
    if not key:
        return ""
    k = key.strip()
    if len(k) <= 8:
        return "***"
    return f"{k[:6]}...{k[-4:]}"


def get_masked_drive_api_key() -> str:
    """Return masked drive API key from environment or local profile."""
    return mask_api_key(get_drive_api_key())


def sanitize_message_for_logs(message: Any) -> str:
    """Remove potential API keys from error messages or log output."""
    if message is None:
        return ""
    msg_str = str(message)

    def _mask_match(m):
        raw = m.group(0)
        return mask_api_key(raw)

    sanitized = re.sub(r"AIza[0-9A-Za-z-_]{10,}", _mask_match, msg_str)
    return sanitized


sanitize_drive_logs = sanitize_message_for_logs

