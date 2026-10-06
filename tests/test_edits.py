"""Tests for organizer edit replay and stable identity (Task 7 / SPEC 6.3)."""

from pathlib import Path
import json
import random
from PIL import Image
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
from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.engine.cache import EmbeddingCache
from backend.engine.scanner import PhotoScanner


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
    """(i) Merge two clusters by anchor faces, re-run with different threshold, confirm merge survives and unlocatable edits reported."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)

    # Person A in p1, Person B in p2 (distance 0.45):
    # First run (distance_threshold=0.50) auto-merges them into one cluster.
    # Second run (distance_threshold=0.35, merge_threshold=0.35) leaves them in separate clusters.
    f_a = _make_face("f_a01", "p1", e0)
    f_b = _make_face("f_b01", "p2", _vector_at_distance(e0, e1, 0.45))
    f_c = _make_face("f_c01", "p3", e2)

    photos = {
        "p1": _make_photo("p1", [f_a]),
        "p2": _make_photo("p2", [f_b]),
        "p3": _make_photo("p3", [f_c]),
    }

    # Initial clustering at threshold 0.50 -> auto-merges f_a and f_b into one cluster (2 clusters total)
    cl1 = FaceClusterer(distance_threshold=0.50)
    people1, unrec1 = cl1.cluster(photos)
    assert len(people1) == 2
    c_a1 = next(p for p in people1 if any(f.face_id == "f_a01" for f in p.faces))
    c_b1 = next(p for p in people1 if any(f.face_id == "f_b01" for f in p.faces))
    assert c_a1.id == c_b1.id

    # Organizer merges Person A and Person B via anchor faces, plus an unlocatable edit
    edits_data = {
        "version": 1,
        "edits": [
            {
                "op": "merge",
                "anchors": [["f_a01"], ["f_b01"]],
            },
            {
                "op": "merge",
                "anchors": [["f_a01"], ["f_nonexistent_999"]],
            },
        ],
    }

    people_edited, unrec_edited, unapplied, _ = apply_edits(people1, unrec1, edits_data, photos)
    assert len(unapplied) == 1
    assert unapplied[0]["edit"]["op"] == "merge"
    assert "could not locate person for anchors" in unapplied[0]["reason"]
    assert len(people_edited) == 2
    merged_person = next(p for p in people_edited if "f_a01" in [f.face_id for f in p.faces])
    assert "f_b01" in [f.face_id for f in merged_person.faces]

    # Re-run clustering with a DIFFERENT distance_threshold (0.35) -> leaves them in separate clusters
    cl2 = FaceClusterer(distance_threshold=0.35, merge_threshold=0.35)
    people2, unrec2 = cl2.cluster(photos)
    assert len(people2) == 3

    # In the second run, assert before replay that the two anchor faces are in different clusters
    c_a2 = next(p for p in people2 if any(f.face_id == "f_a01" for f in p.faces))
    c_b2 = next(p for p in people2 if any(f.face_id == "f_b01" for f in p.faces))
    assert c_a2.id != c_b2.id

    # Apply same edits on the re-run output and assert they are in the same cluster
    people_replayed, _, unapplied2, _ = apply_edits(people2, unrec2, edits_data, photos)
    assert len(unapplied2) == 1
    assert unapplied2[0]["edit"]["op"] == "merge"
    assert "could not locate person for anchors" in unapplied2[0]["reason"]
    assert len(people_replayed) == 2
    merged_replayed = next(p for p in people_replayed if "f_a01" in [f.face_id for f in p.faces])
    assert "f_b01" in [f.face_id for f in merged_replayed.faces]


def test_unapplied_edit_unknown_face_id():
    """(ii) An edit with an unknown face ID appears in unapplied_edits with reason, never crashes or silently drops."""
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

    # Must execute safely without crashing
    _, _, unapplied, stats = apply_edits(people, unrec, edits_data, photos)
    assert len(unapplied) == 5
    assert stats["failed"] == 5
    for u in unapplied:
        assert "reason" in u
        assert len(u["reason"]) > 0


def test_deterministic_cluster_ids_shuffled_input():
    """(iii) Cluster IDs are deterministic: shuffling input order produces identical photo-count-descending order and smallest-face-ID tie-break."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)

    # Person Alpha: 3 photos (photo count = 3)
    f_a1 = _make_face("f_alpha_01", "ph_a1", e0)
    f_a2 = _make_face("f_alpha_02", "ph_a2", e0)
    f_a3 = _make_face("f_alpha_03", "ph_a3", e0)

    # Person Beta: 2 photos (photo count = 2, smallest face ID = "f_beta_01")
    f_b1 = _make_face("f_beta_01", "ph_b1", e1)
    f_b2 = _make_face("f_beta_02", "ph_b2", e1)

    # Person Gamma: 2 photos (photo count = 2, smallest face ID = "f_gamma_01")
    # "f_beta_01" < "f_gamma_01", so Beta must tie-break before Gamma
    f_g1 = _make_face("f_gamma_01", "ph_g1", e2)
    f_g2 = _make_face("f_gamma_02", "ph_g2", e2)

    all_photos = [
        _make_photo("ph_a1", [f_a1]),
        _make_photo("ph_a2", [f_a2]),
        _make_photo("ph_a3", [f_a3]),
        _make_photo("ph_b1", [f_b1]),
        _make_photo("ph_b2", [f_b2]),
        _make_photo("ph_g1", [f_g1]),
        _make_photo("ph_g2", [f_g2]),
    ]

    base_results = None
    rng = random.Random(42)

    for trial in range(5):
        shuffled = list(all_photos)
        rng.shuffle(shuffled)
        photos_dict = {p.photo_id: p for p in shuffled}

        cl = FaceClusterer()
        people, _ = cl.cluster(photos_dict)

        assert len(people) == 3
        # Strict order:
        # 1st: Person Alpha (3 photos)
        assert len(people[0].photo_ids) == 3
        assert "f_alpha_01" in [f.face_id for f in people[0].faces]

        # 2nd: Person Beta (2 photos, tie-break 'f_beta_01' < 'f_gamma_01')
        assert len(people[1].photo_ids) == 2
        assert "f_beta_01" in [f.face_id for f in people[1].faces]

        # 3rd: Person Gamma (2 photos)
        assert len(people[2].photo_ids) == 2
        assert "f_gamma_01" in [f.face_id for f in people[2].faces]

        summary = [(p.id, len(p.photo_ids), FaceClusterer.get_cluster_best_face(p.faces)[0]) for p in people]
        if base_results is None:
            base_results = summary
        else:
            assert summary == base_results


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
    assert len(people_after[0].faces) == 2
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


