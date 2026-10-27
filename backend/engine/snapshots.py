"""Snapshot manager for CatLog projects (Phase V2-3 Incremental Undo & Rollback).

Provides atomic backups of project metadata (people.json, manifest.json, edits.json,
suggestions.json, id_map.json) before incremental mutations, enabling safe one-click undo.
"""

from __future__ import annotations
import os
import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_snapshots_dir(work_dir: Path | str) -> Path:
    """Returns the snapshots directory for a given work directory."""
    p = Path(work_dir).resolve() / "snapshots"
    p.mkdir(parents=True, exist_ok=True)
    return p


def create_snapshot(
    work_dir: Path | str,
    export_dir: Optional[Path | str] = None,
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates an atomic snapshot of project state before a mutation.
    Returns snapshot metadata dict.
    """
    work_p = Path(work_dir).resolve()
    snap_root = get_snapshots_dir(work_p)

    timestamp = datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    snapshot_id = f"snap_{timestamp}"
    snap_dir = snap_root / snapshot_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    files_saved = []
    target_files = [
        "people.json",
        "manifest.json",
        "edits.json",
        "suggestions.json",
        "id_map.json",
        "what_changed.json",
    ]
    for fn in target_files:
        src = work_p / fn
        if src.is_file():
            shutil.copy2(src, snap_dir / fn)
            files_saved.append(fn)

    if export_dir:
        exp_p = Path(export_dir).resolve()
        for fn in ["people.json", "manifest.json"]:
            if fn not in files_saved:
                src = exp_p / fn
                if src.is_file():
                    shutil.copy2(src, snap_dir / fn)
                    files_saved.append(fn)

    people_count = 0
    photo_count = 0
    if (snap_dir / "people.json").is_file():
        try:
            with open(snap_dir / "people.json", "r", encoding="utf-8") as f:
                pj_data = json.load(f)
            people_count = len(pj_data.get("people", []))
            ph_dict = pj_data.get("photos", {})
            photo_count = len(ph_dict)
            if photo_count == 0:
                pids = set(pj_data.get("unrecognized", {}).get("photo_ids", []))
                for p_item in pj_data.get("people", []):
                    pids.update(p_item.get("photos") or p_item.get("photo_ids", []))
                photo_count = len(pids)
        except Exception:
            pass

    meta = {
        "snapshot_id": snapshot_id,
        "created_at": datetime.datetime.now().astimezone().isoformat(),
        "label": label or "Pre-incremental scan snapshot",
        "work_dir": str(work_p),
        "export_dir": str(Path(export_dir).resolve()) if export_dir else None,
        "files_saved": files_saved,
        "counts": {
            "people": people_count,
            "photos": photo_count,
        },
    }

    with open(snap_dir / "snapshot_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


def list_snapshots(work_dir: Path | str) -> List[Dict[str, Any]]:
    """Lists all available snapshots for a project, sorted newest first."""
    work_p = Path(work_dir).resolve()
    snap_root = work_p / "snapshots"
    if not snap_root.is_dir():
        return []

    snapshots = []
    for d in snap_root.iterdir():
        if d.is_dir() and (d / "snapshot_meta.json").is_file():
            try:
                with open(d / "snapshot_meta.json", "r", encoding="utf-8") as f:
                    meta = json.load(f)
                snapshots.append(meta)
            except Exception:
                pass

    snapshots.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return snapshots


def restore_snapshot(
    work_dir: Path | str,
    export_dir: Optional[Path | str] = None,
    snapshot_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Restores the specified snapshot (or latest if snapshot_id is None).
    Overwrites people.json, manifest.json, edits.json in work_dir and export_dir.
    Returns the restored snapshot metadata.
    """
    work_p = Path(work_dir).resolve()
    snap_root = work_p / "snapshots"
    if not snap_root.is_dir():
        raise FileNotFoundError(f"No snapshots directory found in {work_p}")

    if snapshot_id:
        target_dir = snap_root / snapshot_id
    else:
        all_snaps = list_snapshots(work_p)
        if not all_snaps:
            raise FileNotFoundError(f"No snapshots found for project in {work_p}")
        target_dir = snap_root / all_snaps[0]["snapshot_id"]

    if not target_dir.is_dir() or not (target_dir / "snapshot_meta.json").is_file():
        raise FileNotFoundError(f"Snapshot '{snapshot_id}' does not exist or is corrupt.")

    with open(target_dir / "snapshot_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Restore files to work_dir
    for fn in ["people.json", "manifest.json", "edits.json", "suggestions.json", "id_map.json", "what_changed.json"]:
        src = target_dir / fn
        dest = work_p / fn
        if src.is_file():
            shutil.copy2(src, dest)
        elif dest.is_file() and fn == "what_changed.json":
            # If what_changed didn't exist in snapshot, remove current one to avoid stale diffs
            try:
                dest.unlink()
            except Exception:
                pass

    # Restore files to export_dir if provided or recorded in meta
    exp_target = Path(export_dir).resolve() if export_dir else (Path(meta["export_dir"]).resolve() if meta.get("export_dir") else None)
    if exp_target and exp_target.is_dir():
        for fn in ["people.json", "manifest.json"]:
            src = target_dir / fn
            if src.is_file():
                shutil.copy2(src, exp_target / fn)

    return meta
