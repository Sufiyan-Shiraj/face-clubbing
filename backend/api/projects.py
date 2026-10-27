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
    """Returns path to projects.json, allowing override via CATLOG_PROJECTS_FILE or PHOTOSORTER_PROJECTS_FILE for test isolation."""
    env_override = os.environ.get("CATLOG_PROJECTS_FILE") or os.environ.get("PHOTOSORTER_PROJECTS_FILE")
    if env_override:
        p = Path(env_override).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    from backend.drive.config import get_user_settings_dir
    default_dir = get_user_settings_dir()
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


def resolve_project_export_path(work_dir: Path | str, export_path: Optional[Path | str] = None) -> Optional[str]:
    """
    Resolves the exact folder containing people.json for a project.
    Handles nested export subfolders (e.g. export/EVENT/EVENT Images vs export/EVENT),
    sibling folders, and project name variations.
    """
    work_p = Path(work_dir).resolve() if work_dir else None

    if export_path:
        exp = Path(export_path).resolve()
        if (exp / "people.json").is_file():
            return str(exp)

        # 1. Check if export_path contains people.json in any subfolder
        if exp.exists() and exp.is_dir():
            for sub in exp.glob("**/people.json"):
                if sub.is_file():
                    return str(sub.parent)

        # 2. Check sibling directories in parent folder
        if exp.parent.exists():
            cand_img = exp.parent / f"{exp.name} Images"
            if (cand_img / "people.json").is_file():
                return str(cand_img)

            for sibling in exp.parent.glob(f"*{exp.name}*"):
                if (sibling / "people.json").is_file():
                    return str(sibling)

            for p in exp.parent.glob("**/people.json"):
                if exp.name.lower() in str(p).lower():
                    return str(p.parent)

    # 3. Check work_dir
    if work_p:
        if (work_p / "people.json").is_file():
            return str(work_p)

        # 4. Check sibling of work_p if work_p is *.work
        if work_p.name.endswith(".work") and work_p.name.lower() not in ("export.work", ".work"):
            sibling_exp = work_p.parent / work_p.name.removesuffix(".work")
            if (sibling_exp / "people.json").is_file():
                return str(sibling_exp)
            for sub in sibling_exp.glob("**/people.json"):
                if sub.is_file():
                    return str(sub.parent)

    # 5. Check workspace export directory
    repo_export = Path.cwd() / "export"
    if repo_export.exists():
        name_hint = Path(export_path).name if export_path else (work_p.name.removesuffix(".work") if work_p else "")
        if name_hint and name_hint.lower() not in ("export", "work", "export.work", ".work", ""):
            if (repo_export / name_hint / "people.json").is_file():
                return str(repo_export / name_hint)
            if (repo_export / f"{name_hint} Images" / "people.json").is_file():
                return str(repo_export / f"{name_hint} Images")
            for p in repo_export.glob(f"**/*{name_hint}*/**/people.json"):
                if p.is_file():
                    return str(p.parent)

    return str(Path(export_path).resolve()) if export_path else None


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

    # Enrich each entry with current on-disk existence check and auto-heal paths/counts
    enriched: List[Dict[str, Any]] = []
    projects_mutated = False
    for p in projects:
        if not isinstance(p, dict) or "work_dir" not in p:
            continue
        work_path = Path(p["work_dir"])
        entry = dict(p)
        entry["exists"] = work_path.exists() and work_path.is_dir()
        if "source_description" in entry:
            entry["source_description"] = _sanitize_source_description(entry["source_description"])

        # Auto-heal export_path if subfolder with people.json exists
        resolved_exp = resolve_project_export_path(p["work_dir"], p.get("export_path"))
        if resolved_exp and resolved_exp != p.get("export_path"):
            entry["export_path"] = resolved_exp
            projects_mutated = True

        # Sync true counts from people.json if available
        exp_to_check = entry.get("export_path")
        if exp_to_check:
            pj_path = Path(exp_to_check) / "people.json"
            if pj_path.is_file():
                try:
                    with open(pj_path, "r", encoding="utf-8") as f:
                        pj_data = json.load(f)
                    p_cnt = len(pj_data.get("people", []))
                    ph_dict = pj_data.get("photos", {})
                    ph_cnt = len(ph_dict)
                    if ph_cnt == 0:
                        ph_ids = set(pj_data.get("unrecognized", {}).get("photo_ids", []))
                        for p_item in pj_data.get("people", []):
                            ph_ids.update(p_item.get("photos") or p_item.get("photo_ids", []))
                        ph_cnt = len(ph_ids)
                    curr_counts = entry.get("counts", {})
                    if curr_counts.get("people") != p_cnt or curr_counts.get("photos") != ph_cnt:
                        entry["counts"] = {"people": p_cnt, "photos": ph_cnt}
                        projects_mutated = True
                except Exception:
                    pass

        if entry.get("schema_version", 1) < 2:
            entry["schema_version"] = 2
            projects_mutated = True
        if "sources" not in entry or not entry["sources"]:
            src_desc = entry.get("source_description", "Local Folder")
            is_drive_src = "Drive" in src_desc or "http" in src_desc
            entry["sources"] = [
                {
                    "id": "src_01",
                    "kind": "drive" if is_drive_src else "local",
                    "path_or_url": src_desc,
                    "label": src_desc,
                    "photo_count": entry.get("counts", {}).get("photos", 0),
                    "status": "completed",
                    "error": None,
                }
            ]
            projects_mutated = True

        enriched.append(entry)

    # Persist healed paths and counts back to projects.json so bad historical data is permanently repaired
    if projects_mutated:
        try:
            to_save = []
            for item in enriched:
                cleaned = dict(item)
                cleaned.pop("exists", None)
                to_save.append(cleaned)
            tmp_path = file_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "projects": to_save}, f, indent=2)
            tmp_path.replace(file_path)
        except Exception:
            pass

    # Sort descending by last_opened
    enriched.sort(key=lambda x: x.get("last_opened", ""), reverse=True)
    return enriched


def save_recent_project(
    work_dir: Path | str,
    export_path: Optional[Path | str] = None,
    source_description: Optional[str] = None,
    counts: Optional[Dict[str, int]] = None,
    name: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    schema_version: int = 2,
) -> Dict[str, Any]:
    """
    Saves or updates a project entry in projects.json.
    Keyed stably by canonical work_dir.
    """
    file_path = get_projects_file()
    resolved_work = str(Path(work_dir).resolve())
    resolved_export = resolve_project_export_path(work_dir, export_path)

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
        "schema_version": schema_version,
        "sources": sources or [],
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
            if not sources and item.get("sources"):
                project_entry["sources"] = item["sources"]
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
