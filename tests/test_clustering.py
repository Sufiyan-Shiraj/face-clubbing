"""Unit tests for FaceClusterer using synthetic embeddings (no model files required)."""

from typing import List, Dict, Optional
import numpy as np
import pytest

from backend.engine.clusterer import FaceClusterer
from backend.engine.models import FaceDetection, PhotoRecord, PersonCluster, UnrecognizedGroup


def _make_unit_vector(index: int, dim: int = 512) -> np.ndarray:
    v = np.zeros(dim, dtype=np.float32)
    v[index] = 1.0
    return v


def _vector_at_distance(base: np.ndarray, orth: np.ndarray, dist: float) -> np.ndarray:
    """Generate a unit vector at exact cosine distance `dist` from `base` towards `orth`."""
    cos_theta = 1.0 - dist
    sin_theta = float(np.sqrt(max(0.0, 1.0 - cos_theta**2)))
    v = cos_theta * base + sin_theta * orth
    return (v / np.linalg.norm(v)).astype(np.float32)


def _make_face(
    face_id: str,
    photo_id: str,
    embedding: np.ndarray,
    det_score: float = 0.90,
    dim: int = 100,
    yaw: float = 0.0,
) -> FaceDetection:
    return FaceDetection(
        face_id=face_id,
        photo_id=photo_id,
        bbox=[0.0, 0.0, float(dim), float(dim)],
        det_score=det_score,
        embedding=embedding,
        pose=[0.0, yaw, 0.0],
        is_good_quality=True,
    )


def _make_photo(photo_id: str, faces: List[FaceDetection]) -> PhotoRecord:
    return PhotoRecord(
        photo_id=photo_id,
        original_path=f"/dummy/{photo_id}.jpg",
        file_name=f"{photo_id}.jpg",
        width=1000,
        height=1000,
        faces=faces,
    )


def test_seed_vs_attach_only_roles():
    """Seed faces can start clusters; attach-only faces cannot start clusters."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    # 1. Attach-only face alone without seeds cannot start a cluster
    attach_alone = _make_face("f_att", "p1", e0, det_score=0.60)  # det_score 0.60 < 0.70 seed floor
    photos = {"p1": _make_photo("p1", [attach_alone])}
    clusterer = FaceClusterer()
    people, unrec = clusterer.cluster(photos)

    assert len(people) == 0
    assert len(unrec.faces) == 1
    assert unrec.faces[0]["photo_id"] == "p1"
    assert attach_alone.rejection_reason == "unattached_lowscore"

    # 2. When a seed face exists, attach-only face can attach to it
    seed_face = _make_face("f_seed", "p2", e0, det_score=0.90)
    # attach-only face at distance 0.20 from seed_face
    att_emb = _vector_at_distance(e0, e1, 0.20)
    attach_face = _make_face("f_att2", "p3", att_emb, det_score=0.60)

    photos2 = {
        "p2": _make_photo("p2", [seed_face]),
        "p3": _make_photo("p3", [attach_face]),
    }
    clusterer2 = FaceClusterer()
    people2, unrec2 = clusterer2.cluster(photos2)

    assert len(people2) == 1
    assert len(people2[0].faces) == 2
    assert set(people2[0].photo_ids) == {"p2", "p3"}
    assert len(unrec2.faces) == 0


def test_attach_margin():
    """Attach-only face attaches if d1 < 0.45 and (d2 - d1) >= 0.05; fails margin if < 0.05."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)
    e3 = _make_unit_vector(3)

    # Seed 1 in p1 (e0), Seed 2 in p2 (e2)
    s1 = _make_face("f_s1", "p1", e0, det_score=0.90)
    s2 = _make_face("f_s2", "p2", e2, det_score=0.90)

    # Case A: Attach-only face with margin < 0.05 (e.g. d1 = 0.30, d2 = 0.33)
    rem_sq = 1.0 - (0.70**2 + 0.67**2)
    assert rem_sq > 0
    v_ambig = (0.70 * e0 + 0.67 * e2 + np.sqrt(rem_sq) * e3).astype(np.float32)
    f_ambig = _make_face("f_ambig", "p3", v_ambig, det_score=0.60)

    photos_ambig = {
        "p1": _make_photo("p1", [s1]),
        "p2": _make_photo("p2", [s2]),
        "p3": _make_photo("p3", [f_ambig]),
    }
    cl_ambig = FaceClusterer(distance_threshold=0.50)
    people_a, unrec_a = cl_ambig.cluster(photos_ambig)

    assert len(people_a) == 2
    assert len(unrec_a.faces) == 1
    assert f_ambig.rejection_reason == "ambiguous"

    # Case B: Attach-only face with margin >= 0.05 (e.g. d1 = 0.30, d2 = 0.40)
    v_clear = (0.70 * e0 + 0.60 * e2 + np.sqrt(1.0 - (0.70**2 + 0.60**2)) * e3).astype(np.float32)
    f_clear = _make_face("f_clear", "p4", v_clear, det_score=0.60)

    photos_clear = {
        "p1": _make_photo("p1", [s1]),
        "p2": _make_photo("p2", [s2]),
        "p4": _make_photo("p4", [f_clear]),
    }
    cl_clear = FaceClusterer(distance_threshold=0.50)
    people_b, unrec_b = cl_clear.cluster(photos_clear)

    assert len(people_b) == 2
    assert len(unrec_b.faces) == 0
    # Attached to cluster 1
    c1 = next(p for p in people_b if "p1" in p.photo_ids)
    assert "f_clear" in [f.face_id for f in c1.faces]


