"""Tests for organizer edit replay (Task 7 / SPEC 6.3)."""

from pathlib import Path
import numpy as np
import pytest

from backend.engine.models import (
    FaceDetection,
    PhotoRecord,
    PersonCluster,
    UnrecognizedGroup,
)
from backend.engine.clusterer import FaceClusterer
from backend.engine.edits import apply_edits, locate_person_by_anchors


def _make_unit_vector(index: int, dim: int = 512) -> np.ndarray:
    v = np.zeros(dim, dtype=np.float32)
    v[index] = 1.0
    return v


def _vector_at_distance(base: np.ndarray, orth: np.ndarray, dist: float) -> np.ndarray:
    cos_theta = 1.0 - dist
    sin_theta = float(np.sqrt(max(0.0, 1.0 - cos_theta**2)))
    v = cos_theta * base + sin_theta * orth
    return (v / np.linalg.norm(v)).astype(np.float32)


def _make_face(face_id: str, photo_id: str, embedding: np.ndarray, det_score: float = 0.90) -> FaceDetection:
    return FaceDetection(
        face_id=face_id,
        photo_id=photo_id,
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=det_score,
        embedding=embedding,
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )


def _make_photo(photo_id: str, faces: list[FaceDetection]) -> PhotoRecord:
    return PhotoRecord(
        photo_id=photo_id,
        original_path=f"/dummy/{photo_id}.jpg",
        file_name=f"{photo_id}.jpg",
        width=1000,
        height=1000,
        faces=faces,
    )


def test_edit_merge_preservation_across_thresholds():
    """(i) Merge two clusters by anchor faces, re-run with different threshold, confirm merge survives."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)

    # Person A in p1, Person B in p2 (distance 0.65 -> not merged automatically)
    f_a = _make_face("f_a01", "p1", e0)
    f_b = _make_face("f_b01", "p2", _vector_at_distance(e0, e1, 0.65))
    f_c = _make_face("f_c01", "p3", e2)

    photos = {
        "p1": _make_photo("p1", [f_a]),
        "p2": _make_photo("p2", [f_b]),
        "p3": _make_photo("p3", [f_c]),
    }

    # Initial clustering at threshold 0.50 -> 3 separate clusters
    cl1 = FaceClusterer(distance_threshold=0.50)
    people1, unrec1 = cl1.cluster(photos)
    assert len(people1) == 3

    # Organizer merges Person A and Person B via anchor faces
    edits_data = {
        "version": 1,
        "edits": [
            {
                "op": "merge",
                "anchors": [["f_a01"], ["f_b01"]],
            }
        ],
    }

    people_edited, unrec_edited, unapplied, _ = apply_edits(people1, unrec1, edits_data, photos)
    assert len(unapplied) == 0
    assert len(people_edited) == 2
    merged_person = next(p for p in people_edited if "f_a01" in [f.face_id for f in p.faces])
    assert "f_b01" in [f.face_id for f in merged_person.faces]

    # Re-run clustering with a DIFFERENT distance_threshold (0.35)
    cl2 = FaceClusterer(distance_threshold=0.35)
    people2, unrec2 = cl2.cluster(photos)
    assert len(people2) == 3

    # Replay same edits on the re-run output
    people_replayed, _, unapplied2, _ = apply_edits(people2, unrec2, edits_data, photos)
    assert len(unapplied2) == 0
    assert len(people_replayed) == 2
    merged_replayed = next(p for p in people_replayed if "f_a01" in [f.face_id for f in p.faces])
    assert "f_b01" in [f.face_id for f in merged_replayed.faces]


def test_unapplied_edit_unknown_face_id():
    """(ii) An edit with an unknown face ID appears in unapplied_edits with reason, never silently dropped."""
    e0 = _make_unit_vector(0)
    f_a = _make_face("f_a01", "p1", e0)
    photos = {"p1": _make_photo("p1", [f_a])}

    cl = FaceClusterer()
    people, unrec = cl.cluster(photos)

    edits_data = {
        "version": 1,
        "edits": [
            {
                "op": "merge",
                "anchors": [["f_a01"], ["f_nonexistent_999"]],
            },
            {
                "op": "remove",
                "person": ["f_a01"],
                "face_id": "f_nonexistent_888",
            },
            {
                "op": "assign",
                "face_id": "f_ghost_777",
                "person": ["f_a01"],
            },
            {
                "op": "hide",
                "person": ["f_missing_666"],
            },
            {
                "op": "name",
                "person": ["f_phantom_555"],
                "label": "Nobody",
            },
        ],
    }

    _, _, unapplied, stats = apply_edits(people, unrec, edits_data, photos)
    assert len(unapplied) == 5
    assert stats["failed"] == 5
    for u in unapplied:
        assert "reason" in u
        assert len(u["reason"]) > 0


def test_deterministic_identical_runs():
    """(iii) Two identical runs give identical cluster IDs and assignments."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)

    # 3 photos
    f1 = _make_face("f_001", "p1", e0, det_score=0.92)
    f2 = _make_face("f_002", "p2", _vector_at_distance(e0, e1, 0.15), det_score=0.91)
    f3 = _make_face("f_003", "p3", e2, det_score=0.89)

    photos = {
        "p1": _make_photo("p1", [f1]),
        "p2": _make_photo("p2", [f2]),
        "p3": _make_photo("p3", [f3]),
    }

    cl1 = FaceClusterer()
    people1, _ = cl1.cluster(photos)

    cl2 = FaceClusterer()
    people2, _ = cl2.cluster(photos)

    assert len(people1) == len(people2)
    for p1, p2 in zip(people1, people2):
        assert p1.id == p2.id
        assert p1.photo_ids == p2.photo_ids
        assert [f.face_id for f in p1.faces] == [f.face_id for f in p2.faces]


def test_hide_removes_person_and_preserves_photo_reachability():
    """(iv) Hide removes person from public people while every photo stays reachable (in Unrecognized), with unreachable count reported."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    # Person 1 in photo 1 (only photo 1)
    # Person 2 in photo 2 and photo 3
    f1 = _make_face("f_sole01", "ph1_sole", e0)
    f2 = _make_face("f_multi01", "ph2_multi", e1)
    f3 = _make_face("f_multi02", "ph3_multi", e1)

    photos = {
        "ph1_sole": _make_photo("ph1_sole", [f1]),
        "ph2_multi": _make_photo("ph2_multi", [f2]),
        "ph3_multi": _make_photo("ph3_multi", [f3]),
    }

    cl = FaceClusterer()
    people, unrec = cl.cluster(photos)
    assert len(people) == 2

    # Hide Person 1 (whose sole photo is ph1_sole)
    edits_data = {
        "version": 1,
        "edits": [
            {
                "op": "hide",
                "person": ["f_sole01"],
            }
        ],
    }

    people_after, unrec_after, unapplied, stats = apply_edits(people, unrec, edits_data, photos)
    assert len(unapplied) == 0
    assert len(people_after) == 1
    assert people_after[0].id == "p001"
    # Person 1 was removed
    assert "f_sole01" not in [f.face_id for f in people_after[0].faces]

    # ph1_sole was orphaned, so it must now be in unrec.photo_ids
    assert "ph1_sole" in unrec_after.photo_ids
    assert stats["unreachable_photos_routed_to_unrecognized"] == 1

    # Every original photo is reachable across people + unrecognized
    all_reachable = set(unrec_after.photo_ids)
    for p in people_after:
        all_reachable.update(p.photo_ids)
    assert all_reachable == {"ph1_sole", "ph2_multi", "ph3_multi"}
