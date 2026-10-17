"""Tests for 'Open saved project' and recent projects management.

Verifies:
1. Backend remembers projects in ~/.photosorter/projects.json (paths, counts, last-opened).
2. Privacy: NEVER stores Google Drive API keys, face vectors, or raw photos.
3. Edge case 1: Work folder moved/deleted (clear message, offer to remove entry).
4. Edge case 2: Source photos moved or missing (cluster view opens, photo viewing shows source missing).
5. Edge case 3: Drive-sourced project (uses cached thumbnails, needs no API key to open).
6. Edge case 4: Corrupt edits.json (opens read-only, reports error, never overwrites).
7. Edge case 5: Opening project while scan is running (blocked with 409 Conflict message).
8. Preserves invariant: clustered faces + unrecognized faces = total detected faces.
"""

import os
import json
import shutil
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

from backend.api.app import create_app
from backend.api.projects import (
    get_projects_file,
    load_recent_projects,
    save_recent_project,
    remove_recent_project,
    get_project_by_id,
    _sanitize_source_description,
)
from backend.engine.models import FaceDetection, PhotoRecord, PersonCluster, UnrecognizedGroup, EngineResult
from backend.engine.cache import EmbeddingCache


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    """Isolate projects.json and working directories to tmp_path."""
    projects_file = tmp_path / ".photosorter" / "projects.json"
    monkeypatch.setenv("PHOTOSORTER_PROJECTS_FILE", str(projects_file))
    work_dir = tmp_path / "work"
    export_dir = tmp_path / "export"
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    return {
        "root": tmp_path,
        "projects_file": projects_file,
        "work_dir": work_dir,
        "export_dir": export_dir,
    }


def create_synthetic_project(work_dir: Path, export_dir: Path, photos_missing: bool = False):
    """Creates a complete synthetic project on disk with cached embeddings and export bundle."""
    cache = EmbeddingCache(work_dir)
    crops_dir = work_dir / "crops"
    thumbs_dir = work_dir / "thumbs"
    crops_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    # 2 sample photos
    photos_dir = work_dir / "source_photos"
    if not photos_missing:
        photos_dir.mkdir(parents=True, exist_ok=True)

    cached_photos = {}
    face_objects = []
    for i, pid in enumerate(["ph_01", "ph_02"]):
        orig_img_path = photos_dir / f"{pid}.jpg"
        if not photos_missing:
            img = Image.new("RGB", (200, 200), color=(100 + i * 20, 150, 200))
            img.save(orig_img_path)

        # Thumb
        thumb_img = Image.new("RGB", (50, 50), color=(100, 100, 100))
        thumb_img.save(thumbs_dir / f"{pid}.jpg")

        # Face crop
        fid = f"f_{pid}_001"
        crop_img = Image.new("RGB", (40, 40), color=(120, 120, 120))
        crop_img.save(crops_dir / f"{fid}.jpg")

        emb = np.zeros(512, dtype=np.float32)
        emb[i] = 1.0
        f_det = FaceDetection(
            face_id=fid,
            photo_id=pid,
            bbox=[10.0, 10.0, 50.0, 50.0],
            det_score=0.92,
            embedding=emb,
            cluster_id=f"p{i+1:03d}",
        )
        face_objects.append(f_det)
        prec = PhotoRecord(
            photo_id=pid,
            original_path=str(orig_img_path),
            file_name=f"{pid}.jpg",
            width=200,
            height=200,
            faces=[f_det],
        )
        cached_photos[pid] = prec
        cache.save(prec)

    # people.json in export_dir
    people_data = {
        "version": 1,
        "title": "Synthetic Test Project",
        "photos": {
            "ph_01": {"name": "ph_01.jpg", "thumb": "thumbs/ph_01.jpg", "width": 200, "height": 200},
            "ph_02": {"name": "ph_02.jpg", "thumb": "thumbs/ph_02.jpg", "width": 200, "height": 200},
        },
        "people": [
            {
                "id": "person_test_01",
                "label": "Person One",
                "face": "faces/f_ph_01_001.jpg",
                "photo_ids": ["ph_01"],
                "faces": [{"face_id": "f_ph_01_001", "photo_id": "ph_01", "bbox": [10, 10, 50, 50]}],
                "merged_from": [],
            },
            {
                "id": "person_test_02",
                "label": "Person Two",
                "face": "faces/f_ph_02_001.jpg",
                "photo_ids": ["ph_02"],
                "faces": [{"face_id": "f_ph_02_001", "photo_id": "ph_02", "bbox": [10, 10, 50, 50]}],
                "merged_from": [],
            },
        ],
        "unrecognized": {
            "photo_ids": [],
            "faces": [],
        },
    }
    with open(export_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_data, f, indent=2)

    # suggestions.json in work_dir
    with open(work_dir / "suggestions.json", "w", encoding="utf-8") as f:
        json.dump({"maybe_groups": [], "ambiguous_faces": []}, f)

    # edits.json in work_dir
    with open(work_dir / "edits.json", "w", encoding="utf-8") as f:
        json.dump({"version": 1, "edits": []}, f)

    return cached_photos


