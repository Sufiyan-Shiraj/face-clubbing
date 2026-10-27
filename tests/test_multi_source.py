"""Comprehensive test suite for Phase V2-2 Piece 1:
Project Model v2 & Multi-Source Scan Backend Foundation.

Verifies:
1. Multi-source scanning across multiple local directories into a single unified project.
2. Cross-source photo deduplication (identical photos indexed once, deduplicated via SHA-256).
3. Cross-source fault isolation (missing or unreadable folders do not abort the job).
4. Project manifest v2 generation and persistence in export bundle and .work folder.
5. Backwards-compatible loading and migration of legacy v1 projects.
6. API endpoint GET /api/project/sources and open_saved_project source metadata.
"""

import os
import json
import shutil
import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from fastapi.testclient import TestClient

from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.engine.models import EngineResult, PhotoRecord, PersonCluster, UnrecognizedGroup, FaceDetection
from backend.engine.exporter import BundleExporter
from backend.engine.cache import EmbeddingCache
from backend.api.app import create_app
from backend.api.state import AppState
from backend.api.projects import save_recent_project, load_recent_projects


class MockFaceDetector:
    """Mock detector to avoid needing insightface runtime weights for unit tests."""
    def __init__(self, *args, **kwargs):
        pass

    def detect_and_embed(self, orig_rgb, photo_id):
        emb = np.random.randn(512).astype(np.float32)
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


@pytest.fixture
def multi_source_env(tmp_path, monkeypatch):
    """Sets up a clean temporary environment with folders for multi-source scans."""
    projects_file = tmp_path / ".photosorter" / "projects.json"
    monkeypatch.setenv("PHOTOSORTER_PROJECTS_FILE", str(projects_file))

    work_dir = tmp_path / "work"
    export_dir = tmp_path / "export"
    source_a = tmp_path / "source_folder_a"
    source_b = tmp_path / "source_folder_b"
    work_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    source_a.mkdir(parents=True, exist_ok=True)
    source_b.mkdir(parents=True, exist_ok=True)

    # Source A has 3 photos (img1, img2, img3)
    img1_path = source_a / "photo_a1.jpg"
    img2_path = source_a / "photo_a2.jpg"
    img3_path = source_a / "photo_a3.jpg"

    img_data_1 = Image.new("RGB", (120, 120), color=(200, 50, 50))
    img_data_2 = Image.new("RGB", (120, 120), color=(50, 200, 50))
    img_data_3 = Image.new("RGB", (120, 120), color=(50, 50, 200))
    img_data_1.save(img1_path)
    img_data_2.save(img2_path)
    img_data_3.save(img3_path)

    # Source B has 2 photos: one unique (img4) and one duplicate of img1
    img4_path = source_b / "photo_b1.jpg"
    img_dup_path = source_b / "photo_b_duplicate.jpg"
    img_data_4 = Image.new("RGB", (120, 120), color=(180, 180, 50))
    img_data_4.save(img4_path)
    # Exact copy of img1 bytes
    shutil.copy2(img1_path, img_dup_path)

    return {
        "root": tmp_path,
        "work_dir": work_dir,
        "export_dir": export_dir,
        "source_a": source_a,
        "source_b": source_b,
        "img1": img1_path,
        "img2": img2_path,
        "img3": img3_path,
        "img4": img4_path,
        "dup": img_dup_path,
    }


def test_multi_source_scan_and_deduplication(multi_source_env, monkeypatch):
    """Verifies that multiple sources are scanned and identical photos across sources are deduplicated."""
    env = multi_source_env
    monkeypatch.setattr("backend.engine.pipeline.FaceDetector", MockFaceDetector)

    sources_config = [
        {"id": "src_01", "source_type": "local", "path": str(env["source_a"]), "label": "Source Folder A"},
        {"id": "src_02", "source_type": "local", "path": str(env["source_b"]), "label": "Source Folder B"},
    ]

    config = EngineConfig(
        input_path=str(env["source_a"]),
        sources=sources_config,
        output_dir=env["export_dir"],
        cache_dir=env["work_dir"],
        distance_threshold=0.50,
    )

    result = run_pipeline(config)

    # 1. Total scanned photos must be 4 unique (3 from A, 1 unique from B, duplicate skipped)
    assert len(result.photos) == 4
    assert hasattr(result, "sources")
    assert len(result.sources) == 2

    # Verify source metadata
    src_a = next(s for s in result.sources if s["id"] == "src_01")
    src_b = next(s for s in result.sources if s["id"] == "src_02")
    assert src_a["status"] == "completed"
    assert src_a["photo_count"] == 3
    assert src_b["status"] == "completed"
    assert src_b["photo_count"] == 1  # 1 unique, 1 duplicate ignored

    # Check manifest
    assert result.manifest is not None
    assert result.manifest["schema_version"] == 2
    assert result.manifest["total_photos"] == 4
    assert len(result.manifest["sources"]) == 2