def test_same_photo_exclusion_on_attach():
    """Attach-only face cannot attach to a cluster containing a face from the same photo."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    # Seed face in photo 1
    s1 = _make_face("f_s1", "p1", e0, det_score=0.90)
    # Attach-only face in the SAME photo (p1), close to s1 (dist 0.20 < 0.45)
    att_emb = _vector_at_distance(e0, e1, 0.20)
    att_face = _make_face("f_att", "p1", att_emb, det_score=0.60)

    photos = {"p1": _make_photo("p1", [s1, att_face])}
    cl = FaceClusterer()
    people, unrec = cl.cluster(photos)

    assert len(people) == 1
    assert len(people[0].faces) == 1
    assert people[0].faces[0].face_id == "f_s1"
    assert len(unrec.faces) == 1
    assert att_face.rejection_reason == "ambiguous"


def test_second_pass_auto_merge_below_050():
    """Two seed clusters with centroid distance < 0.50 auto-merge into one cluster."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    # Seeds at distance 0.35 from each other
    # With distance_threshold=0.30 in pass 1, they form 2 initial clusters.
    # In pass 2 (merge_threshold=0.50), centroid distance is 0.35 < 0.50, so they auto-merge.
    s1 = _make_face("f_s1", "p1", e0, det_score=0.90)
    v_s2 = _vector_at_distance(e0, e1, 0.35)
    s2 = _make_face("f_s2", "p2", v_s2, det_score=0.90)

    photos = {
        "p1": _make_photo("p1", [s1]),
        "p2": _make_photo("p2", [s2]),
    }
    cl = FaceClusterer(
        distance_threshold=0.30,
        second_pass_merge=True,
        merge_threshold=0.50,
    )
    people, unrec = cl.cluster(photos)

    assert len(people) == 1
    assert set(people[0].photo_ids) == {"p1", "p2"}
    assert len(people[0].faces) == 2


