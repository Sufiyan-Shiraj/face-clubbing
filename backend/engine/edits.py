"""Organizer edits schema and replay module (SPEC 6.3)."""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
import logging

from backend.engine.models import PersonCluster, UnrecognizedGroup, FaceDetection, PhotoRecord
from backend.engine.clusterer import FaceClusterer

logger = logging.getLogger(__name__)


def locate_person_by_anchors(
    people: List[PersonCluster],
    anchors: List[str],
) -> Tuple[Optional[PersonCluster], Optional[str]]:
    """
    Locates a person cluster containing the anchor face IDs.
    If anchors fall across multiple clusters, returns the cluster holding the most anchors
    and logs the conflict.
    If none of the anchor face IDs are found in any cluster, returns (None, reason).
    """
    if not anchors:
        return None, "empty anchor list"

    anchor_set = set(anchors)
    cluster_counts = Counter()
    face_map: Dict[str, PersonCluster] = {}

    for person in people:
        person_fids = {f.face_id for f in person.faces}
        matching = person_fids & anchor_set
        if matching:
            cluster_counts[person.id] = len(matching)
            face_map[person.id] = person

    if not cluster_counts:
        return None, f"anchors {anchors} not found in any person cluster"

    best_cid, best_count = cluster_counts.most_common(1)[0]
    if len(cluster_counts) > 1:
        logger.warning(
            f"Anchors split across clusters: {dict(cluster_counts)}. "
            f"Using {best_cid} which has the most matching anchors ({best_count})."
        )

    return face_map[best_cid], None


def find_face_by_id(
    face_id: str,
    people: List[PersonCluster],
    unrecognized: UnrecognizedGroup,
    photos: Dict[str, PhotoRecord],
) -> Tuple[Optional[FaceDetection], Optional[str], Optional[PersonCluster]]:
    """
    Locates a face by face_id.
    Returns (face_obj, location_type, person_cluster_or_None).
    location_type is 'cluster', 'unrecognized', or 'photo_record'.
    """
    # 1. Search in people clusters
    for person in people:
        for f in person.faces:
            if f.face_id == face_id:
                return f, "cluster", person

    # 2. Search in unrecognized internal face items or faces
    internal_items = getattr(unrecognized, "_face_items", [])
    for item in internal_items:
        f_obj = item.get("face_obj")
        if f_obj and f_obj.face_id == face_id:
            return f_obj, "unrecognized", None

    # 3. Search in all photo records
    for precord in photos.values():
        for f in precord.faces:
            if f.face_id == face_id:
                return f, "photo_record", None

    return None, None, None