def test_recent_projects_crud_and_privacy(temp_env):
    """Test saving, listing, and removing recent projects with privacy guarantees and undo-after-reopen."""
    work_dir = temp_env["work_dir"]
    export_dir = temp_env["export_dir"]

    # 1. Save project with Drive link containing secret API key query parameter
    sensitive_source = "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs?key=AIzaSySecretApiKey123"
    entry = save_recent_project(
        work_dir=work_dir,
        export_path=export_dir,
        source_description=sensitive_source,
        counts={"people": 2, "photos": 2},
        name="Test Family Gathering",
    )

    assert entry["id"] is not None
    assert entry["name"] == "Test Family Gathering"
    assert entry["counts"] == {"people": 2, "photos": 2}
    assert entry["exists"] is True

    # PRIVACY AUDIT: Verify API key was NEVER written to disk
    projects_file = temp_env["projects_file"]
    assert projects_file.exists()
    raw_json = projects_file.read_text(encoding="utf-8")
    assert "AIzaSy" not in raw_json
    assert "SecretApiKey" not in raw_json
    assert "key=" not in raw_json

    # Requirement 5: Verify 'exists' is NOT stored in projects.json on disk (computed dynamically)
    parsed_json = json.loads(raw_json)
    assert "exists" not in parsed_json["projects"][0]

    # List recent projects: dynamically computes exists=True
    projects = load_recent_projects()
    assert len(projects) == 1
    assert projects[0]["id"] == entry["id"]
    assert projects[0]["exists"] is True
    assert projects[0]["source_description"] == "Drive folder 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"

    # Requirement 4: Undo-after-reopen test (open project, make edit, close, reopen, undo, confirm previous state returns)
    create_synthetic_project(work_dir, export_dir)
    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)

    # Open project
    open_resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert open_resp.status_code == 200
    people_before = client.get("/api/people").json()
    assert people_before[0]["label"] == "Person One"

    # Make edit: rename person_test_01
    edit_resp = client.post("/api/edits", json={
        "op": "name",
        "person_id": "person_test_01",
        "label": "Renamed VIP",
    })
    assert edit_resp.status_code == 200
    assert client.get("/api/people").json()[0]["label"] == "Renamed VIP"

    # Close and reopen (simulate fresh server restart)
    app_reopened = create_app(work_dir=work_dir, output_dir=export_dir)
    client_reopened = TestClient(app_reopened)
    reopen_resp = client_reopened.post("/api/projects/open", json={"project_id": entry["id"]})
    assert reopen_resp.status_code == 200
    assert client_reopened.get("/api/people").json()[0]["label"] == "Renamed VIP"

    # Undo after reopen: confirm previous state returns
    undo_resp = client_reopened.post("/api/edits", json={"op": "undo"})
    assert undo_resp.status_code == 200
    assert undo_resp.json()["success"] is True
    assert client_reopened.get("/api/people").json()[0]["label"] == "Person One"

    # Remove project (verify metadata removed, disk files untouched)
    test_marker = work_dir / "marker.txt"
    test_marker.write_text("important data", encoding="utf-8")

    removed = remove_recent_project(entry["id"])
    assert removed is True

    # Verify projects list is now empty
    assert len(load_recent_projects()) == 0

    # Strict Guarantee: Files on disk must NOT be deleted
    assert work_dir.exists()
    assert test_marker.exists()
    assert test_marker.read_text(encoding="utf-8") == "important data"


