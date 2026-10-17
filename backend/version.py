"""Single source of truth for CatLog application version."""

from __future__ import annotations
import sys
from pathlib import Path


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
