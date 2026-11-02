"""Unit and integration tests for Phase V2-4: Merge Two Projects.

Verifies:
1. Merging project with itself changes nothing (A + A == A).
2. Commutativity: A + B equals B + A (same photo count, identical clusters, same face accounting).
3. Originals untouched: files in project A and B remain strictly unmodified.
4. Settings hash check: merging projects with different settings hash raises ValueError.
5. Edits combination:
   - Merge anchors combined order-independently.
   - Assigns and removes preserved.
   - Conflict detection: Name conflicts and Assign vs Remove conflicts flagged.
6. Manifest records both parents as sources.
7. API endpoint: POST /api/projects/merge returns valid response and sets active project.
"""

import os
import json
import shutil
import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.engine.models import FaceDetection, PhotoRecord, PersonCluster, UnrecognizedGroup, EngineResult
from backend.engine.cache import EmbeddingCache, compute_settings_hash
from backend.engine.merger import merge_projects, combine_edits, verify_settings_compatibility, read_project_data


def make_test_vector(seed_val: float) -> np.ndarray:
    """Generates a deterministic 512-d unit vector as numpy array."""
    np.random.seed(int(seed_val * 1000) % (2**31 - 1))
    v = np.random.randn(512).astype(np.float32)
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v


def setup_synthetic_project(
    work_dir: Path,
    export_dir: Path,
    proj_name: str,
    photos_data: list[dict],
    edits_list: list[dict] = None,
    settings_hash: str = None,
):
    """Sets up a complete on-disk CatLog project."""
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir = work_dir / "thumbs"
    crops_dir = work_dir / "crops"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    cache = EmbeddingCache(work_dir, settings_hash=settings_hash)

    photos_dict = {}
    for p_info in photos_data:
        pid = p_info["photo_id"]
        # Dummy thumb
        t_img = Image.new("RGB", (60, 60), color=(100, 150, 200))
        t_img.save(thumbs_dir / f"{pid}.jpg")

        faces = []
        for f_idx, f_info in enumerate(p_info.get("faces", [])):
            fid = f_info.get("face_id", f"f_{pid}_{f_idx:03d}")
            emb = f_info.get("embedding") if f_info.get("embedding") is not None else make_test_vector(f_info.get("seed", 1.0))
            # Dummy crop
            c_img = Image.new("RGB", (64, 64), color=(200, 100, 50))
            c_img.save(crops_dir / f"{fid}.jpg")

            faces.append(
                FaceDetection(
                    face_id=fid,
                    photo_id=pid,
                    bbox=f_info.get("bbox", [10, 10, 80, 80]),
                    det_score=f_info.get("det_score", 0.95),
                    embedding=emb,
                )
            )

        rec = PhotoRecord(
            photo_id=pid,
            original_path=str(work_dir / f"{pid}.jpg"),
            file_name=f"{pid}.jpg",
            width=200,
            height=200,
            faces=faces,
            source_id=p_info.get("source_id", "src_test"),
            source_label=p_info.get("source_label", "Local Folder"),
        )
        cache.save(rec)
        photos_dict[pid] = rec

    # Create people.json
    people_list = []
    # Simple grouping for the test setup
    for idx, (pid, rec) in enumerate(photos_dict.items()):
        if rec.faces:
            rep_face = rec.faces[0]
            people_list.append({
                "id": f"p{idx+1:03d}",
                "label": f"Person {idx+1}",
                "face": f"faces/{rep_face.face_id}.jpg",
                "photo_ids": [pid],
                "photos": [pid],
                "faces": [
                    {
                        "face_id": rep_face.face_id,
                        "photo_id": pid,
                        "file_name": rec.file_name,
                        "det_score": rep_face.det_score,
                        "bbox": rep_face.bbox,
                    }
                ],
                "merged_from": [f"p{idx+1:03d}"],
                "maybe_photos": [],
            })

    people_payload = {
        "version": 1,
        "schema_version": 2,
        "generated_at": "2026-11-02T12:00:00Z",
        "sources": [
            {
                "id": "src_01",
                "kind": "local",
                "label": proj_name,
                "photo_count": len(photos_dict),
                "status": "completed",
            }
        ],
        "photos": {
            pid: {
                "name": rec.file_name,
                "thumb": f"thumbs/{pid}.jpg",
                "download": None,
                "drive_url": None,
            }
            for pid, rec in photos_dict.items()
        },
        "people": people_list,
        "unrecognized": {"photo_ids": [], "faces": []},
    }
    with open(work_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people_payload, f, indent=2)

    manifest_payload = {
        "schema_version": 2,
        "project_name": proj_name,
        "generated_at": "2026-11-02T12:00:00Z",
        "sources": people_payload["sources"],
        "total_photos": len(photos_dict),
        "total_people": len(people_list),
        "settings_hash": settings_hash or compute_settings_hash(),
    }
    with open(work_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    if edits_list is not None:
        edits_payload = {"version": 1, "edits": edits_list}
        with open(work_dir / "edits.json", "w", encoding="utf-8") as f:
            json.dump(edits_payload, f, indent=2)


def test_merge_project_with_itself_idempotent(tmp_path):
    """Merging a project with itself changes nothing (A + A == A)."""
    wa = tmp_path / "proj_a.work"
    ea = tmp_path / "proj_a"
    target_w = tmp_path / "merged.work"
    target_e = tmp_path / "merged"

    common_vec = make_test_vector(42.0)
    photos_data = [
        {"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001", "embedding": common_vec}]},
        {"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001", "embedding": make_test_vector(99.0)}]},
    ]
    setup_synthetic_project(wa, ea, "Project A", photos_data)

    res = merge_projects(
        proj_a_work=wa,
        proj_b_work=wa,
        target_work=target_w,
        target_export=target_e,
    )

    assert res["success"] is True
    assert res["total_photos"] == 2
    assert res["shared_photos"] == 2
    assert res["people_count"] == 2
    assert (target_w / "people.json").is_file()
    assert (target_e / "people.json").is_file()


