"""Integration tests for PhotoSorter FastAPI layer (BUILD_PLAN Phase 3).

Tests:
1. Merging 3+ people in one call writes anchor face IDs, not cluster IDs, into edits.json (asserts no \\bp\\d{3}\\b).
2. Assigning an Unrecognized face, re-running with changed clustering parameter, confirming edits survived.
3. An edit whose anchor face no longer exists is returned in unapplied_edits without crashing.
4. Undo restores previous state for each edit type (merge, remove, assign, hide, name).
5. Cancel stops a running job.
6. Export contains strictly public-bundle files (no suggestions.json, edits.json, id_map.json, .cache).
"""

import json
import re
import time
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.engine.models import FaceDetection, PhotoRecord, PersonCluster, UnrecognizedGroup, EngineResult
from backend.api.app import create_app
from backend.api.models import SettingsModel

REPO_ROOT = Path(__file__).resolve().parent.parent

def _has_canonical_data() -> bool:
    export_people = REPO_ROOT / "export" / "people.json"
    if not export_people.exists():
        return False
    work_dir = REPO_ROOT / "export.work"
    cache_subdir = work_dir / ".cache"
    has_cache = (
        (work_dir.exists() and len(list(work_dir.glob("*.json"))) >= 200)
        or (cache_subdir.exists() and len(list(cache_subdir.glob("*.json"))) >= 200)
    )
    return has_cache


CANONICAL_DATA_PRESENT = _has_canonical_data()

from PIL import Image

def _make_unit_vector(index: int, dim: int = 512) -> np.ndarray:
    v = np.zeros(dim, dtype=np.float32)
    v[index] = 1.0
    return v


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


def _make_photo(photo_id: str, faces: list[FaceDetection], file_path: str = None) -> PhotoRecord:
    return PhotoRecord(
        photo_id=photo_id,
        original_path=file_path or f"/dummy/{photo_id}.jpg",
        file_name=f"{photo_id}.jpg",
        width=1000,
        height=1000,
        faces=faces,
    )


@pytest.fixture
def api_setup(tmp_path: Path):
    work_dir = tmp_path / "work"
    export_dir = tmp_path / "export"
    photos_dir = tmp_path / "photos"
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy images on disk so BundleExporter thumbnail generation succeeds
    photo_paths = {}
    for pid in ["ph1", "ph2", "ph3", "ph4", "ph5"]:
        p_path = photos_dir / f"{pid}.jpg"
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        img.save(p_path)
        photo_paths[pid] = str(p_path)

    app = create_app(work_dir=work_dir)
    state = app.state.app_state
    state.settings.output_dir = str(export_dir)
    state.settings.cache_dir = str(work_dir)

    # Populate synthetic baseline dataset
    # Person 1 (photo 1)
    f1 = _make_face("f_anchor_01", "ph1", _make_unit_vector(0))
    # Person 2 (photo 2)
    f2 = _make_face("f_anchor_02", "ph2", _make_unit_vector(1))
    # Person 3 (photo 3)
    f3 = _make_face("f_anchor_03", "ph3", _make_unit_vector(2))
    # Person 4 (photo 4) with two faces
    f4a = _make_face("f_anchor_04a", "ph4", _make_unit_vector(3))
    f4b = _make_face("f_anchor_04b", "ph4", _make_unit_vector(3))

    # Unrecognized face in photo 5
    f_unrec = _make_face("f_unrec_01", "ph5", _make_unit_vector(4), det_score=0.45)
    f_unrec.is_good_quality = False
    f_unrec.rejection_reason = "unattached_lowscore"

    photos = {
        "ph1": _make_photo("ph1", [f1], photo_paths["ph1"]),
        "ph2": _make_photo("ph2", [f2], photo_paths["ph2"]),
        "ph3": _make_photo("ph3", [f3], photo_paths["ph3"]),
        "ph4": _make_photo("ph4", [f4a, f4b], photo_paths["ph4"]),
        "ph5": _make_photo("ph5", [f_unrec], photo_paths["ph5"]),
    }

    people = [
        PersonCluster(id="c_01", photo_ids=["ph4"], faces=[f4a, f4b], merged_from=[]),
        PersonCluster(id="c_02", photo_ids=["ph1"], faces=[f1], merged_from=[]),
        PersonCluster(id="c_03", photo_ids=["ph2"], faces=[f2], merged_from=[]),
        PersonCluster(id="c_04", photo_ids=["ph3"], faces=[f3], merged_from=[]),
    ]

    unrec_group = UnrecognizedGroup(
        photo_ids=["ph5"],
        faces=[{"face_id": "f_unrec_01", "photo_id": "ph5", "face": "faces/f_unrec_01.jpg", "rejection_reason": "unattached_lowscore"}],
    )
    unrec_group._face_items = [{"face_obj": f_unrec, "photo_id": "ph5", "face": "faces/f_unrec_01.jpg"}]

    result = EngineResult(
        photos=photos,
        people=people,
        unrecognized=unrec_group,
        distance_threshold=0.50,
        id_map={},
    )
    state.set_result(result, work_dir=work_dir)

    client = TestClient(app)
    return client, state, work_dir, export_dir