def test_same_photo_guard_blocking_and_collage():
    """Same-photo guard blocks merge if same-photo face pair > 0.40, but allows collage <= 0.40."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    # Cluster 1 seed is in p1 (e0).
    # Cluster 2 seed is in p2 at distance d from e0.
    # p_shared has two attach-only faces:
    # f_x (dist 0 from s1, so attaches to Cluster 1)
    # f_y (dist 0 from s2, so attaches to Cluster 2)
    # The pairwise distance between f_x and f_y is d.

    # Scenario A: Blocked merge because pairwise distance is 0.45 > 0.40
    # Centroid distance between Cluster 1 and Cluster 2 is ~0.45 < 0.50 (merge_threshold)
    v_45 = _vector_at_distance(e0, e1, 0.45)
    s1_bl = _make_face("f_s1", "p1", e0, det_score=0.95)
    s2_bl = _make_face("f_s2", "p2", v_45, det_score=0.95)
    fx_bl = _make_face("f_x", "p_shared", e0, det_score=0.60)
    fy_bl = _make_face("f_y", "p_shared", v_45, det_score=0.60)

    photos_blocked = {
        "p1": _make_photo("p1", [s1_bl]),
        "p2": _make_photo("p2", [s2_bl]),
        "p_shared": _make_photo("p_shared", [fx_bl, fy_bl]),
    }
    cl_blocked = FaceClusterer(
        distance_threshold=0.20,
        second_pass_merge=True,
        merge_threshold=0.50,
        same_photo_merge_max=0.40,
        maybe_threshold=0.65,
    )
    people_bl, unrec_bl = cl_blocked.cluster(photos_blocked)

    # Should remain 2 separate clusters because same-photo pair distance 0.45 > 0.40
    assert len(people_bl) == 2
    # Check that a same_photo_conflict maybe link was recorded
    reasons = [l["reason"] for g in cl_blocked.maybe_groups for l in g["links"]]
    assert "same_photo_conflict" in reasons

    # Scenario B: Collage allowed because pairwise distance is 0.25 <= 0.40
    v_25 = _vector_at_distance(e0, e1, 0.25)
    s1_col = _make_face("f_s1", "p1", e0, det_score=0.95)
    s2_col = _make_face("f_s2", "p2", v_25, det_score=0.95)
    fx_col = _make_face("f_x", "p_collage", e0, det_score=0.60)
    fy_col = _make_face("f_y", "p_collage", v_25, det_score=0.60)

    photos_collage = {
        "p1": _make_photo("p1", [s1_col]),
        "p2": _make_photo("p2", [s2_col]),
        "p_collage": _make_photo("p_collage", [fx_col, fy_col]),
    }
    cl_collage = FaceClusterer(
        distance_threshold=0.20,  # Separate in pass 1
        second_pass_merge=True,
        merge_threshold=0.50,
        same_photo_merge_max=0.40,
    )
    people_col, unrec_col = cl_collage.cluster(photos_collage)

    # Auto-merge succeeds into 1 cluster because collage <= 0.40
    assert len(people_col) == 1
    assert len(people_col[0].faces) == 4


def test_ambiguous_reattach_after_merge():
    """Ambiguous face that failed attach margin before merge recovers after clusters merge."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)
    e3 = _make_unit_vector(3)

    # Cluster 1 (seed in p1, e0) and Cluster 2 (seed in p2, at dist 0.30 from e0)
    # Pass 1 cut is 0.25, so they start in separate clusters.
    c2_emb = _vector_at_distance(e0, e1, 0.30)
    s1 = _make_face("f_s1", "p1", e0, det_score=0.95)
    s2 = _make_face("f_s2", "p2", c2_emb, det_score=0.95)

    # Attach-only face F in p3 is equidistant from Cluster 1 and Cluster 2:
    # d1 ~ 0.31, d2 ~ 0.32 -> margin < 0.05, so fails first pass as "ambiguous"
    v_att = (0.69 * e0 + 0.69 * c2_emb + 0.20 * e3)
    v_att /= np.linalg.norm(v_att)
    f_att = _make_face("f_att", "p3", v_att, det_score=0.60)

    photos = {
        "p1": _make_photo("p1", [s1]),
        "p2": _make_photo("p2", [s2]),
        "p3": _make_photo("p3", [f_att]),
    }

    cl = FaceClusterer(
        distance_threshold=0.25,
        second_pass_merge=True,
        merge_threshold=0.50,
    )
    people, unrec = cl.cluster(photos)

    # Clusters 1 and 2 merged into 1 person, and face F re-attached to the merged cluster!
    assert len(people) == 1
    assert len(unrec.faces) == 0
    assert "f_att" in [f.face_id for f in people[0].faces]