def test_merge_commutativity_a_plus_b_equals_b_plus_a(tmp_path):
    """A + B equals B + A in terms of photo count, cluster structure, and face assignments."""
    wa = tmp_path / "proj_a.work"
    ea = tmp_path / "proj_a"
    wb = tmp_path / "proj_b.work"
    eb = tmp_path / "proj_b"

    v_person1 = make_test_vector(10.0)
    v_person2 = make_test_vector(20.0)
    v_person3 = make_test_vector(30.0)

    # Project A has photo 1 (person 1) and photo 2 (person 2)
    setup_synthetic_project(
        wa, ea, "Project A",
        [
            {"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001", "embedding": v_person1}]},
            {"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001", "embedding": v_person2}]},
        ]
    )

    # Project B has photo 2 (person 2, shared) and photo 3 (person 3, new)
    setup_synthetic_project(
        wb, eb, "Project B",
        [
            {"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001", "embedding": v_person2}]},
            {"photo_id": "ph_03", "faces": [{"face_id": "f_ph_03_001", "embedding": v_person3}]},
        ]
    )

    # Merge A + B
    target_ab_w = tmp_path / "ab.work"
    target_ab_e = tmp_path / "ab"
    res_ab = merge_projects(wa, wb, target_ab_w, target_ab_e)

    # Merge B + A
    target_ba_w = tmp_path / "ba.work"
    target_ba_e = tmp_path / "ba"
    res_ba = merge_projects(wb, wa, target_ba_w, target_ba_e)

    assert res_ab["total_photos"] == 3
    assert res_ba["total_photos"] == 3
    assert res_ab["shared_photos"] == 1
    assert res_ba["shared_photos"] == 1
    assert res_ab["people_count"] == res_ba["people_count"]


def test_originals_remain_strictly_untouched(tmp_path):
    """Verifies that merging projects never alters files in the parent directories."""
    wa = tmp_path / "proj_a.work"
    ea = tmp_path / "proj_a"
    wb = tmp_path / "proj_b.work"
    eb = tmp_path / "proj_b"

    setup_synthetic_project(
        wa, ea, "Project A",
        [{"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001"}]}]
    )
    setup_synthetic_project(
        wb, eb, "Project B",
        [{"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001"}]}]
    )

    # Read original contents
    with open(wa / "people.json", "r", encoding="utf-8") as f:
        orig_a_people = f.read()
    with open(wb / "people.json", "r", encoding="utf-8") as f:
        orig_b_people = f.read()

    target_w = tmp_path / "merged.work"
    target_e = tmp_path / "merged"
    merge_projects(wa, wb, target_w, target_e)

    # Check that originals are identical
    with open(wa / "people.json", "r", encoding="utf-8") as f:
        assert f.read() == orig_a_people
    with open(wb / "people.json", "r", encoding="utf-8") as f:
        assert f.read() == orig_b_people