def apply_edits(
    people: List[PersonCluster],
    unrecognized: UnrecognizedGroup,
    edits_data: Dict[str, Any],
    photos: Dict[str, PhotoRecord],
) -> Tuple[List[PersonCluster], UnrecognizedGroup, List[Dict[str, Any]], Dict[str, int]]:
    """
    Replays organizer edits from edits.json on top of freshly clustered people.

    Schema:
    {
      "version": 1,
      "edits": [
        { "op": "merge",  "anchors": [["face_id", ...], ["face_id", ...]] },
        { "op": "remove", "person": ["face_id", ...], "face_id": "f_..." },
        { "op": "assign", "face_id": "f_...", "person": ["face_id", ...] },
        { "op": "hide",   "person": ["face_id", ...] },
        { "op": "name",   "person": ["face_id", ...], "label": "..." }
      ]
    }

    Returns:
        people: Updated list of PersonClusters with deterministic IDs.
        unrecognized: Updated UnrecognizedGroup.
        unapplied_edits: List of edits that could not be applied with failure reasons.
        stats: Dictionary containing applied counts and unreachable photo count.
    """
    edits_list = edits_data.get("edits", [])
    unapplied_edits: List[Dict[str, Any]] = []
    stats = {
        "applied": 0,
        "failed": 0,
        "unreachable_photos_routed_to_unrecognized": 0,
    }

    current_people = list(people)

    for edit in edits_list:
        op = edit.get("op")

        if op == "merge":
            anchors_groups = edit.get("anchors", [])
            if len(anchors_groups) < 2:
                unapplied_edits.append({"edit": edit, "reason": "merge requires at least 2 anchor groups"})
                stats["failed"] += 1
                continue

            target_clusters: List[PersonCluster] = []
            resolve_failed = False
            for grp in anchors_groups:
                c, err = locate_person_by_anchors(current_people, grp)
                if c is None:
                    unapplied_edits.append({"edit": edit, "reason": f"could not locate person for anchors {grp}: {err}"})
                    stats["failed"] += 1
                    resolve_failed = True
                    break
                target_clusters.append(c)

            if resolve_failed:
                continue

            # Deduplicate target clusters preserving order
            unique_clusters: List[PersonCluster] = []
            for c in target_clusters:
                if c not in unique_clusters:
                    unique_clusters.append(c)

            if len(unique_clusters) == 1:
                # Already merged
                stats["applied"] += 1
                continue

            # Merge all clusters into the first one
            primary = unique_clusters[0]
            for other in unique_clusters[1:]:
                # Merge faces
                primary.faces.extend(other.faces)
                # Merge photos
                for pid in other.photo_ids:
                    if pid not in primary.photo_ids:
                        primary.photo_ids.append(pid)
                # Merge merged_from
                combined_pre = set(primary.merged_from) | set(other.merged_from)
                primary.merged_from = sorted(
                    list(combined_pre),
                    key=lambda x: int(x[1:]) if x[1:].isdigit() else x,
                )
                if not primary.label and other.label:
                    primary.label = other.label
                current_people.remove(other)

            stats["applied"] += 1

        elif op == "remove":
            person_anchors = edit.get("person", [])
            target_fid = edit.get("face_id")
            person, err = locate_person_by_anchors(current_people, person_anchors)
            if person is None:
                unapplied_edits.append({"edit": edit, "reason": f"could not locate person: {err}"})
                stats["failed"] += 1
                continue

            matching = [f for f in person.faces if f.face_id == target_fid]
            if not matching:
                unapplied_edits.append({"edit": edit, "reason": f"face {target_fid} not found in person"})
                stats["failed"] += 1
                continue

            rem_face = matching[0]
            person.faces.remove(rem_face)
            rem_face.is_good_quality = False
            rem_face.rejection_reason = "organizer_removed"
            rem_face.cluster_id = None

            # Add to unrecognized
            unrec_item = {
                "photo_id": rem_face.photo_id,
                "face": f"faces/{rem_face.face_id}.jpg",
                "face_obj": rem_face,
            }
            if not hasattr(unrecognized, "_face_items"):
                unrecognized._face_items = []
            unrecognized._face_items.append(unrec_item)
            unrecognized.faces.append({
                "photo_id": rem_face.photo_id,
                "face": f"faces/{rem_face.face_id}.jpg",
            })

            # Check if photo still in person
            if not any(f.photo_id == rem_face.photo_id for f in person.faces):
                if rem_face.photo_id in person.photo_ids:
                    person.photo_ids.remove(rem_face.photo_id)

            # Check if photo now unreachable
            in_any_person = any(rem_face.photo_id in p.photo_ids for p in current_people)
            if not in_any_person:
                if rem_face.photo_id not in unrecognized.photo_ids:
                    unrecognized.photo_ids.append(rem_face.photo_id)
                stats["unreachable_photos_routed_to_unrecognized"] += 1

            stats["applied"] += 1

        elif op == "assign":
            target_fid = edit.get("face_id")
            target_anchors = edit.get("person")

            face_obj, loc_type, loc_person = find_face_by_id(target_fid, current_people, unrecognized, photos)
            if face_obj is None:
                unapplied_edits.append({"edit": edit, "reason": f"face {target_fid} not found in dataset"})
                stats["failed"] += 1
                continue

            # Remove face from prior cluster if applicable
            if loc_type == "cluster" and loc_person is not None:
                if face_obj in loc_person.faces:
                    loc_person.faces.remove(face_obj)
                    if not any(f.photo_id == face_obj.photo_id for f in loc_person.faces):
                        if face_obj.photo_id in loc_person.photo_ids:
                            loc_person.photo_ids.remove(face_obj.photo_id)

            # Remove from unrecognized if applicable
            if loc_type == "unrecognized":
                internal_items = getattr(unrecognized, "_face_items", [])
                unrecognized._face_items = [it for it in internal_items if it.get("face_obj") != face_obj]
                unrecognized.faces = [it for it in unrecognized.faces if it.get("face") != f"faces/{target_fid}.jpg"]

            face_obj.is_good_quality = True
            face_obj.rejection_reason = None

            if target_anchors is None:
                # Create a new person cluster
                new_person = PersonCluster(
                    id="p_new",
                    photo_ids=[face_obj.photo_id],
                    faces=[face_obj],
                    merged_from=[],
                    merged_from_numbering="",
                )
                current_people.append(new_person)
            else:
                target_person, err = locate_person_by_anchors(current_people, target_anchors)
                if target_person is None:
                    unapplied_edits.append({"edit": edit, "reason": f"could not locate target person: {err}"})
                    stats["failed"] += 1
                    continue
                target_person.faces.append(face_obj)
                if face_obj.photo_id not in target_person.photo_ids:
                    target_person.photo_ids.append(face_obj.photo_id)

            stats["applied"] += 1

        elif op == "hide":
            person_anchors = edit.get("person", [])
            target_person, err = locate_person_by_anchors(current_people, person_anchors)
            if target_person is None:
                unapplied_edits.append({"edit": edit, "reason": f"could not locate person to hide: {err}"})
                stats["failed"] += 1
                continue

            current_people.remove(target_person)

            # Check if any photo of this hidden person becomes unreachable
            for pid in target_person.photo_ids:
                in_remaining = any(pid in p.photo_ids for p in current_people)
                if not in_remaining:
                    if pid not in unrecognized.photo_ids:
                        unrecognized.photo_ids.append(pid)
                    stats["unreachable_photos_routed_to_unrecognized"] += 1

            stats["applied"] += 1

        elif op == "name":
            person_anchors = edit.get("person", [])
            label = edit.get("label")
            target_person, err = locate_person_by_anchors(current_people, person_anchors)
            if target_person is None:
                unapplied_edits.append({"edit": edit, "reason": f"could not locate person to name: {err}"})
                stats["failed"] += 1
                continue

            target_person.label = label
            stats["applied"] += 1

        else:
            unapplied_edits.append({"edit": edit, "reason": f"unknown operation '{op}'"})
            stats["failed"] += 1

    # Remove any empty person clusters that may have resulted from removing all faces
    current_people = [p for p in current_people if len(p.faces) > 0]

    # Re-sort deterministically: photo count desc, ties by best-face ID lexicographically smallest
    current_people.sort(
        key=lambda p: (
            -len(p.photo_ids),
            FaceClusterer.get_cluster_best_face(p.faces)[0],
        )
    )

    # Re-assign canonical cluster IDs p001, p002...
    for idx, p in enumerate(current_people):
        new_id = f"p{idx+1:03d}"
        p.id = new_id
        p.face_path = f"faces/{new_id}.jpg"
        for f in p.faces:
            f.cluster_id = new_id
        p.photo_ids.sort()

    unrecognized.photo_ids.sort()

    return current_people, unrecognized, unapplied_edits, stats