def test_deterministic_identical_runs(tmp_path: Path):
    """Running the engine twice on identical synthetic inputs produces identical output (excluding generated_at)."""
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    p1 = photos_dir / "img1.jpg"
    p2 = photos_dir / "img2.jpg"
    p3 = photos_dir / "img3.jpg"
    for i, p in enumerate([p1, p2, p3]):
        img = Image.new("RGB", (200, 200), color=(100 + i * 20, 120 + i * 20, 140 + i * 20))
        img.save(p)

    with PhotoScanner(photos_dir) as scanner:
        scanned = scanner.scan()
    pid_map = {item.file_name: item.photo_id for item in scanned}

    work_dir = tmp_path / "work"
    cache = EmbeddingCache(work_dir)
    e0 = np.zeros(512, dtype=np.float32)
    e0[0] = 1.0
    e1 = np.zeros(512, dtype=np.float32)
    e1[1] = 1.0

    pid1 = pid_map["img1.jpg"]
    pid2 = pid_map["img2.jpg"]
    pid3 = pid_map["img3.jpg"]

    f1 = FaceDetection(
        face_id=f"f_{pid1}_001",
        photo_id=pid1,
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=0.92,
        embedding=e0,
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )
    f2 = FaceDetection(
        face_id=f"f_{pid2}_001",
        photo_id=pid2,
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=0.91,
        embedding=e0,
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )
    f3 = FaceDetection(
        face_id=f"f_{pid3}_001",
        photo_id=pid3,
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=0.90,
        embedding=e1,
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )

    for p_file, f_obj in [("img1.jpg", f1), ("img2.jpg", f2), ("img3.jpg", f3)]:
        rec = PhotoRecord(
            photo_id=pid_map[p_file],
            original_path=str(photos_dir / p_file),
            file_name=p_file,
            width=200,
            height=200,
            faces=[f_obj],
        )
        cache.save(rec)

    out1 = tmp_path / "out1"
    config1 = EngineConfig(
        input_path=photos_dir,
        output_dir=out1,
        cache_dir=work_dir,
        distance_threshold=0.50,
    )
    run_pipeline(config1)

    out2 = tmp_path / "out2"
    config2 = EngineConfig(
        input_path=photos_dir,
        output_dir=out2,
        cache_dir=work_dir,
        distance_threshold=0.50,
    )
    run_pipeline(config2)

    with open(out1 / "people.json", "r", encoding="utf-8") as f:
        data1 = json.load(f)
    with open(out2 / "people.json", "r", encoding="utf-8") as f:
        data2 = json.load(f)

    assert "generated_at" in data1 and "generated_at" in data2
    data1.pop("generated_at")
    data2.pop("generated_at")
    assert data1 == data2, "people.json should be identical excluding generated_at"