def test_api_merge_three_people_writes_anchor_faces_no_cluster_ids(api_setup):
    """(1) Merging 3+ people in one call writes anchor face IDs, not cluster IDs, into edits.json (assert no \\bp\\d{3}\\b)."""
    client, state, work_dir, _ = api_setup

    # Merge 3 people in one call dynamically resolved from active people
    current_people = client.get("/api/people").json()
    ids_to_merge = [current_people[1]["id"], current_people[2]["id"], current_people[3]["id"]]
    resp = client.post("/api/edits", json={"op": "merge", "person_ids": ids_to_merge})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # Initial 4 people -> merging 3 results in 2 people
    assert data["people_count"] == 2

    # Verify edits.json on disk
    edits_file = work_dir / "edits.json"
    assert edits_file.exists()
    content = edits_file.read_text(encoding="utf-8")

    # STRICT ASSERTION: No cluster ID pattern like p001, p002, p003 anywhere in saved file
    assert re.search(r'\bp\d{3}\b', content) is None, f"Found cluster ID in edits.json: {content}"

    # Verify anchor face IDs are saved
    parsed = json.loads(content)
    assert len(parsed["edits"]) == 1
    edit_entry = parsed["edits"][0]
    assert edit_entry["op"] == "merge"
    assert len(edit_entry["anchors"]) == 3
    assert ["f_anchor_02"] in edit_entry["anchors"]
    assert ["f_anchor_03"] in edit_entry["anchors"]
    assert ["f_anchor_01"] in edit_entry["anchors"]


