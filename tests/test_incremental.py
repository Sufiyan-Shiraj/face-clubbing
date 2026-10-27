"""Unit and regression tests for Phase V2-3 Piece 1:
Incremental Face Clustering, Frozen Mode Invariants, and Project Snapshots.

Verifies:
1. Incremental clustering with empty new photos leaves state unchanged.
2. New faces matching an existing person attach cleanly under frozen mode.
3. Same-photo collision prevents attachment to an existing person.
4. Unmatched new faces form new people clusters with sequential IDs.
5. New clusters can merge into existing people if centroid distance < merge_threshold.
6. Frozen mode invariant guarantees zero pre-existing face membership changes.
7. Snapshots capture people.json, manifest.json, edits.json and can be restored cleanly.
"""

import json
import pytest
import numpy as np
from pathlib import Path

from backend.engine.clusterer import FaceClusterer
from backend.engine.models import FaceDetection, PhotoRecord, PersonCluster, UnrecognizedGroup
from backend.engine.snapshots import create_snapshot, restore_snapshot, list_snapshots


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


def _make_photo(photo_id: str, faces: list[FaceDetection]) -> PhotoRecord:
    return PhotoRecord(
        photo_id=photo_id,
        original_path=f"/dummy/{photo_id}.jpg",
        file_name=f"{photo_id}.jpg",
        width=1000,
        height=1000,
        faces=faces,
    )


def test_incremental_empty_new_photos():
    """Empty new photos returns existing people and zero diff report."""
    clusterer = FaceClusterer()
    e0 = _make_unit_vector(0)
    face1 = _make_face("f_01", "p1", e0)
    person1 = PersonCluster(
        id="person_01",
        label="Existing Alice",
        face_path="faces/person_01.jpg",
        rep_face=face1,
        photo_ids=["p1"],
        faces=[face1],
    )
    unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    photos = {"p1": _make_photo("p1", [face1])}

    people, updated_unrec, diff = clusterer.cluster_incremental(
        existing_people=[person1],
        existing_unrecognized=unrec,
        existing_photos=photos,
        new_photos={},
    )

    assert len(people) == 1
    assert people[0].id == "person_01"
    assert people[0].label == "Existing Alice"
    assert diff["new_photos_count"] == 0
    assert diff["new_people_count"] == 0
    assert diff["joined_existing_count"] == 0
    assert diff["existing_people_membership_changed"] == 0


def test_incremental_new_face_attaches_to_existing_person():
    """New photo containing a matching face attaches to existing person without modifying pre-existing members."""
    clusterer = FaceClusterer()
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    face1 = _make_face("f_exist_01", "photo_old", e0)
    person1 = PersonCluster(
        id="person_01",
        label="Alice",
        face_path="faces/person_01.jpg",
        rep_face=face1,
        photo_ids=["photo_old"],
        faces=[face1],
    )
    existing_unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    existing_photos = {"photo_old": _make_photo("photo_old", [face1])}

    # New photo with face close to Alice (dist 0.15 < 0.50)
    emb_alice_new = _vector_at_distance(e0, e1, 0.15)
    face_new = _make_face("f_new_01", "photo_new", emb_alice_new)
    new_photos = {"photo_new": _make_photo("photo_new", [face_new])}

    people, updated_unrec, diff = clusterer.cluster_incremental(
        existing_people=[person1],
        existing_unrecognized=existing_unrec,
        existing_photos=existing_photos,
        new_photos=new_photos,
        frozen_mode=True,
    )

    assert len(people) == 1
    assert people[0].id == "person_01"
    assert people[0].label == "Alice"
    assert "photo_new" in people[0].photo_ids
    assert "photo_old" in people[0].photo_ids
    assert len(people[0].faces) == 2
    assert people[0].faces[0].face_id == "f_exist_01"  # Pre-existing face preserved first
    assert people[0].faces[1].face_id == "f_new_01"

    # Verify What Changed report
    assert diff["new_photos_count"] == 1
    assert diff["new_people_count"] == 0
    assert diff["joined_existing_count"] == 1
    assert "person_01" in diff["joined_existing"]
    assert "f_new_01" in diff["joined_existing"]["person_01"]["added_faces"]
    assert "photo_new" in diff["joined_existing"]["person_01"]["added_photos"]
    assert diff["existing_people_membership_changed"] == 0


