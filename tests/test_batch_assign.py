import pytest
import json
import re
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient
from backend.api.app import create_app
from backend.engine.models import PersonCluster, FaceDetection, UnrecognizedGroup, PhotoRecord
from backend.engine.edits import apply_edits

def test_api_batch_assign_faces(tmp_path: Path):
    """Verify assigning multiple face_ids in one batch request."""
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)
    state = app.state.app_state

    # Setup mock data in state
    face_a = FaceDetection(face_id="f_anchor_1", photo_id="photo_1", bbox=[0, 0, 10, 10], det_score=0.95, embedding=np.array([0.1]*512, dtype=np.float32))
    face_u1 = FaceDetection(face_id="f_unrec_1", photo_id="photo_2", bbox=[0, 0, 10, 10], det_score=0.85, embedding=np.array([0.2]*512, dtype=np.float32))
    face_u2 = FaceDetection(face_id="f_unrec_2", photo_id="photo_3", bbox=[0, 0, 10, 10], det_score=0.82, embedding=np.array([0.22]*512, dtype=np.float32))

    person1 = PersonCluster(
        id="person_1",
        photo_ids=["photo_1"],
        faces=[face_a],
    )
    unrec = UnrecognizedGroup(
        photo_ids=["photo_2", "photo_3"],
        faces=[
            {"face_id": "f_unrec_1", "photo_id": "photo_2", "face": "faces/f_unrec_1.jpg"},
            {"face_id": "f_unrec_2", "photo_id": "photo_3", "face": "faces/f_unrec_2.jpg"},
        ],
    )
    unrec._face_items = [
        {"face_obj": face_u1, "photo_id": "photo_2", "face_id": "f_unrec_1", "face": "faces/f_unrec_1.jpg"},
        {"face_obj": face_u2, "photo_id": "photo_3", "face_id": "f_unrec_2", "face": "faces/f_unrec_2.jpg"},
    ]

    photos = {
        "photo_1": PhotoRecord(photo_id="photo_1", original_path="/p1.jpg", file_name="p1.jpg", width=100, height=100, faces=[face_a]),
        "photo_2": PhotoRecord(photo_id="photo_2", original_path="/p2.jpg", file_name="p2.jpg", width=100, height=100, faces=[face_u1]),
        "photo_3": PhotoRecord(photo_id="photo_3", original_path="/p3.jpg", file_name="p3.jpg", width=100, height=100, faces=[face_u2]),
    }

    state.people = [person1]
    state.base_people = [person1]
    state.unrecognized = unrec
    state.base_unrecognized = unrec
    state.photos = photos

    # Execute batch assignment of both faces to person_1
    res = client.post("/api/edits", json={
        "op": "assign",
        "face_ids": ["f_unrec_1", "f_unrec_2"],
        "person_id": "person_1",
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["success"] is True

    # Check updated people
    people_res = client.get("/api/people").json()
    assert len(people_res) == 1
    p_updated = people_res[0]
    p_face_ids = [f["face_id"] for f in p_updated["faces"]]
    assert "f_anchor_1" in p_face_ids
    assert "f_unrec_1" in p_face_ids
    assert "f_unrec_2" in p_face_ids
    assert "photo_2" in p_updated["photo_ids"]
    assert "photo_3" in p_updated["photo_ids"]

    # Check unrecognized faces are removed
    unrec_res = client.get("/api/unrecognized").json()
    assert len(unrec_res["faces"]) == 0

def test_api_detach_known_face_to_unknown(tmp_path: Path):
    """Verify detaching (removing) a face from an existing person cluster back to unrecognized."""
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)
    state = app.state.app_state

    face_a = FaceDetection(face_id="f_anchor_1", photo_id="photo_1", bbox=[0, 0, 10, 10], det_score=0.95, embedding=np.array([0.1]*512, dtype=np.float32))
    face_b = FaceDetection(face_id="f_face_2", photo_id="photo_2", bbox=[0, 0, 10, 10], det_score=0.88, embedding=np.array([0.12]*512, dtype=np.float32))

    person = PersonCluster(
        id="person_1",
        photo_ids=["photo_1", "photo_2"],
        faces=[face_a, face_b],
    )
    unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    unrec._face_items = []

    photos = {
        "photo_1": PhotoRecord(photo_id="photo_1", original_path="/p1.jpg", file_name="p1.jpg", width=100, height=100, faces=[face_a]),
        "photo_2": PhotoRecord(photo_id="photo_2", original_path="/p2.jpg", file_name="p2.jpg", width=100, height=100, faces=[face_b]),
    }

    state.people = [person]
    state.base_people = [person]
    state.unrecognized = unrec
    state.base_unrecognized = unrec
    state.photos = photos

    # Detach face_b from person_1
    res = client.post("/api/edits", json={
        "op": "remove",
        "person_id": "person_1",
        "face_id": "f_face_2",
    })
    assert res.status_code == 200, res.text

    # Person should only have face_a now
    people_res = client.get("/api/people").json()
    assert len(people_res) == 1
    assert len(people_res[0]["faces"]) == 1
    assert people_res[0]["faces"][0]["face_id"] == "f_anchor_1"

    # Unrecognized group should now contain detached face_b
    unrec_res = client.get("/api/unrecognized").json()
    assert len(unrec_res["faces"]) == 1
    assert unrec_res["faces"][0]["face_id"] == "f_face_2"

def test_api_create_new_person_from_selected(tmp_path: Path):
    """Verify creating a new person cluster from unrecognized faces (person_id=None)."""
    work_dir = tmp_path / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)
    state = app.state.app_state

    face_u1 = FaceDetection(face_id="f_unrec_1", photo_id="photo_1", bbox=[0, 0, 10, 10], det_score=0.85, embedding=np.array([0.2]*512, dtype=np.float32))
    face_u2 = FaceDetection(face_id="f_unrec_2", photo_id="photo_2", bbox=[0, 0, 10, 10], det_score=0.82, embedding=np.array([0.22]*512, dtype=np.float32))

    unrec = UnrecognizedGroup(
        photo_ids=["photo_1", "photo_2"],
        faces=[
            {"face_id": "f_unrec_1", "photo_id": "photo_1", "face": "faces/f_unrec_1.jpg"},
            {"face_id": "f_unrec_2", "photo_id": "photo_2", "face": "faces/f_unrec_2.jpg"},
        ],
    )
    unrec._face_items = [
        {"face_obj": face_u1, "photo_id": "photo_1", "face_id": "f_unrec_1", "face": "faces/f_unrec_1.jpg"},
        {"face_obj": face_u2, "photo_id": "photo_2", "face_id": "f_unrec_2", "face": "faces/f_unrec_2.jpg"},
    ]

    photos = {
        "photo_1": PhotoRecord(photo_id="photo_1", original_path="/p1.jpg", file_name="p1.jpg", width=100, height=100, faces=[face_u1]),
        "photo_2": PhotoRecord(photo_id="photo_2", original_path="/p2.jpg", file_name="p2.jpg", width=100, height=100, faces=[face_u2]),
    }

    state.people = []
    state.base_people = []
    state.unrecognized = unrec
    state.base_unrecognized = unrec
    state.photos = photos

    # Create new person from f_unrec_1 and f_unrec_2
    res = client.post("/api/edits", json={
        "op": "assign",
        "face_ids": ["f_unrec_1", "f_unrec_2"],
        "person_id": None,
    })
    assert res.status_code == 200, res.text

    people_res = client.get("/api/people").json()
    assert len(people_res) == 1
    new_p = people_res[0]
    assert len(new_p["faces"]) == 2
    fids = [f["face_id"] for f in new_p["faces"]]
    assert "f_unrec_1" in fids and "f_unrec_2" in fids

    # Unrecognized group now empty
    unrec_res = client.get("/api/unrecognized").json()
    assert len(unrec_res["faces"]) == 0