def test_multi_source_fault_isolation(multi_source_env, monkeypatch):
    """Verifies that an invalid/missing source folder does not fail other valid sources."""
    env = multi_source_env
    monkeypatch.setattr("backend.engine.pipeline.FaceDetector", MockFaceDetector)
    missing_dir = env["root"] / "non_existent_folder_xyz"

    sources_config = [
        {"id": "src_valid", "source_type": "local", "path": str(env["source_a"]), "label": "Valid Folder"},
        {"id": "src_broken", "source_type": "local", "path": str(missing_dir), "label": "Broken Folder"},
    ]

    config = EngineConfig(
        input_path=str(env["source_a"]),
        sources=sources_config,
        output_dir=env["export_dir"],
        cache_dir=env["work_dir"],
    )

    # Must complete without unhandled exception
    result = run_pipeline(config)

    assert len(result.sources) == 2
    valid_src = next(s for s in result.sources if s["id"] == "src_valid")
    broken_src = next(s for s in result.sources if s["id"] == "src_broken")

    assert valid_src["status"] == "completed"
    assert valid_src["photo_count"] == 3
    assert broken_src["status"] == "failed"
    assert "error" in broken_src


def test_manifest_v2_export_and_persistence(multi_source_env):
    """Verifies manifest.json v2 generation in both export bundle and work directory."""
    env = multi_source_env

    # Create synthetic result
    p1 = PhotoRecord(
        photo_id="p1",
        original_path=str(env["img1"]),
        file_name="p1.jpg",
        width=100,
        height=100,
        source_id="src_01",
        source_label="Camera Roll A",
        faces=[
            FaceDetection(
                face_id="f1",
                photo_id="p1",
                bbox=[0, 0, 50, 50],
                det_score=0.9,
                embedding=np.ones(512, dtype=np.float32),
            )
        ],
    )
    p2 = PhotoRecord(
        photo_id="p2",
        original_path=str(env["img4"]),
        file_name="p2.jpg",
        width=100,
        height=100,
        source_id="src_02",
        source_label="Camera Roll B",
        faces=[
            FaceDetection(
                face_id="f2",
                photo_id="p2",
                bbox=[0, 0, 50, 50],
                det_score=0.9,
                embedding=np.ones(512, dtype=np.float32),
            )
        ],
    )

    photos = {"p1": p1, "p2": p2}
    people = [
        PersonCluster(id="person_cluster_01", photo_ids=["p1", "p2"], faces=[p1.faces[0], p2.faces[0]]),
    ]
    unrec = UnrecognizedGroup(photo_ids=[], faces=[])
    sources = [
        {"id": "src_01", "source_type": "local", "path": str(env["source_a"]), "label": "Camera Roll A", "photo_count": 1},
        {"id": "src_02", "source_type": "local", "path": str(env["source_b"]), "label": "Camera Roll B", "photo_count": 1},
    ]

    res = EngineResult(
        photos=photos,
        people=people,
        unrecognized=unrec,
        distance_threshold=0.50,
        sources=sources,
    )

    exporter = BundleExporter(
        output_dir=env["export_dir"],
        cache_dir=env["work_dir"],
    )
    out_dir = exporter.export(res, title="Multi Source Gallery")
    assert out_dir == env["export_dir"]

    # 1. manifest.json written to output_dir AND cache_dir
    export_manifest_p = env["export_dir"] / "manifest.json"
    work_manifest_p = env["work_dir"] / "manifest.json"
    assert export_manifest_p.exists()
    assert work_manifest_p.exists()

    with open(export_manifest_p, "r", encoding="utf-8") as f:
        saved_m = json.load(f)

    # 2. Manifest has schema_version 2, photo origins, and sources
    assert saved_m["schema_version"] == 2
    assert saved_m["total_photos"] == 2
    assert saved_m["total_people"] == 1
    assert "photo_origins" in saved_m
    assert saved_m["photo_origins"]["p1"]["source_id"] == "src_01"
    assert saved_m["photo_origins"]["p2"]["source_id"] == "src_02"
    assert len(saved_m["sources"]) == 2

    # 3. people.json has schema_version 2 and sources
    with open(env["export_dir"] / "people.json", "r", encoding="utf-8") as f:
        saved_p = json.load(f)
    assert saved_p.get("schema_version") == 2
    assert "sources" in saved_p
    assert len(saved_p["sources"]) == 2