def test_incremental_same_photo_collision_blocks_attach():
    """If existing person already contains a face from that photo, attach is blocked to avoid duplicate person in same photo."""
    clusterer = FaceClusterer()
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    face1 = _make_face("f_exist_01", "shared_photo", e0)
    person1 = PersonCluster(
        id="person_01",
        label="Alice",
        face_path="faces/person_01.jpg",
        rep_face=face1,
        photo_ids=["shared_photo"],
        faces=[face1],
    )
    existing_unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    existing_photos = {"shared_photo": _make_photo("shared_photo", [face1])}

    # Second face from the SAME photo that looks similar
    emb_close = _vector_at_distance(e0, e1, 0.20)
    face_second = _make_face("f_second_in_photo", "shared_photo", emb_close, det_score=0.60)  # non-seed
    new_photos = {"shared_photo": _make_photo("shared_photo", [face1, face_second])}

    people, updated_unrec, diff = clusterer.cluster_incremental(
        existing_people=[person1],
        existing_unrecognized=existing_unrec,
        existing_photos=existing_photos,
        new_photos={"photo_extra": _make_photo("photo_extra", [face_second])},
    )

    # Note: if face_second was from "shared_photo" (already in Alice), it wouldn't attach to Alice.
    # Here let's test explicitly when photo_id is already in person1:
    face_collision = _make_face("f_col", "shared_photo", emb_close, det_score=0.60)
    people2, updated_unrec2, diff2 = clusterer.cluster_incremental(
        existing_people=[person1],
        existing_unrecognized=existing_unrec,
        existing_photos=existing_photos,
        new_photos={"shared_photo_variant": _make_photo("shared_photo", [face_collision])},
    )
    # The collision face should not attach to Alice because "shared_photo" is already in Alice!
    assert "f_col" not in [f.face_id for f in people2[0].faces]
    assert any(f["face_id"] == "f_col" for f in updated_unrec2.faces)


def test_incremental_forms_new_people_clusters():
    """Unmatched new faces cluster amongst themselves to form new people clusters with sequential IDs."""
    clusterer = FaceClusterer()
    e0 = _make_unit_vector(0)
    e2 = _make_unit_vector(2)
    e3 = _make_unit_vector(3)

    face_alice = _make_face("f_alice", "p_alice", e0)
    person_alice = PersonCluster(
        id="person_01",
        label="Alice",
        face_path="faces/person_01.jpg",
        rep_face=face_alice,
        photo_ids=["p_alice"],
        faces=[face_alice],
    )
    existing_unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    existing_photos = {"p_alice": _make_photo("p_alice", [face_alice])}

    # Two new photos of Bob (orthogonal to Alice)
    emb_bob1 = e2
    emb_bob2 = _vector_at_distance(e2, e3, 0.10)
    face_bob1 = _make_face("f_bob1", "p_bob1", emb_bob1, det_score=0.92)
    face_bob2 = _make_face("f_bob2", "p_bob2", emb_bob2, det_score=0.88)

    new_photos = {
        "p_bob1": _make_photo("p_bob1", [face_bob1]),
        "p_bob2": _make_photo("p_bob2", [face_bob2]),
    }

    people, updated_unrec, diff = clusterer.cluster_incremental(
        existing_people=[person_alice],
        existing_unrecognized=existing_unrec,
        existing_photos=existing_photos,
        new_photos=new_photos,
        frozen_mode=True,
    )

    assert len(people) == 2
    assert people[0].id == "person_01"
    assert people[0].label == "Alice"
    expected_new_pid = f"p{2:03d}"
    assert people[1].id == expected_new_pid
    assert set(people[1].photo_ids) == {"p_bob1", "p_bob2"}
    assert set(f.face_id for f in people[1].faces) == {"f_bob1", "f_bob2"}

    assert diff["new_photos_count"] == 2
    assert diff["new_people_count"] == 1
    assert diff["new_people_ids"] == [expected_new_pid]
    assert diff["joined_existing_count"] == 0
    assert diff["existing_people_membership_changed"] == 0


