"""Application update check service using GitHub Releases API (SPEC & BUILD_PLAN V2-8).

Guarantees:
- Notify only: never automatically downloads, executes, or installs binaries.
- Zero telemetry: no user metrics, IP logging, or unique identifiers are sent.
- Offline-safe: network errors, offline states, or GitHub rate limits fail silently and return update_available=False.
- Low-latency timeout (3.0s).
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from backend.version import __version__, is_newer_version

GITHUB_REPO = "Sufiyan-Shiraj/face-clubbing"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def check_app_update(
    api_url: Optional[str] = None,
    current_version: Optional[str] = None,
    timeout: float = 3.0,
) -> Dict[str, Any]:
    """Checks the official GitHub Releases API for a newer CatLog version.
    
    Returns:
        dict: {
            "current_version": str,
            "latest_version": str,
            "update_available": bool,
            "release_name": str,
            "release_url": str,
            "release_notes": str,
            "published_at": str,
            "checked_online": bool,
            "error": Optional[str],
        }
    """
    cur_ver = current_version or __version__
    url = api_url or RELEASES_API_URL

    res: Dict[str, Any] = {
        "current_version": cur_ver,
        "latest_version": cur_ver,
        "update_available": False,
        "release_name": "",
        "release_url": f"https://github.com/{GITHUB_REPO}/releases",
        "release_notes": "",
        "published_at": "",
        "checked_online": False,
        "error": None,
    }

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"CatLog/{cur_ver} (desktop-app; offline-safe)",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                payload = json.loads(resp.read().decode("utf-8"))
                tag_name = payload.get("tag_name", "").lstrip("vV")
                if tag_name:
                    res["latest_version"] = tag_name
                    res["release_name"] = payload.get("name") or f"CatLog v{tag_name}"
                    res["release_url"] = payload.get("html_url") or res["release_url"]
                    res["release_notes"] = payload.get("body") or ""
                    res["published_at"] = payload.get("published_at") or ""
                    res["checked_online"] = True
                    res["update_available"] = is_newer_version(cur_ver, tag_name)
    except urllib.error.HTTPError as e:
        # e.g. 404 if no release exists yet, or 403 rate limit
        res["error"] = f"HTTP {e.code}"
    except Exception as e:
        # Offline, DNS failure, timeout
        res["error"] = str(e)

    return res