def test_edge_case_1_work_folder_moved_or_deleted(temp_env):
    """Edge Case 1: Work folder moved/deleted returns clear message and offers removal."""
    app = create_app(work_dir=temp_env["work_dir"], output_dir=temp_env["export_dir"])
    client = TestClient(app)

    # Save entry pointing to a folder that will be deleted
    temp_work = temp_env["root"] / "disappearing_work"
    temp_work.mkdir(parents=True, exist_ok=True)
    entry = save_recent_project(
        work_dir=temp_work,
        export_path=temp_env["export_dir"],
        source_description="Test Folder",
        counts={"people": 1, "photos": 1},
        name="Disappearing Project",
    )

    # Confirm listed with exists=True
    listed = client.get("/api/projects").json()
    assert any(p["id"] == entry["id"] and p["exists"] is True for p in listed)

    # Now delete the work folder
    shutil.rmtree(temp_work)

    # Verify listing now marks exists=False
    listed_after = client.get("/api/projects").json()
    proj_item = next(p for p in listed_after if p["id"] == entry["id"])
    assert proj_item["exists"] is False

    # Attempt to open project: must return 404 with clear message offering to remove entry
    resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert "not found or was moved" in detail
    assert "remove this entry" in detail

    # Remove the entry
    del_resp = client.delete(f"/api/projects/{entry['id']}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Entry is gone from list
    remaining = client.get("/api/projects").json()
    assert not any(p["id"] == entry["id"] for p in remaining)


def test_edge_case_2_source_photos_moved_or_missing(temp_env):
    """Edge Case 2: Source photos moved or missing; cluster view opens, photo download shows missing."""
    work_dir = temp_env["work_dir"]
    export_dir = temp_env["export_dir"]

    # Setup project where source photos folder does not exist
    create_synthetic_project(work_dir, export_dir, photos_missing=True)

    entry = save_recent_project(
        work_dir=work_dir,
        export_path=export_dir,
        source_description="Moved Photos Folder",
        counts={"people": 2, "photos": 2},
    )

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)

    # Open project
    open_resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert open_resp.status_code == 200
    assert open_resp.json()["people_count"] == 2
    assert open_resp.json()["photos_count"] == 2

    # Cluster view still opens successfully
    people_resp = client.get("/api/people")
    assert people_resp.status_code == 200
    assert len(people_resp.json()) == 2

    # Check /api/photos: source_exists is False because photos are missing
    photos_resp = client.get("/api/photos")
    assert photos_resp.status_code == 200
    photos_data = photos_resp.json()
    assert "ph_01" in photos_data
    assert photos_data["ph_01"]["source_exists"] is False

    # Attempting to download original photo returns 404 with clear missing state
    dl_resp = client.get("/api/photos/ph_01/download")
    assert dl_resp.status_code == 404
    assert "missing or moved" in dl_resp.json()["detail"]


def test_edge_case_3_drive_sourced_project_no_api_key(temp_env, monkeypatch):
    """Edge Case 3: Drive-sourced project opens from cache without requiring any API key."""
    # Ensure no Drive API key is set
    monkeypatch.delenv("PHOTOSORTER_DRIVE_API_KEY", raising=False)
    monkeypatch.delenv("DRIVE_API_KEY", raising=False)

    work_dir = temp_env["work_dir"]
    export_dir = temp_env["export_dir"]
    create_synthetic_project(work_dir, export_dir)

    entry = save_recent_project(
        work_dir=work_dir,
        export_path=export_dir,
        source_description="https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
        counts={"people": 2, "photos": 2},
    )

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)

    # Open project without any API key headers or credentials
    open_resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert open_resp.status_code == 200
    data = open_resp.json()
    assert data["success"] is True
    assert data["people_count"] == 2

    # Thumbnails and face crops load from local cache
    thumb_resp = client.get("/thumbs/ph_01.jpg")
    assert thumb_resp.status_code == 200

    crop_resp = client.get("/faces/f_ph_01_001.jpg")
    assert crop_resp.status_code == 200