def test_incremental_new_cluster_merges_into_existing_person():
    """A new cluster formed by new photos merges into an existing person if centroid distance < merge_threshold."""
    clusterer = FaceClusterer(merge_threshold=0.50)
    e0 = _make_unit_vector(0)
    e1 = _make_unit_vector(1)

    face_alice = _make_face("f_alice", "p_alice", e0)
    person_alice = PersonCluster(
        id="person_01",
        label="Alice",
        face_path="faces/person_01.jpg",
        rep_face=face_alice,
        photo_ids=["p_alice"],
        faces=[face_alice],
    )
    existing_unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    existing_photos = {"p_alice": _make_photo("p_alice", [face_alice])}

    # Two new photos forming a cluster close to Alice (dist 0.35 < 0.50)
    emb_c1 = _vector_at_distance(e0, e1, 0.35)
    emb_c2 = _vector_at_distance(e0, e1, 0.38)
    f1 = _make_face("f_new_c1", "p_new_1", emb_c1, det_score=0.91)
    f2 = _make_face("f_new_c2", "p_new_2", emb_c2, det_score=0.92)

    new_photos = {
        "p_new_1": _make_photo("p_new_1", [f1]),
        "p_new_2": _make_photo("p_new_2", [f2]),
    }

    people, updated_unrec, diff = clusterer.cluster_incremental(
        existing_people=[person_alice],
        existing_unrecognized=existing_unrec,
        existing_photos=existing_photos,
        new_photos=new_photos,
        frozen_mode=True,
    )

    # Because distance < 0.50, the new cluster merges INTO Alice
    assert len(people) == 1
    assert people[0].id == "person_01"
    assert "p_new_1" in people[0].photo_ids
    assert "p_new_2" in people[0].photo_ids
    assert diff["new_photos_count"] == 2
    assert diff["new_people_count"] == 0
    assert diff["joined_existing_count"] == 2
    assert diff["existing_people_membership_changed"] == 0


def test_snapshots_create_list_and_restore(tmp_path):
    """Verifies that project snapshots capture metadata and restore rollbacks accurately."""
    work_dir = tmp_path / "work"
    export_dir = tmp_path / "export"
    work_dir.mkdir(parents=True)
    export_dir.mkdir(parents=True)

    # Initial state files
    people_v1 = {
        "version": 1,
        "people": [{"id": "person_01", "photos": ["ph1"], "name": "Initial Alice"}],
        "photos": {"ph1": {"file_name": "ph1.jpg"}},
    }
    manifest_v1 = {
        "version": 2,
        "sources": [{"id": "src_01", "label": "Original Camera"}],
        "photo_origins": {"ph1": "src_01"},
    }
    edits_v1 = {"version": 1, "edits": [{"op": "name", "person_id": "person_01", "name": "Alice"}]}

    with open(work_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_v1, f)
    with open(work_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_v1, f)
    with open(work_dir / "edits.json", "w", encoding="utf-8") as f:
        json.dump(edits_v1, f)
    with open(export_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_v1, f)

    # 1. Create snapshot
    snap_meta = create_snapshot(work_dir=work_dir, export_dir=export_dir, label="Pre-add Source 2")
    assert snap_meta["snapshot_id"].startswith("snap_")
    assert snap_meta["counts"]["people"] == 1
    assert snap_meta["counts"]["photos"] == 1

    # 2. List snapshots
    snaps = list_snapshots(work_dir)
    assert len(snaps) == 1
    assert snaps[0]["snapshot_id"] == snap_meta["snapshot_id"]

    # 3. Simulate mutation (new photos and people added)
    people_v2 = {
        "version": 1,
        "people": [
            {"id": "person_01", "photos": ["ph1", "ph2"], "name": "Alice"},
            {"id": "person_02", "photos": ["ph3"], "name": "Bob"},
        ],
        "photos": {"ph1": {}, "ph2": {}, "ph3": {}},
    }
    with open(work_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_v2, f)
    with open(export_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_v2, f)

    # Check corrupted / mutated count
    with open(work_dir / "people.json", "r", encoding="utf-8") as f:
        cur_p = json.load(f)
    assert len(cur_p["people"]) == 2

    # 4. Restore snapshot (Undo)
    restored_meta = restore_snapshot(work_dir=work_dir, export_dir=export_dir)
    assert restored_meta["snapshot_id"] == snap_meta["snapshot_id"]

    # Verify work_dir and export_dir rolled back to initial state
    with open(work_dir / "people.json", "r", encoding="utf-8") as f:
        rolled_back_work = json.load(f)
    assert len(rolled_back_work["people"]) == 1
    assert rolled_back_work["people"][0]["name"] == "Initial Alice"

    with open(export_dir / "people.json", "r", encoding="utf-8") as f:
        rolled_back_exp = json.load(f)
    assert len(rolled_back_exp["people"]) == 1


