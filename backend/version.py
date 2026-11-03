"""Single source of truth for CatLog application version."""

from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Tuple


def get_version() -> str:
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "VERSION")
    candidates.append(Path(__file__).resolve().parent.parent / "VERSION")
    candidates.append(Path("VERSION"))
    for p in candidates:
        try:
            if p.is_file():
                v = p.read_text(encoding="utf-8").strip()
                if v:
                    return v
        except Exception:
            pass
    return "0.1.0-rc1"


__version__ = get_version()


def parse_semver(v: str) -> Tuple[int, int, int, str]:
    """Parses a version string into (major, minor, patch, prerelease).
    
    Examples:
        '0.1.0' -> (0, 1, 0, '')
        'v0.1.0-rc1' -> (0, 1, 0, 'rc1')
        '1.2.3' -> (1, 2, 3, '')
    """
    clean = v.strip().lstrip("vV")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", clean)
    if not match:
        return (0, 0, 0, clean)
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    prerelease = match.group(4) or ""
    return (major, minor, patch, prerelease)


def is_newer_version(current: str, candidate: str) -> bool:
    """Returns True if candidate is strictly newer than current.
    
    A non-prerelease version is newer than a prerelease of the same (major, minor, patch).
    Example: 0.1.0 is newer than 0.1.0-rc1.
    """
    c_maj, c_min, c_pat, c_pre = parse_semver(current)
    k_maj, k_min, k_pat, k_pre = parse_semver(candidate)

    if (k_maj, k_min, k_pat) > (c_maj, c_min, c_pat):
        return True
    if (k_maj, k_min, k_pat) < (c_maj, c_min, c_pat):
        return False

    # Same major.minor.patch:
    # If current is prerelease (e.g. 'rc1') and candidate is final release (''):
    if c_pre and not k_pre:
        return True
    # If candidate is also prerelease or both are final:
    if c_pre and k_pre and k_pre > c_pre:
        return True
    return False