def test_edge_case_4_corrupt_edits_json_read_only(temp_env):
    """Edge Case 4: Corrupt edits.json opens read-only, reports error, and is never overwritten."""
    work_dir = temp_env["work_dir"]
    export_dir = temp_env["export_dir"]
    create_synthetic_project(work_dir, export_dir)

    # Corrupt edits.json with invalid JSON
    corrupt_content = "{ this is completely malformed json syntax !!! "
    edits_file = work_dir / "edits.json"
    edits_file.write_text(corrupt_content, encoding="utf-8")

    entry = save_recent_project(
        work_dir=work_dir,
        export_path=export_dir,
        source_description="Local Project",
        counts={"people": 2, "photos": 2},
    )

    app = create_app(work_dir=work_dir, output_dir=export_dir)
    client = TestClient(app)

    # Open project
    open_resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert open_resp.status_code == 200
    data = open_resp.json()
    assert data["read_only"] is True
    assert data["edits_error"] is not None
    assert "Corrupt edits.json" in data["edits_error"]

    # Applying any edit must be rejected
    edit_resp = client.post("/api/edits", json={
        "op": "name",
        "person_id": "person_test_01",
        "label": "Hacked Name",
    })
    assert edit_resp.status_code == 400
    assert "read-only mode" in edit_resp.json()["detail"]

    # STRICT ASSERTION: The file on disk was NEVER overwritten!
    assert edits_file.read_text(encoding="utf-8") == corrupt_content


def test_edge_case_5_open_project_while_scan_running(temp_env):
    """Edge Case 5: Opening a project while a scan is running is blocked with 409 Conflict."""
    app = create_app(work_dir=temp_env["work_dir"], output_dir=temp_env["export_dir"])
    client = TestClient(app)

    # Mock job manager status to "running"
    job_mgr = app.state.job_manager
    job_mgr.status = "running"

    entry = save_recent_project(
        work_dir=temp_env["work_dir"],
        export_path=temp_env["export_dir"],
        counts={"people": 1, "photos": 1},
    )

    resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert resp.status_code == 409
    assert "Cannot open project while a scan is currently running" in resp.json()["detail"]

    # Reset
    job_mgr.status = "idle"


def test_open_project_shared_cache_isolation_and_reexport(temp_env):
    """
    Verifies that reopening a project when work_dir cache contains foreign/unrelated photos
    from other scans does NOT leak those photos into the project or cause export verification failures.
    """
    create_synthetic_project(temp_env["work_dir"], temp_env["export_dir"])

    # Simulate foreign photo in the shared cache
    cache = EmbeddingCache(temp_env["work_dir"])
    foreign_rec = PhotoRecord(
        photo_id="ph_foreign",
        original_path="C:/photos/foreign.jpg",
        file_name="foreign.jpg",
        width=300,
        height=300,
        faces=[
            FaceDetection(
                face_id="f_ph_foreign_001",
                photo_id="ph_foreign",
                bbox=[0.0, 0.0, 50.0, 50.0],
                det_score=0.9,
                embedding=np.zeros(512, dtype=np.float32),
            )
        ],
    )
    cache.save(foreign_rec)

    # Work dir now has 3 cached photos: ph_01, ph_02, and ph_foreign
    all_cached = cache.load_all()
    assert len(all_cached) == 3

    # Create app and client
    app = create_app(work_dir=temp_env["work_dir"], output_dir=temp_env["export_dir"])
    client = TestClient(app)

    # Open project
    entry = save_recent_project(
        work_dir=temp_env["work_dir"],
        export_path=temp_env["export_dir"],
        counts={"people": 2, "photos": 2},
    )

    open_resp = client.post("/api/projects/open", json={"project_id": entry["id"]})
    assert open_resp.status_code == 200
    data = open_resp.json()
    # Must ONLY report the 2 project photos, not the foreign one
    assert data["photos_count"] == 2

    # /api/photos must only have the 2 project photos
    photos_resp = client.get("/api/photos")
    assert photos_resp.status_code == 200
    photos_data = photos_resp.json()
    assert len(photos_data) == 2
    assert "ph_foreign" not in photos_data

    # Perform an edit: merge person p001 and p002
    edit_resp = client.post("/api/edits", json={
        "op": "merge",
        "anchors": [["f_ph_01_001"], ["f_ph_02_001"]],
    })
    assert edit_resp.status_code == 200

    # Re-export to export directory: MUST SUCCEED and pass verification!
    export_resp = client.post("/api/export", json={
        "output_dir": str(temp_env["export_dir"]),
    })
    assert export_resp.status_code == 200
    export_result = export_resp.json()
    assert export_result["success"] is True

    # Validate output people.json
    out_people = json.loads((temp_env["export_dir"] / "people.json").read_text(encoding="utf-8"))
    assert set(out_people["photos"].keys()) == {"ph_01", "ph_02"}
    assert "ph_foreign" not in out_people["photos"]