class MockIncrementalDetector:
    def __init__(self, *args, **kwargs):
        pass

    def detect_and_embed(self, orig_rgb, photo_id):
        seed_val = int(photo_id[:4], 16) if len(photo_id) >= 4 else 42
        rng = np.random.RandomState(seed_val)
        emb = rng.randn(512).astype(np.float32)
        emb /= np.linalg.norm(emb)
        return [
            FaceDetection(
                face_id=f"f_{photo_id}_01",
                photo_id=photo_id,
                bbox=[10.0, 10.0, 80.0, 80.0],
                det_score=0.95,
                embedding=emb,
            )
        ]


def test_run_incremental_pipeline_e2e(tmp_path, monkeypatch):
    """End-to-end verification of run_incremental_pipeline including deduplication, manifest update, and what_changed.json."""
    from PIL import Image
    import shutil
    from backend.engine.pipeline import EngineConfig, run_incremental_pipeline

    monkeypatch.setattr("backend.engine.pipeline.FaceDetector", MockIncrementalDetector)

    work_dir = tmp_path / "work"
    export_dir = tmp_path / "export"
    work_dir.mkdir(parents=True)
    export_dir.mkdir(parents=True)

    # Source 1: initial photo
    source_1_dir = tmp_path / "source_1"
    source_1_dir.mkdir()
    p1_path = source_1_dir / "photo1.jpg"
    Image.new("RGB", (100, 100), color=(200, 50, 50)).save(p1_path)
    from backend.engine.scanner import compute_file_hash
    p1_hash = compute_file_hash(p1_path)

    # Initial state files
    people_initial = {
        "version": 1,
        "people": [{"id": "person_01", "photos": [p1_hash], "name": "Alice"}],
        "photos": {p1_hash: {"file_name": "photo1.jpg"}},
        "unrecognized": {"photo_ids": [], "faces": []},
    }
    manifest_initial = {
        "schema_version": 2,
        "project_name": "Test Event",
        "created_at": "2026-10-20T00:00:00Z",
        "sources": [{"id": "src_01", "kind": "local", "path_or_url": str(source_1_dir), "label": "Source 1", "photo_count": 1, "status": "completed"}],
        "photo_origins": {p1_hash: "src_01"},
    }
    with open(work_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_initial, f)
    with open(export_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_initial, f)
    with open(work_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_initial, f)
    with open(export_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_initial, f)

    # Source 2: has one duplicate of photo1 and one new photo2
    source_2_dir = tmp_path / "source_2"
    source_2_dir.mkdir()
    shutil.copy2(p1_path, source_2_dir / "photo1_dup.jpg")
    p2_path = source_2_dir / "photo2_new.jpg"
    Image.new("RGB", (100, 100), color=(50, 200, 50)).save(p2_path)

    config = EngineConfig(
        input_path=str(source_2_dir),
        output_dir=export_dir,
        cache_dir=work_dir,
        event_title="Test Event",
    )

    new_src_def = {
        "id": "src_02",
        "kind": "local",
        "path_or_url": str(source_2_dir),
        "label": "Source 2",
    }

    result, diff = run_incremental_pipeline(
        config=config,
        new_source=new_src_def,
        work_dir=work_dir,
        export_dir=export_dir,
        frozen_mode=True,
    )

    # 1. Deduplication verified: photo1_dup was detected as duplicate
    assert diff["skipped_duplicate_photos"] == 1
    assert diff["new_photos_count"] == 1
    assert diff["existing_people_membership_changed"] == 0

    # 2. Manifest v2 updated
    with open(work_dir / "manifest.json", "r", encoding="utf-8") as f:
        updated_mf = json.load(f)
    assert len(updated_mf["sources"]) == 2
    assert updated_mf["sources"][1]["id"] == "src_02"
    assert updated_mf["sources"][1]["photo_count"] == 1

    # 3. what_changed.json written to work_dir and export_dir
    assert (work_dir / "what_changed.json").is_file()
    assert (export_dir / "what_changed.json").is_file()


