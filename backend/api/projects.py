"""Recent projects manager for PhotoSorter (SPEC Open saved project).

Stores metadata for recently opened or exported projects in ~/.photosorter/projects.json
(outside the repository).

Privacy & Security Guarantees:
- Only paths, timestamps, and high-level counts are persisted.
- NEVER saves Google Drive API keys or credentials.
- NEVER persists face embeddings, vectors, or raw photos.
- Removing an entry from projects.json NEVER deletes files or folders on disk.
"""

from __future__ import annotations
import os
import re
import json
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_projects_file() -> Path:
    """Returns path to projects.json, allowing override via PHOTOSORTER_PROJECTS_FILE for test isolation."""
    env_override = os.environ.get("PHOTOSORTER_PROJECTS_FILE")
    if env_override:
        p = Path(env_override).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    default_dir = Path.home() / ".photosorter"
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir / "projects.json"


def _sanitize_source_description(source: Optional[str]) -> str:
    """Sanitizes source description to ensure NO API keys or sensitive query parameters are stored."""
    if not source:
        return "Local Folder"
    s = str(source).strip()
    # Strip any api_key or key query parameters if a URL was provided
    if "key=" in s.lower() or "api_key=" in s.lower():
        s = re.sub(r'([?&]key=[^&]+)', '', s, flags=re.IGNORECASE)
        s = re.sub(r'([?&]api_key=[^&]+)', '', s, flags=re.IGNORECASE)

    try:
        from backend.drive.parser import parse_drive_folder_id, is_drive_folder_input
        if is_drive_folder_input(s):
            fid = parse_drive_folder_id(s)
            return f"Drive folder {fid}"
    except Exception:
        pass

    # Never persist strings that look like raw Google API keys (AIza...)
    if "AIza" in s:
        s = "[Google Drive]"
    return s


def load_recent_projects() -> List[Dict[str, Any]]:
    """Loads all recent projects from projects.json sorted by last_opened descending."""
    file_path = get_projects_file()
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        projects = data.get("projects", [])
        if not isinstance(projects, list):
            return []
    except Exception:
        # Corrupt projects.json is handled safely without crashing
        return []

    # Enrich each entry with current on-disk existence check
    enriched: List[Dict[str, Any]] = []
    for p in projects:
        if not isinstance(p, dict) or "work_dir" not in p:
            continue
        work_path = Path(p["work_dir"])
        entry = dict(p)
        entry["exists"] = work_path.exists() and work_path.is_dir()
        if "source_description" in entry:
            entry["source_description"] = _sanitize_source_description(entry["source_description"])
        enriched.append(entry)

    # Sort descending by last_opened
    enriched.sort(key=lambda x: x.get("last_opened", ""), reverse=True)
    return enriched


def save_recent_project(
    work_dir: Path | str,
    export_path: Optional[Path | str] = None,
    source_description: Optional[str] = None,
    counts: Optional[Dict[str, int]] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saves or updates a project entry in projects.json.
    Keyed stably by canonical work_dir.
    """
    file_path = get_projects_file()
    resolved_work = str(Path(work_dir).resolve())
    resolved_export = str(Path(export_path).resolve()) if export_path else None

    # Stable 12-char ID derived from canonical work_dir
    project_id = hashlib.sha256(resolved_work.encode("utf-8")).hexdigest()[:12]

    # Derive human-friendly display name
    if not name:
        if resolved_export and Path(resolved_export).name not in ("export", ""):
            name = Path(resolved_export).name
        elif Path(resolved_work).name not in ("export.work", "work", ""):
            name = Path(resolved_work).name
        else:
            name = Path(resolved_work).parent.name or "PhotoSorter Project"

    clean_source = _sanitize_source_description(source_description)

    now_iso = datetime.datetime.now().astimezone().isoformat()

    existing_projects = []
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            existing_projects = data.get("projects", [])
            if not isinstance(existing_projects, list):
                existing_projects = []
        except Exception:
            existing_projects = []

    # Update or add
    updated = False
    is_existing = Path(resolved_work).exists() and Path(resolved_work).is_dir()
    project_entry: Dict[str, Any] = {
        "id": project_id,
        "name": name,
        "work_dir": resolved_work,
        "export_path": resolved_export,
        "source_description": clean_source,
        "last_opened": now_iso,
        "counts": counts or {"people": 0, "photos": 0},
    }

    new_list: List[Dict[str, Any]] = []
    for item in existing_projects:
        if isinstance(item, dict) and (item.get("id") == project_id or item.get("work_dir") == resolved_work):
            # Merge existing counts if not provided in update
            if not counts and "counts" in item:
                project_entry["counts"] = item["counts"]
            if not export_path and item.get("export_path"):
                project_entry["export_path"] = item["export_path"]
            if not source_description and item.get("source_description"):
                project_entry["source_description"] = item["source_description"]
            new_list.append(project_entry)
            updated = True
        else:
            if isinstance(item, dict):
                cleaned = dict(item)
                cleaned.pop("exists", None)
                new_list.append(cleaned)
            else:
                new_list.append(item)

    if not updated:
        new_list.append(project_entry)

    # Sort descending by last_opened
    new_list.sort(key=lambda x: x.get("last_opened", ""), reverse=True)

    # Atomic write to projects.json
    tmp_path = file_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "projects": new_list}, f, indent=2)
    tmp_path.replace(file_path)

    return dict(project_entry, exists=is_existing)


def remove_recent_project(project_id: str) -> bool:
    """
    Removes a project entry from projects.json.
    Strictly touches metadata only: NEVER deletes or modifies files on disk.
    """
    file_path = get_projects_file()
    if not file_path.exists():
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        projects = data.get("projects", [])
    except Exception:
        return False

    original_len = len(projects)
    filtered = [
        p for p in projects
        if isinstance(p, dict) and p.get("id") != project_id and p.get("work_dir") != project_id
    ]

    if len(filtered) == original_len:
        return False

    tmp_path = file_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "projects": filtered}, f, indent=2)
    tmp_path.replace(file_path)
    return True


def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """Looks up a project entry by its id or canonical work_dir."""
    projects = load_recent_projects()
    for p in projects:
        if p.get("id") == project_id or p.get("work_dir") == str(Path(project_id).resolve()):
            return p
    return None