def test_legacy_v1_project_backward_compatibility_migration(multi_source_env):
    """Verifies that legacy v1 projects (without manifest v2 or sources) load and auto-migrate seamlessly."""
    env = multi_source_env

    # Construct a legacy v1 project (version 1 people.json, no manifest.json)
    cache = EmbeddingCache(env["work_dir"])
    p_rec = PhotoRecord(
        photo_id="ph_legacy",
        original_path=str(env["img1"]),
        file_name="legacy.jpg",
        width=100,
        height=100,
        faces=[
            FaceDetection(
                face_id="f_legacy_01",
                photo_id="ph_legacy",
                bbox=[0, 0, 50, 50],
                det_score=0.95,
                embedding=np.ones(512, dtype=np.float32),
            )
        ],
    )
    cache.save(p_rec)

    legacy_people_json = {
        "version": 1,
        "people": [
            {
                "id": "person_legacy",
                "photos": ["ph_legacy"],
                "faces": [{"face_id": "f_legacy_01", "photo_id": "ph_legacy", "bbox": [0, 0, 50, 50]}],
                "face": "faces/person_legacy.jpg",
            }
        ],
        "photos": {
            "ph_legacy": {"name": "legacy.jpg", "thumb": "thumbs/ph_legacy.jpg"}
        },
        "unrecognized": {"photo_ids": [], "faces": []},
    }
    with open(env["export_dir"] / "people.json", "w", encoding="utf-8") as f:
        json.dump(legacy_people_json, f)

    state = AppState(work_dir=env["work_dir"], output_dir=env["export_dir"])
    res = state.open_saved_project(work_dir=env["work_dir"], export_path=env["export_dir"])

    assert res["people_count"] == 1
    assert res["photos_count"] == 1
    # Auto-synthesized v1 source
    assert "sources" in res
    assert len(res["sources"]) == 1
    assert res["sources"][0]["id"] == "src_01"
    assert res["sources"][0]["source_type"] == "local"

    # Verify projects.json persistence preserves migration
    save_recent_project(
        work_dir=env["work_dir"],
        export_path=env["export_dir"],
        source_description="Legacy Album",
        counts={"people": 1, "photos": 1},
        schema_version=1,
    )

    recent = load_recent_projects()
    assert len(recent) >= 1
    target_p = next(p for p in recent if Path(p["work_dir"]).resolve() == env["work_dir"].resolve())
    assert target_p["schema_version"] == 2
    assert len(target_p["sources"]) >= 1


def test_api_project_sources_endpoint(multi_source_env):
    """Verifies GET /api/project/sources returns correct sources and schema version."""
    env = multi_source_env
    app = create_app(work_dir=env["work_dir"], output_dir=env["export_dir"])
    client = TestClient(app)

    # 1. Initially empty
    resp = client.get("/api/project/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sources"] == 0
    assert data["sources"] == []

    # 2. Simulate opening a project with 2 sources
    state: AppState = app.state.app_state
    state.sources = [
        {"id": "src_01", "source_type": "local", "path": str(env["source_a"]), "label": "Folder A", "photo_count": 3},
        {"id": "src_02", "source_type": "local", "path": str(env["source_b"]), "label": "Folder B", "photo_count": 1},
    ]
    state.project_manifest = {"schema_version": 2, "sources": state.sources}
    state.project_active = True

    resp2 = client.get("/api/project/sources")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total_sources"] == 2
    assert len(data2["sources"]) == 2
    assert data2["schema_version"] == 2
    assert data2["sources"][0]["id"] == "src_01"
    assert data2["sources"][1]["id"] == "src_02"