def test_api_assign_unrecognized_face_and_rerun_survives(api_setup):
    """(2) Assigning an Unrecognized face, re-running with changed clustering parameter, checking edits survived."""
    client, state, work_dir, _ = api_setup

    # Assign f_unrec_01 to person with f_anchor_01
    target_p = next(p for p in client.get("/api/people").json() if "f_anchor_01" in p["anchor_face_ids"])
    resp = client.post("/api/edits", json={
        "op": "assign",
        "face_id": "f_unrec_01",
        "person_id": target_p["id"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # Confirm face attached in API response
    people_resp = client.get("/api/people").json()
    p_target = next(p for p in people_resp if "f_anchor_01" in p["anchor_face_ids"])
    face_ids = [f["face_id"] for f in p_target["faces"]]
    assert "f_unrec_01" in face_ids

    # Simulate re-running with a changed clustering parameter
    rerun_resp = client.post("/api/rerun", json={
        "settings": {"distance_threshold": 0.40}
    })
    assert rerun_resp.status_code == 200
    rerun_data = rerun_resp.json()
    assert rerun_data["success"] is True
    assert len(rerun_data["unapplied_edits"]) == 0

    # Verify the edit survived
    people_after = client.get("/api/people").json()
    p_after = next(p for p in people_after if "f_anchor_01" in p["anchor_face_ids"])
    face_ids_after = [f["face_id"] for f in p_after["faces"]]
    assert "f_unrec_01" in face_ids_after


def test_api_unapplied_edit_when_anchor_face_no_longer_exists(api_setup):
    """(3) An edit whose anchor face no longer exists is returned in the 'could not re-apply' list without crashing."""
    client, state, work_dir, _ = api_setup

    # Submit an edit referencing a non-existent anchor face
    edits_file = work_dir / "edits.json"
    ghost_edits = {
        "version": 1,
        "edits": [
            {
                "op": "merge",
                "anchors": [["f_anchor_01"], ["f_ghost_nonexistent_999"]],
            }
        ],
    }
    edits_file.write_text(json.dumps(ghost_edits), encoding="utf-8")
    state._load_edits_from_disk()

    # Re-run pipeline with edits
    rerun_resp = client.post("/api/rerun")
    assert rerun_resp.status_code == 200
    rerun_data = rerun_resp.json()
    assert rerun_data["success"] is True

    # The ghost edit must be reported in unapplied_edits without crashing
    unapplied = rerun_data["unapplied_edits"]
    assert len(unapplied) == 1
    assert "could not locate person for anchors" in unapplied[0]["reason"]
    assert unapplied[0]["edit"]["op"] == "merge"


def test_api_undo_restores_previous_state_for_each_edit_type(api_setup):
    """(4) Undo restores previous state for each edit type (merge, remove, assign, hide, name)."""
    client, state, _, _ = api_setup

    # 1. Test Undo Merge
    cur_people = client.get("/api/people").json()
    orig_people_count = len(cur_people)
    client.post("/api/edits", json={"op": "merge", "person_ids": [cur_people[1]["id"], cur_people[2]["id"]]})
    assert len(client.get("/api/people").json()) == orig_people_count - 1
    # Undo
    undo_resp = client.post("/api/edits", json={"op": "undo"})
    assert undo_resp.status_code == 200
    assert len(client.get("/api/people").json()) == orig_people_count

    # 2. Test Undo Remove
    p1 = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    orig_faces_len = len(p1["faces"])
    client.post("/api/edits", json={"op": "remove", "person_id": p1["id"], "face_id": "f_anchor_04b"})
    p1_after = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    assert len(p1_after["faces"]) == orig_faces_len - 1
    # Undo
    client.post("/api/edits", json={"op": "undo"})
    p1_restored = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    assert len(p1_restored["faces"]) == orig_faces_len

    # 3. Test Undo Assign
    p1 = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    res_assign = client.post("/api/edits", json={"op": "assign", "face_id": "f_unrec_01", "person_id": p1["id"]})
    assert res_assign.status_code == 200
    p1_with_unrec = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    assert any(f["face_id"] == "f_unrec_01" for f in p1_with_unrec["faces"])
    # Undo
    client.post("/api/edits", json={"op": "undo"})
    p1_reverted = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    assert not any(f["face_id"] == "f_unrec_01" for f in p1_reverted["faces"])

    # 4. Test Undo Hide
    p1 = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    client.post("/api/edits", json={"op": "hide", "person_id": p1["id"]})
    assert len(client.get("/api/people").json()) == orig_people_count - 1
    # Undo
    client.post("/api/edits", json={"op": "undo"})
    assert len(client.get("/api/people").json()) == orig_people_count

    # 5. Test Undo Name
    p1 = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    client.post("/api/edits", json={"op": "name", "person_id": p1["id"], "label": "Champion"})
    named_p = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    assert named_p["label"] == "Champion"
    # Undo
    client.post("/api/edits", json={"op": "undo"})
    unnamed_p = next(p for p in client.get("/api/people").json() if "f_anchor_04a" in p["anchor_face_ids"])
    assert unnamed_p["label"] is None


def test_api_cancel_stops_running_job(api_setup, monkeypatch):
    """(5) Cancel stops a running background job."""
    client, state, work_dir, _ = api_setup

    def fake_pipeline(config):
        for _ in range(50):
            if config.cancel_check and config.cancel_check():
                raise InterruptedError("Cancelled")
            time.sleep(0.05)
        return state.result

    monkeypatch.setattr("backend.api.jobs.run_pipeline", fake_pipeline)

    # Start job
    start_resp = client.post("/api/jobs/start", json={})
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "running"

    # Cancel job
    cancel_resp = client.post("/api/jobs/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] in ["cancelled", "cancelling"]

    # Verify status after cancellation propagates
    time.sleep(0.15)
    status = client.get("/api/jobs/status").json()
    assert status["status"] == "cancelled"


def test_api_export_public_bundle_hygiene(api_setup):
    """(6) Export contains only public-bundle files (no suggestions.json, edits.json, id_map.json, .cache)."""
    client, state, _, export_dir = api_setup

    # Request export
    export_resp = client.post("/api/export", json={"output_dir": str(export_dir)})
    if export_resp.status_code != 200:
        print("EXPORT RESP ERROR:", export_resp.status_code, export_resp.text)
    assert export_resp.status_code == 200
    data = export_resp.json()
    assert data["success"] is True

    # Check files in export_dir
    files_present = sorted([p.name for p in export_dir.iterdir()])

    # Allowed in public bundle: config.json, people.json, faces, thumbs
    allowed = {"config.json", "people.json", "faces", "thumbs"}
    assert set(files_present).issubset(allowed)
    assert "people.json" in files_present
    assert "config.json" in files_present

    # FORBIDDEN:
    forbidden = {"suggestions.json", "edits.json", "id_map.json", ".cache"}
    for f in forbidden:
        assert f not in files_present, f"Forbidden file '{f}' found in public export bundle!"


def test_state_missing_embedding_raises_error(tmp_path: Path):
    """TASK 2: Missing embedding raises clear RuntimeError instead of being faked, and no face in state has embedding None."""
    from backend.api.state import AppState

    fake_export = tmp_path / "export"
    fake_work = tmp_path / "work"
    fake_export.mkdir(parents=True)
    fake_work.mkdir(parents=True)

    # Write a people.json that has a face without embedding in cache
    dummy_people_json = {
        "version": 2,
        "generated_at": "2026-10-06T00:00:00Z",
        "people": [
            {
                "id": "c_missing_01",
                "photos": ["ph_missing"],
                "faces": [
                    {
                        "face_id": "f_missing_999",
                        "photo_id": "ph_missing",
                        "bbox": [10.0, 10.0, 80.0, 80.0],
                        "det_score": 0.95,
                    }
                ],
            }
        ],
        "photos": {
            "ph_missing": {"name": "ph_missing.jpg", "thumb": "thumbs/ph_missing.jpg"}
        },
        "unrecognized": {
            "total_unrecognized_photos": 0,
            "no_face_photos": [],
            "faces": [],
        },
    }
    (fake_export / "people.json").write_text(json.dumps(dummy_people_json), encoding="utf-8")

    # Creating AppState with empty cache must raise RuntimeError
    state = AppState(work_dir=fake_work)
    state.settings.output_dir = str(fake_export)
    state.settings.cache_dir = str(fake_work)

    with pytest.raises(RuntimeError) as exc_info:
        state._try_load_existing_dataset()
    expected_error_msg = (
        "Missing embedding cache for face 'f_missing_999' in photo 'ph_missing'. "
        "State must load embeddings for every face in people.json; fabricating fake FaceDetection is forbidden."
    )
    assert str(exc_info.value) == expected_error_msg

    # Verify that loading the real canonical state succeeds and NO face has embedding None
    if not CANONICAL_DATA_PRESENT:
        pytest.skip("Requires 271-photo export/ and export.work/.cache embedding cache")

    real_state = AppState()
    assert len(real_state.people) == 192
    assert len(real_state.unrecognized.faces) == 445
    for p in real_state.people:
        for f in p.faces:
            assert f.embedding is not None, f"Face {f.face_id} in {p.id} has embedding None!"
            assert isinstance(f.embedding, np.ndarray)
            assert f.embedding.shape == (512,)
    for item in real_state.unrecognized._face_items:
        f_obj = item.get("face_obj")
        assert f_obj is not None
        assert f_obj.embedding is not None, "Unrecognized face has embedding None!"
        assert isinstance(f_obj.embedding, np.ndarray)


def test_api_unrecognized_count_bug_and_invariants(api_setup):
    """TASK 3: Assign drops unrecognized by 1, face disappears from unrec and appears in target person. Undo restores count. Face accounting invariant holds across all edit ops."""
    client, state, work_dir, _ = api_setup

    initial_people = client.get("/api/people").json()
    initial_unrec = client.get("/api/unrecognized").json()

    initial_clustered_faces = sum(len(p["faces"]) for p in initial_people)
    initial_unrec_faces = len(initial_unrec["faces"])
    total_faces = initial_clustered_faces + initial_unrec_faces
    assert initial_unrec_faces == 1
    assert total_faces == 6

    # Target person to receive the face
    target_p = initial_people[0]
    target_id = target_p["id"]
    target_anchor = target_p["anchor_face_ids"][0]
    unrec_face_id = initial_unrec["faces"][0]["face_id"]
    assert unrec_face_id == "f_unrec_01"

    # 1. Assign unrecognized face
    assign_resp = client.post("/api/edits", json={
        "op": "assign",
        "face_id": unrec_face_id,
        "person_id": target_id,
    })
    assert assign_resp.status_code == 200
    assign_data = assign_resp.json()
    assert assign_data["unrecognized_faces_count"] == initial_unrec_faces - 1

    # Check GET /api/unrecognized: face must disappear
    unrec_after_assign = client.get("/api/unrecognized").json()
    assert len(unrec_after_assign["faces"]) == initial_unrec_faces - 1
    assert not any(f["face_id"] == unrec_face_id for f in unrec_after_assign["faces"])

    # Check GET /api/people: face must appear in target person (located by anchor face ID)
    people_after_assign = client.get("/api/people").json()
    target_after_assign = next(p for p in people_after_assign if target_anchor in p["anchor_face_ids"])
    assert any(f["face_id"] == unrec_face_id for f in target_after_assign["faces"])

    # Invariant: clustered faces + unrecognized faces == total_faces
    clustered_after_assign = sum(len(p["faces"]) for p in people_after_assign)
    unrec_count_after_assign = len(unrec_after_assign["faces"])
    assert clustered_after_assign + unrec_count_after_assign == total_faces

    # 2. Undo restores count
    undo_resp = client.post("/api/edits", json={"op": "undo"})
    assert undo_resp.status_code == 200
    undo_data = undo_resp.json()
    assert undo_data["unrecognized_faces_count"] == initial_unrec_faces

    unrec_after_undo = client.get("/api/unrecognized").json()
    assert len(unrec_after_undo["faces"]) == initial_unrec_faces
    assert any(f["face_id"] == unrec_face_id for f in unrec_after_undo["faces"])

    people_after_undo = client.get("/api/people").json()
    clustered_after_undo = sum(len(p["faces"]) for p in people_after_undo)
    assert clustered_after_undo + len(unrec_after_undo["faces"]) == total_faces

    # 3. Test invariant after EVERY edit type:
    def assert_face_invariant():
        ppl = client.get("/api/people").json()
        unr = client.get("/api/unrecognized").json()
        c_count = sum(len(p["faces"]) for p in ppl)
        u_count = len(unr["faces"])
        assert c_count + u_count == total_faces, f"Face accounting invariant failed: {c_count} + {u_count} != {total_faces}"

    # op: merge
    client.post("/api/edits", json={"op": "merge", "person_ids": [people_after_undo[1]["id"], people_after_undo[2]["id"]]})
    assert_face_invariant()

    # op: remove
    ppl_now = client.get("/api/people").json()
    face_to_remove = ppl_now[0]["faces"][0]["face_id"]
    client.post("/api/edits", json={"op": "remove", "person_id": ppl_now[0]["id"], "face_id": face_to_remove})
    assert_face_invariant()

    # op: assign
    unr_now = client.get("/api/unrecognized").json()
    client.post("/api/edits", json={"op": "assign", "face_id": unr_now["faces"][0]["face_id"], "person_id": ppl_now[0]["id"]})
    assert_face_invariant()

    # op: hide
    ppl_now2 = client.get("/api/people").json()
    client.post("/api/edits", json={"op": "hide", "person_id": ppl_now2[-1]["id"]})
    assert_face_invariant()

    # op: name
    ppl_now3 = client.get("/api/people").json()
    client.post("/api/edits", json={"op": "name", "person_id": ppl_now3[0]["id"], "label": "TestPerson"})
    assert_face_invariant()

    # op: undo
    client.post("/api/edits", json={"op": "undo"})
    assert_face_invariant()

    # rerun
    client.post("/api/rerun", json={"settings": {"distance_threshold": 0.45}})
    assert_face_invariant()


@pytest.mark.skipif(
    not CANONICAL_DATA_PRESENT,
    reason="Requires 271-photo export/ and export.work/.cache embedding cache",
)
def test_api_rerun_replay_under_real_clustering_change():
    """TASK 4: Re-run proves replay under a real clustering change (attach_distance_cap).
    Reports people_count and unrec_faces with and without it, asserts by face ID merged anchors and assigned face survive.
    """
    from backend.api.state import AppState
    from backend.api.app import create_app

    # Use a separate test work directory so we never touch canonical edits.json
    repo_root = Path(__file__).resolve().parent.parent
    work_dir = repo_root / "export.work"
    test_edits_path = work_dir / "edits_test_task4.json"
    if test_edits_path.exists():
        test_edits_path.unlink()

    app = create_app(work_dir=work_dir)
    client = TestClient(app)
    state = app.state.app_state
    # Point edits path to test file
    state.edits_path = test_edits_path
    state.edits_list = []

    try:
        # Default baseline check
        people_init = client.get("/api/people").json()
        unrec_init = client.get("/api/unrecognized").json()
        assert len(people_init) == 192
        assert len(unrec_init["faces"]) == 445

        # Pick 3 people to merge by dynamic handles from people_init
        c_a = people_init[-3]
        c_b = people_init[-2]
        c_c = people_init[-1]
        anchor_a = c_a["anchor_face_ids"][0]
        anchor_b = c_b["anchor_face_ids"][0]
        anchor_c = c_c["anchor_face_ids"][0]

        res_merge = client.post("/api/edits", json={"op": "merge", "person_ids": [c_a["id"], c_b["id"], c_c["id"]]})
        assert res_merge.status_code == 200

        # Assign an unrecognized face f_017688ce4a6e7198_004 to first person
        target_person = people_init[0]
        target_person_anchor = target_person["anchor_face_ids"][0]
        unrec_face_id = "f_017688ce4a6e7198_004"

        res_assign = client.post("/api/edits", json={
            "op": "assign",
            "face_id": unrec_face_id,
            "person_id": target_person["id"],
        })
        assert res_assign.status_code == 200
        assign_data = res_assign.json()
        assert assign_data["unrecognized_faces_count"] == 444

        # Capture baseline people_count and unrecognized_faces_count before rerun
        people_pre = client.get("/api/people").json()
        unrec_pre = client.get("/api/unrecognized").json()
        people_count_baseline = len(people_pre)
        unrecognized_faces_count_baseline = len(unrec_pre["faces"])

        # Rerun under attach_distance_cap = 0.35 (measurably changes clustering: 194 people / 528 unrec faces base)
        rerun_res = client.post("/api/rerun", json={
            "settings": {"attach_distance_cap": 0.35}
        })
        assert rerun_res.status_code == 200
        rerun_data = rerun_res.json()
        assert rerun_data["success"] is True

        # Capture counts after rerun with attach_distance_cap = 0.35
        people_post = client.get("/api/people").json()
        unrec_post = client.get("/api/unrecognized").json()
        people_count_after = len(people_post)
        unrecognized_faces_count_after = len(unrec_post["faces"])

        # Print all four numbers
        print(f"\npeople_count_baseline: {people_count_baseline}")
        print(f"unrecognized_faces_count_baseline: {unrecognized_faces_count_baseline}")
        print(f"people_count_after: {people_count_after}")
        print(f"unrecognized_faces_count_after: {unrecognized_faces_count_after}")

        # Assert both differ from baseline
        assert people_count_after != people_count_baseline, (
            f"people_count did not differ after rerun: {people_count_after} == {people_count_baseline}"
        )
        assert unrecognized_faces_count_after != unrecognized_faces_count_baseline, (
            f"unrecognized_faces_count did not differ after rerun: "
            f"{unrecognized_faces_count_after} == {unrecognized_faces_count_baseline}"
        )
        assert people_count_after == 192
        assert unrecognized_faces_count_after == 527

        # Assert BY FACE ID:
        # (a) the 3 merged anchors are in ONE person
        people_after = client.get("/api/people").json()
        merged_person = None
        for p in people_after:
            fids = {f["face_id"] for f in p["faces"]}
            if anchor_a in fids:
                merged_person = p
                break
        assert merged_person is not None, f"Anchor {anchor_a} not found after rerun!"
        merged_fids = {f["face_id"] for f in merged_person["faces"]}
        assert anchor_b in merged_fids, f"Anchor {anchor_b} not in merged person after rerun!"
        assert anchor_c in merged_fids, f"Anchor {anchor_c} not in merged person after rerun!"

        # (b) the assigned face is in its target person
        target_person_after = None
        for p in people_after:
            fids = {f["face_id"] for f in p["faces"]}
            if target_person_anchor in fids:
                target_person_after = p
                break
        assert target_person_after is not None, f"Target anchor {target_person_anchor} not found after rerun!"
        target_fids = {f["face_id"] for f in target_person_after["faces"]}
        assert unrec_face_id in target_fids, f"Assigned face {unrec_face_id} not in target person after rerun!"

        # Face must NOT be in unrecognized
        unrec_after = client.get("/api/unrecognized").json()
        assert not any(f["face_id"] == unrec_face_id for f in unrec_after["faces"])
    finally:
        # Cleanup
        if test_edits_path.exists():
            test_edits_path.unlink()
        # Reset state back to default
        state.settings.attach_distance_cap = 0.45
        state.edits_path = work_dir / "edits.json"
        state._load_edits_from_disk()
        state.rerun_pipeline_with_edits()

