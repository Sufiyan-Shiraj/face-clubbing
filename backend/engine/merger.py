"""Project Merger module for CatLog (BUILD_PLAN Phase V2-4).

Merges two existing CatLog projects (A and B) into a brand-new project C:
- Original projects remain completely untouched.
- Union by photo ID; photos appearing in both projects are unified.
- Strict check on detection settings hash: projects must share the same settings hash
  (model_name, det_size, min_det_score, min_face_size, max_yaw, max_image_dim, flip_average),
  otherwise an error is raised (or re-detect required).
- Copies / unifies caches (thumbnails, crops, embedding json).
- Combines edits as order-independent rules:
  * Merge anchors: connected components across all merge operations.
  * Removes: union of (person anchors, face_id/photo_id) removal rules.
  * Assigns: union of face assignments.
  * Names: labels applied to matching people. If two projects give different custom names to
    the same person (connected component), this is flagged as a conflict.
  * Hides: union of hidden people rules.
- Conflict detection:
  * Name conflicts: different non-empty labels for the same cluster/person.
  * Assign vs Remove conflicts: a face assigned to a person in one project but removed in another.
- Merged project manifest records both parents as sources (with their original sources preserved).
- Invariant & Idempotence:
  * Merging project A with itself produces identical results (A + A == A).
  * Merging A + B is commutative with B + A (same people, same clusters, same photo count).
"""

from __future__ import annotations
import os
import json
import shutil
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

from backend.engine.models import (
    PersonCluster,
    UnrecognizedGroup,
    PhotoRecord,
    FaceDetection,
    EngineResult,
)
from backend.engine.cache import EmbeddingCache, compute_settings_hash
from backend.engine.clusterer import FaceClusterer
from backend.engine.edits import apply_edits
from backend.engine.exporter import BundleExporter


class MergeConflict:
    """Represents a conflict detected when merging two projects."""

    def __init__(
        self,
        conflict_type: str,  # "name_conflict" | "assign_vs_remove"
        description: str,
        entity_id: str,
        val_a: Any,
        val_b: Any,
        resolution_strategy: str = "review_needed",
    ):
        self.conflict_type = conflict_type
        self.description = description
        self.entity_id = entity_id
        self.val_a = val_a
        self.val_b = val_b
        self.resolution_strategy = resolution_strategy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "description": self.description,
            "entity_id": self.entity_id,
            "val_a": self.val_a,
            "val_b": self.val_b,
            "resolution_strategy": self.resolution_strategy,
        }