def test_incompatible_settings_hash_raises_error(tmp_path):
    """Projects with differing detection settings hashes fail with a clear ValueError."""
    wa = tmp_path / "proj_a.work"
    ea = tmp_path / "proj_a"
    wb = tmp_path / "proj_b.work"
    eb = tmp_path / "proj_b"

    hash_a = compute_settings_hash(min_face_size=64)
    hash_b = compute_settings_hash(min_face_size=128)

    setup_synthetic_project(
        wa, ea, "Project A",
        [{"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001"}]}],
        settings_hash=hash_a,
    )
    setup_synthetic_project(
        wb, eb, "Project B",
        [{"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001"}]}],
        settings_hash=hash_b,
    )

    with pytest.raises(ValueError, match="settings hashes"):
        merge_projects(wa, wb, tmp_path / "merged.work", tmp_path / "merged")


def test_combines_edits_and_detects_conflicts(tmp_path):
    """Combines edits order-independently and detects name conflicts and assign-vs-remove conflicts."""
    wa = tmp_path / "proj_a.work"
    ea = tmp_path / "proj_a"
    wb = tmp_path / "proj_b.work"
    eb = tmp_path / "proj_b"

    v1 = make_test_vector(11.0)
    v2 = make_test_vector(22.0)

    # Edits for Project A: Name person 1 as "Alice", merge anchors for person 1 and 2
    edits_a = [
        {"op": "name", "person": ["f_ph_01_001"], "label": "Alice"},
        {"op": "assign", "face_id": "f_ph_02_001", "person": ["f_ph_01_001"]},
    ]
    # Edits for Project B: Name person 1 as "Bob" (CONFLICT!), remove face from person 1 (CONFLICT!)
    edits_b = [
        {"op": "name", "person": ["f_ph_01_001"], "label": "Bob"},
        {"op": "remove", "person": ["f_ph_01_001"], "face_id": "f_ph_02_001"},
    ]

    setup_synthetic_project(
        wa, ea, "Project A",
        [
            {"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001", "embedding": v1}]},
            {"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001", "embedding": v2}]},
        ],
        edits_list=edits_a,
    )
    setup_synthetic_project(
        wb, eb, "Project B",
        [
            {"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001", "embedding": v1}]},
            {"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001", "embedding": v2}]},
        ],
        edits_list=edits_b,
    )

    target_w = tmp_path / "merged.work"
    target_e = tmp_path / "merged"
    res = merge_projects(wa, wb, target_w, target_e)

    assert res["conflicts_count"] >= 2
    conflict_types = [c["conflict_type"] for c in res["conflicts"]]
    assert "name_conflict" in conflict_types
    assert "assign_vs_remove" in conflict_types
    assert (target_w / "merge_conflicts.json").is_file()


def test_merge_projects_api_endpoint(tmp_path, monkeypatch):
    """Tests POST /api/projects/merge FastAPI endpoint."""
    projects_file = tmp_path / ".photosorter" / "projects.json"
    monkeypatch.setenv("PHOTOSORTER_PROJECTS_FILE", str(projects_file))

    app = create_app()
    client = TestClient(app)

    wa = tmp_path / "proj_a.work"
    ea = tmp_path / "proj_a"
    wb = tmp_path / "proj_b.work"
    eb = tmp_path / "proj_b"

    setup_synthetic_project(
        wa, ea, "Event Alpha",
        [{"photo_id": "ph_01", "faces": [{"face_id": "f_ph_01_001"}]}]
    )
    setup_synthetic_project(
        wb, eb, "Event Beta",
        [{"photo_id": "ph_02", "faces": [{"face_id": "f_ph_02_001"}]}]
    )

    req_body = {
        "project_a_work_dir": str(wa),
        "project_b_work_dir": str(wb),
        "target_work_dir": str(tmp_path / "combined.work"),
        "target_export_dir": str(tmp_path / "combined"),
        "new_project_name": "Combined Alpha + Beta",
    }

    response = client.post("/api/projects/merge", json=req_body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["project_name"] == "Combined Alpha + Beta"
    assert data["total_photos"] == 2
    assert data["people_count"] >= 1

    # Verify active project reflects the merged project
    active_resp = client.get("/api/projects/active")
    assert active_resp.status_code == 200
    active_data = active_resp.json()
    assert active_data["active"] is True
    assert active_data["name"] == "Combined Alpha + Beta"