def test_every_photo_covered_and_face_accounting():
    """Invariants: every photo is covered, and clustered faces + unrecognized faces == total detected."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)

    s1 = _make_face("f1", "p1", e0, det_score=0.90)
    s2 = _make_face("f2", "p2", e1, det_score=0.90)
    # Small face with orthogonal embedding -> distance 1.0 > 0.45 from all clusters -> stays in Unrecognized
    u1 = _make_face("f3", "p3", e2, det_score=0.80, dim=30)  # dim 30 < 64
    # Photo with no faces
    photos = {
        "p1": _make_photo("p1", [s1]),
        "p2": _make_photo("p2", [s2]),
        "p3": _make_photo("p3", [u1]),
        "p4_noface": _make_photo("p4_noface", []),
    }

    cl = FaceClusterer()
    people, unrec = cl.cluster(photos)

    # 1. Invariant: Every photo covered
    covered = set(unrec.photo_ids)
    for p in people:
        covered.update(p.photo_ids)
    assert covered == set(photos.keys())

    # 2. Invariant: Clustered faces + Unrecognized faces = Total detected faces
    total_detected = sum(len(p.faces) for p in photos.values())
    clustered_count = sum(len(p.faces) for p in people)
    unrec_count = len(unrec.faces)
    assert clustered_count + unrec_count == total_detected
    assert total_detected == 3
    assert clustered_count == 2
    assert unrec_count == 1


def test_merged_from_and_id_map():
    """FaceClusterer populates merged_from, merged_from_numbering, and id_map accurately."""
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)
    e2 = _make_unit_vector(2)
    e3 = _make_unit_vector(3)

    # Initial cluster 1: two photos (distance 0.10)
    s1a = _make_face("f1a", "ph1", e0, det_score=0.90)
    s1b = _make_face("f1b", "ph2", _vector_at_distance(e0, e1, 0.10), det_score=0.90)

    # Initial cluster 2: one photo, at distance 0.46 from e0 (will auto-merge with cluster 1)
    s2a = _make_face("f2a", "ph3", _vector_at_distance(e0, e2, 0.46), det_score=0.90)

    # Initial cluster 3: orthogonal, stays separate
    s3a = _make_face("f3a", "ph4", e3, det_score=0.90)

    photos = {
        "ph1": _make_photo("ph1", [s1a]),
        "ph2": _make_photo("ph2", [s1b]),
        "ph3": _make_photo("ph3", [s2a]),
        "ph4": _make_photo("ph4", [s3a]),
    }

    cl = FaceClusterer(distance_threshold=0.40, second_pass_merge=True, merge_threshold=0.50)
    people, _ = cl.cluster(photos)

    # Pre-merge had 3 clusters; post-merge has 2 clusters
    assert len(people) == 2
    merged_person = next(p for p in people if len(p.photo_ids) == 3)
    single_person = next(p for p in people if len(p.photo_ids) == 1)

    assert len(merged_person.merged_from) == 2
    assert len(single_person.merged_from) == 1
    assert merged_person.merged_from_numbering == "pre-merge 3"
    assert single_person.merged_from_numbering == "pre-merge 3"

    assert "_metadata" in cl.id_map
    assert cl.id_map["_metadata"]["count_pre"] == 3
    assert cl.id_map["_metadata"]["count_final"] == 2
    # All 3 pre-merge IDs must map to final IDs
    pre_ids = [k for k in cl.id_map.keys() if not k.startswith("_")]
    assert len(pre_ids) == 3
    final_ids = {p.id for p in people}
    for pid in pre_ids:
        assert pid in cl.id_map
        assert cl.id_map[pid] in final_ids