def read_project_data(
    work_dir: Path | str,
    export_dir: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Reads all necessary data from a project work/export directory."""
    work_p = Path(work_dir).resolve()
    exp_p = Path(export_dir).resolve() if export_dir else None

    # Find people.json
    people_path = None
    for cand in [work_p / "people.json", exp_p / "people.json" if exp_p else None]:
        if cand and cand.is_file():
            people_path = cand
            break

    if not people_path:
        raise FileNotFoundError(f"Cannot find people.json in {work_p} or {exp_p}")

    with open(people_path, "r", encoding="utf-8") as f:
        people_data = json.load(f)

    # Find manifest.json
    manifest_data = {}
    for cand in [work_p / "manifest.json", exp_p / "manifest.json" if exp_p else None]:
        if cand and cand.is_file():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    break
            except Exception:
                pass

    # Find edits.json
    edits_data = {"version": 1, "edits": []}
    edits_cand = work_p / "edits.json"
    if edits_cand.is_file():
        try:
            with open(edits_cand, "r", encoding="utf-8") as f:
                edits_data = json.load(f)
        except Exception:
            pass

    # Read cached PhotoRecords from work_p / cache
    cache = EmbeddingCache(work_p)
    photos = cache.load_all()

    return {
        "work_dir": work_p,
        "export_dir": exp_p,
        "people_data": people_data,
        "manifest_data": manifest_data,
        "edits_data": edits_data,
        "photos": photos,
        "cache": cache,
    }


def verify_settings_compatibility(
    proj_a: Dict[str, Any],
    proj_b: Dict[str, Any],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks if two projects have matching settings hashes.
    Returns (is_compatible, hash_a, hash_b).
    """
    def extract_hash(proj: Dict[str, Any]) -> str:
        # Check cached photos first
        for rec in proj["photos"].values():
            fpath = proj["work_dir"] / f"{rec.photo_id}.json"
            if fpath.is_file():
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        d = json.load(f)
                        h = d.get("settings_hash")
                        if h:
                            return str(h)
                except Exception:
                    pass
        # Fallback to manifest settings hash
        mf = proj.get("manifest_data", {})
        if "settings_hash" in mf:
            return str(mf["settings_hash"])
        # Default fallback
        return compute_settings_hash()

    hash_a = extract_hash(proj_a)
    hash_b = extract_hash(proj_b)
    return (hash_a == hash_b), hash_a, hash_b


class DisjointSet:
    """Disjoint-set / Union-Find for grouping anchor faces and clusters order-independently."""

    def __init__(self):
        self.parent: Dict[str, str] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            return x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            # Deterministic: point larger string to smaller string
            if root_x < root_y:
                self.parent[root_y] = root_x
            else:
                self.parent[root_x] = root_y


def combine_edits(
    edits_a: List[Dict[str, Any]],
    edits_b: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[MergeConflict]]:
    """
    Combines edits from Project A and Project B as order-independent rules.
    Detects:
    1. Name conflicts (two projects label the same entity differently).
    2. Assign vs Remove conflicts (one project assigns a face, another removes it from that person).
    """
    conflicts: List[MergeConflict] = []
    combined_edits: List[Dict[str, Any]] = []

    # 1. Merge Operations: Union-Find across anchor groups
    uf = DisjointSet()
    all_anchor_groups: List[List[str]] = []

    for edit in edits_a + edits_b:
        if edit.get("op") == "merge":
            groups = edit.get("anchors", [])
            for grp in groups:
                if grp:
                    all_anchor_groups.append(grp)
                    for i in range(1, len(grp)):
                        uf.union(grp[0], grp[i])
            # Union across groups in the same merge edit
            if len(groups) >= 2:
                first_face = groups[0][0] if groups[0] else None
                if first_face:
                    for g in groups[1:]:
                        if g:
                            uf.union(first_face, g[0])

    # Build canonical combined merge edits
    components: Dict[str, Set[str]] = defaultdict(set)
    for grp in all_anchor_groups:
        for fid in grp:
            root = uf.find(fid)
            components[root].add(fid)

    # For each component with > 1 face, if it spanned distinct anchor groups originally, preserve merge
    # Group original anchor groups by component root
    comp_groups: Dict[str, List[List[str]]] = defaultdict(list)
    seen_groups_sig: Set[str] = set()

    for edit in edits_a + edits_b:
        if edit.get("op") == "merge":
            groups = edit.get("anchors", [])
            for grp in groups:
                if grp:
                    sig = ",".join(sorted(grp))
                    if sig not in seen_groups_sig:
                        seen_groups_sig.add(sig)
                        root = uf.find(grp[0])
                        comp_groups[root].append(sorted(grp))

    for root, grps in sorted(comp_groups.items(), key=lambda x: x[0]):
        if len(grps) >= 2:
            combined_edits.append({
                "op": "merge",
                "anchors": grps,
            })

    # 2. Removes
    seen_removes: Set[str] = set()
    removes_map: Dict[Tuple[str, str], Dict[str, Any]] = {}  # (face_id/photo_id, root_anchor) -> edit

    for edit in edits_a + edits_b:
        if edit.get("op") == "remove":
            person_anchors = edit.get("person", [])
            face_id = edit.get("face_id")
            photo_id = edit.get("photo_id")
            item_id = face_id or photo_id
            if item_id and person_anchors:
                # Key by item_id and canonical root of the first anchor
                anchor_root = uf.find(person_anchors[0])
                sig = f"{item_id}::{anchor_root}"
                if sig not in seen_removes:
                    seen_removes.add(sig)
                    removes_map[(item_id, anchor_root)] = edit
                    combined_edits.append(edit)

    # 3. Assigns
    seen_assigns: Set[str] = set()
    for edit in edits_a + edits_b:
        if edit.get("op") == "assign":
            face_id = edit.get("face_id")
            person_anchors = edit.get("person", [])
            if face_id and person_anchors:
                anchor_root = uf.find(person_anchors[0])
                sig = f"{face_id}::{anchor_root}"
                if sig not in seen_assigns:
                    seen_assigns.add(sig)
                    # Check for assign vs remove conflict
                    if (face_id, anchor_root) in removes_map:
                        conflicts.append(
                            MergeConflict(
                                conflict_type="assign_vs_remove",
                                description=f"Face {face_id} was assigned to a person in one project but removed in another.",
                                entity_id=face_id,
                                val_a="assign",
                                val_b="remove",
                                resolution_strategy="review_needed",
                            )
                        )
                    combined_edits.append(edit)

    # 4. Names / Labels
    # Track labels assigned per canonical person (using UF root)
    person_labels: Dict[str, Dict[str, Any]] = {}  # anchor_root -> {label: str, edit: dict, project_source: str}

    for idx, edit_list in enumerate([edits_a, edits_b]):
        proj_tag = "Project A" if idx == 0 else "Project B"
        for edit in edit_list:
            if edit.get("op") == "name":
                label = (edit.get("label") or "").strip()
                person_anchors = edit.get("person", [])
                if label and person_anchors:
                    anchor_root = uf.find(person_anchors[0])
                    if anchor_root in person_labels:
                        existing = person_labels[anchor_root]
                        if existing["label"].lower() != label.lower():
                            # Conflicting names for same person!
                            conflicts.append(
                                MergeConflict(
                                    conflict_type="name_conflict",
                                    description=(
                                        f"Conflicting names for the same individual: "
                                        f"'{existing['label']}' ({existing['project_tag']}) vs '{label}' ({proj_tag})."
                                    ),
                                    entity_id=anchor_root,
                                    val_a=existing["label"],
                                    val_b=label,
                                    resolution_strategy="review_needed",
                                )
                            )
                    else:
                        person_labels[anchor_root] = {
                            "label": label,
                            "edit": edit,
                            "project_tag": proj_tag,
                        }

    # Add non-conflicting names (or first name as fallback while conflict is recorded)
    for info in person_labels.values():
        combined_edits.append(info["edit"])

    # 5. Hides
    seen_hides: Set[str] = set()
    for edit in edits_a + edits_b:
        if edit.get("op") == "hide":
            person_anchors = edit.get("person", [])
            if person_anchors:
                anchor_root = uf.find(person_anchors[0])
                if anchor_root not in seen_hides:
                    seen_hides.add(anchor_root)
                    combined_edits.append(edit)

    return combined_edits, conflicts


def merge_projects(
    proj_a_work: Path | str,
    proj_b_work: Path | str,
    target_work: Path | str,
    target_export: Optional[Path | str] = None,
    new_project_name: Optional[str] = None,
    distance_threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Core function for Phase V2-4: Merges two projects into target_work and target_export.

    Guarantees:
    1. Originals (proj_a_work, proj_b_work) are never modified.
    2. Equal settings hash required.
    3. Union by photo ID; duplicate photos merged.
    4. Caches (photos, thumbs, crops) copied to target.
    5. Edits combined order-independently with conflict detection.
    6. Both parents recorded as sources in manifest v2.
    7. Full static export bundle and people.json generated.
    """
    p_a = read_project_data(proj_a_work)
    p_b = read_project_data(proj_b_work)

    # 1. Verify settings compatibility
    compatible, hash_a, hash_b = verify_settings_compatibility(p_a, p_b)
    if not compatible:
        raise ValueError(
            f"Cannot merge projects with different detection settings hashes: "
            f"Project A has '{hash_a}', Project B has '{hash_b}'. Re-detection is required."
        )

    target_work_p = Path(target_work).resolve()
    target_export_p = Path(target_export).resolve() if target_export else (target_work_p.parent / target_work_p.name.removesuffix(".work"))

    target_work_p.mkdir(parents=True, exist_ok=True)
    target_export_p.mkdir(parents=True, exist_ok=True)

    target_thumbs = target_work_p / "thumbs"
    target_crops = target_work_p / "crops"
    target_thumbs.mkdir(parents=True, exist_ok=True)
    target_crops.mkdir(parents=True, exist_ok=True)

    # 2. Union Photos & Copy Caches
    all_photos: Dict[str, PhotoRecord] = {}
    shared_photo_count = 0

    # Project A photos
    for pid, rec in p_a["photos"].items():
        all_photos[pid] = rec

    # Project B photos
    for pid, rec in p_b["photos"].items():
        if pid in all_photos:
            shared_photo_count += 1
            # Merge photo attributes if Project B has download/share URLs that A lacked
            existing = all_photos[pid]
            if not getattr(existing, "download_url", None) and getattr(rec, "download_url", None):
                existing.download_url = rec.download_url
            if not getattr(existing, "drive_url", None) and getattr(rec, "drive_url", None):
                existing.drive_url = rec.drive_url
        else:
            all_photos[pid] = rec

    # Copy cache files for all photos
    target_cache = EmbeddingCache(target_work_p, settings_hash=hash_a)
    for pid, rec in all_photos.items():
        # Check if already in target cache
        if not target_cache.has(pid):
            # Look in Project A
            src_cache_json = p_a["work_dir"] / f"{pid}.json"
            if not src_cache_json.is_file():
                src_cache_json = p_b["work_dir"] / f"{pid}.json"
            if src_cache_json.is_file():
                shutil.copy2(src_cache_json, target_work_p / f"{pid}.json")

        # Copy thumb
        target_t = target_thumbs / f"{pid}.jpg"
        if not target_t.is_file():
            src_t = p_a["work_dir"] / "thumbs" / f"{pid}.jpg"
            if not src_t.is_file():
                src_t = p_b["work_dir"] / "thumbs" / f"{pid}.jpg"
            if src_t.is_file():
                shutil.copy2(src_t, target_t)

        # Copy face crops
        for face in rec.faces:
            target_c = target_crops / f"{face.face_id}.jpg"
            if not target_c.is_file():
                src_c = p_a["work_dir"] / "crops" / f"{face.face_id}.jpg"
                if not src_c.is_file():
                    src_c = p_b["work_dir"] / "crops" / f"{face.face_id}.jpg"
                if src_c.is_file():
                    shutil.copy2(src_c, target_c)

    # 3. Combine Edits & Detect Conflicts
    combined_edits_list, conflicts = combine_edits(
        p_a["edits_data"].get("edits", []),
        p_b["edits_data"].get("edits", []),
    )
    combined_edits_payload = {
        "version": 1,
        "edits": combined_edits_list,
    }
    with open(target_work_p / "edits.json", "w", encoding="utf-8") as f:
        json.dump(combined_edits_payload, f, indent=2)

    # 4. Cluster Combined Photos
    clusterer = FaceClusterer(
        distance_threshold=distance_threshold,
        second_pass_merge=True,
    )
    people, unrecognized = clusterer.cluster(all_photos)

    # Save id_map.json
    with open(target_work_p / "id_map.json", "w", encoding="utf-8") as f:
        json.dump(clusterer.id_map, f, indent=2)

    # Save suggestions.json
    now_iso = datetime.datetime.now().astimezone().isoformat()
    sug_payload = {
        "version": 1,
        "generated_at": now_iso,
        "threshold_range": [0.50, 0.65],
        "maybe_groups_count": len(clusterer.maybe_groups),
        "maybe_groups": clusterer.maybe_groups,
        "ambiguous_faces_count": len(clusterer.ambiguous_faces),
        "ambiguous_faces": clusterer.ambiguous_faces,
        "stats": clusterer.stats,
    }
    with open(target_work_p / "suggestions.json", "w", encoding="utf-8") as f:
        json.dump(sug_payload, f, indent=2)

    # 5. Replay Combined Edits
    people, unrecognized, unapplied_edits, edit_stats = apply_edits(
        people=people,
        unrecognized=unrecognized,
        edits_data=combined_edits_payload,
        photos=all_photos,
    )

    # 6. Build Manifest v2 with Parent Projects recorded as Sources
    sources_a = p_a.get("manifest_data", {}).get("sources", [])
    sources_b = p_b.get("manifest_data", {}).get("sources", [])

    # Synthesize unified sources list
    parent_a_label = p_a.get("manifest_data", {}).get("project_name") or Path(proj_a_work).name
    parent_b_label = p_b.get("manifest_data", {}).get("project_name") or Path(proj_b_work).name

    combined_sources: List[Dict[str, Any]] = [
        {
            "id": f"src_proj_{hashlib.sha256(str(proj_a_work).encode('utf-8')).hexdigest()[:8]}",
            "kind": "project",
            "label": str(parent_a_label),
            "path_or_url": str(proj_a_work),
            "photo_count": len(p_a["photos"]),
            "status": "completed",
        },
        {
            "id": f"src_proj_{hashlib.sha256(str(proj_b_work).encode('utf-8')).hexdigest()[:8]}",
            "kind": "project",
            "label": str(parent_b_label),
            "path_or_url": str(proj_b_work),
            "photo_count": len(p_b["photos"]),
            "status": "completed",
        },
    ]

    # Also inherit original sources from both projects for downstream filtering
    existing_src_ids = {s["id"] for s in combined_sources}
    for s in sources_a + sources_b:
        if isinstance(s, dict) and s.get("id") and s["id"] not in existing_src_ids:
            combined_sources.append(s)
            existing_src_ids.add(s["id"])

    # 7. Export static bundle
    proj_title = new_project_name or f"Merged: {parent_a_label} + {parent_b_label}"
    result = EngineResult(
        photos=all_photos,
        people=people,
        unrecognized=unrecognized,
        distance_threshold=distance_threshold,
        id_map=clusterer.id_map,
        temp_dir=None,
        source_title=proj_title,
        unapplied_edits=unapplied_edits,
        sources=combined_sources,
    )

    exporter = BundleExporter(
        output_dir=target_export_p,
        cache_dir=target_work_p,
    )
    exporter.export(
        result=result,
        title=proj_title,
        include_maybe=False,
        cleanup_temp=False,
    )

    # Write conflicts report to target work directory
    conflicts_dict_list = [c.to_dict() for c in conflicts]
    conflicts_report = {
        "generated_at": now_iso,
        "parent_a": str(proj_a_work),
        "parent_b": str(proj_b_work),
        "conflicts_count": len(conflicts),
        "conflicts": conflicts_dict_list,
    }
    with open(target_work_p / "merge_conflicts.json", "w", encoding="utf-8") as f:
        json.dump(conflicts_report, f, indent=2)

    return {
        "success": True,
        "project_name": proj_title,
        "work_dir": str(target_work_p),
        "export_dir": str(target_export_p),
        "total_photos": len(all_photos),
        "shared_photos": shared_photo_count,
        "people_count": len(people),
        "unrecognized_faces": len(unrecognized.faces),
        "unrecognized_photos": len(unrecognized.photo_ids),
        "edits_applied": edit_stats.get("applied", 0),
        "unapplied_edits": len(unapplied_edits),
        "conflicts_count": len(conflicts),
        "conflicts": conflicts_dict_list,
    }