def test_incremental_api_endpoints(tmp_path, monkeypatch):
    """Verifies POST /api/project/sources/add, GET /api/project/what-changed, and POST /api/project/snapshots/undo."""
    from PIL import Image
    from fastapi.testclient import TestClient
    from backend.api.app import create_app
    from backend.api.state import AppState
    from backend.api.jobs import JobManager

    monkeypatch.setattr("backend.engine.pipeline.FaceDetector", MockIncrementalDetector)

    work_dir = tmp_path / "api_work"
    export_dir = tmp_path / "api_export"
    work_dir.mkdir(parents=True)
    export_dir.mkdir(parents=True)

    # Setup initial people.json & manifest.json
    people_data = {
        "version": 1,
        "people": [{"id": "person_01", "photos": ["ph1"], "name": "Alice"}],
        "photos": {"ph1": {"file_name": "p1.jpg"}},
        "unrecognized": {"photo_ids": [], "faces": []},
    }
    manifest_data = {
        "schema_version": 2,
        "project_name": "API Project",
        "created_at": "2026-10-20T00:00:00Z",
        "sources": [{"id": "src_01", "kind": "local", "path_or_url": "/dummy", "label": "Camera 1", "photo_count": 1}],
        "photo_origins": {"ph1": "src_01"},
    }
    with open(work_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_data, f)
    with open(export_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_data, f)
    with open(work_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    app.state.app_state.project_active = True
    client = TestClient(app)

    # Create new photos in a second folder
    source_2 = tmp_path / "api_source_2"
    source_2.mkdir()
    Image.new("RGB", (100, 100), color=(10, 20, 30)).save(source_2 / "img2.jpg")

    # 1. Add source incrementally
    add_payload = {
        "source": {
            "kind": "local",
            "path_or_url": str(source_2),
            "label": "Second Photographer",
        },
        "frozen_mode": True,
    }
    resp_add = client.post("/api/project/sources/add", json=add_payload)
    assert resp_add.status_code == 200
    add_data = resp_add.json()
    assert add_data["new_photos_count"] == 1
    assert add_data["existing_people_membership_changed"] == 0

    # 2. Get What Changed
    resp_wc = client.get("/api/project/what-changed")
    assert resp_wc.status_code == 200
    wc_data = resp_wc.json()
    assert wc_data["new_photos_count"] == 1

    # 3. List Snapshots
    resp_snaps = client.get("/api/project/snapshots")
    assert resp_snaps.status_code == 200
    snaps_data = resp_snaps.json()
    assert len(snaps_data) >= 1
    assert snaps_data[0]["snapshot_id"].startswith("snap_")

    # 4. Undo Addition
    resp_undo = client.post("/api/project/snapshots/undo")
    assert resp_undo.status_code == 200
    undo_data = resp_undo.json()
    assert undo_data["success"] is True
    assert "Successfully rolled back" in undo_data["message"]