def test_batch_assign_persists_in_edits_and_replays():
    """Verify batch assign schema and apply_edits replay without cluster IDs."""
    face_a = FaceDetection(face_id="f_anchor_1", photo_id="photo_1", bbox=[0, 0, 10, 10], det_score=0.95, embedding=np.array([0.1]*512, dtype=np.float32))
    face_u1 = FaceDetection(face_id="f_unrec_1", photo_id="photo_2", bbox=[0, 0, 10, 10], det_score=0.85, embedding=np.array([0.2]*512, dtype=np.float32))
    face_u2 = FaceDetection(face_id="f_unrec_2", photo_id="photo_3", bbox=[0, 0, 10, 10], det_score=0.82, embedding=np.array([0.22]*512, dtype=np.float32))

    person1 = PersonCluster(id="person_1", photo_ids=["photo_1"], faces=[face_a])
    unrec = UnrecognizedGroup(photo_ids=["photo_2", "photo_3"], faces=[
        {"face_id": "f_unrec_1", "photo_id": "photo_2", "face": "faces/f_unrec_1.jpg"},
        {"face_id": "f_unrec_2", "photo_id": "photo_3", "face": "faces/f_unrec_2.jpg"},
    ])
    unrec._face_items = [
        {"face_obj": face_u1, "photo_id": "photo_2", "face_id": "f_unrec_1", "face": "faces/f_unrec_1.jpg"},
        {"face_obj": face_u2, "photo_id": "photo_3", "face_id": "f_unrec_2", "face": "faces/f_unrec_2.jpg"},
    ]
    photos = {
        "photo_1": PhotoRecord(photo_id="photo_1", original_path="/p1.jpg", file_name="p1.jpg", width=100, height=100, faces=[face_a]),
        "photo_2": PhotoRecord(photo_id="photo_2", original_path="/p2.jpg", file_name="p2.jpg", width=100, height=100, faces=[face_u1]),
        "photo_3": PhotoRecord(photo_id="photo_3", original_path="/p3.jpg", file_name="p3.jpg", width=100, height=100, faces=[face_u2]),
    }

    edits_data = {
        "version": 1,
        "edits": [
            {"op": "assign", "face_ids": ["f_unrec_1", "f_unrec_2"], "person": ["f_anchor_1"]}
        ]
    }
    # Invariant: Zero cluster IDs in edits schema
    raw_str = json.dumps(edits_data)
    assert re.search(r"\bp\d{3}\b", raw_str) is None

    # Replay through apply_edits
    new_people, new_unrec, unapplied, stats = apply_edits([person1], unrec, edits_data, photos)
    assert len(unapplied) == 0
    assert stats["applied"] == 1
    assert len(new_people[0].faces) == 3
    assert len(new_unrec.faces) == 0
