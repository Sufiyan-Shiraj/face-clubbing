"""Tests for pipeline execution and work directory / public bundle separation."""

import json
from pathlib import Path
from PIL import Image
import numpy as np

from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.engine.cache import EmbeddingCache
from backend.engine.models import PhotoRecord, FaceDetection


def test_pipeline_organizer_and_public_bundle(tmp_path: Path):
    """Verifies that run_pipeline outputs merged_from in people.json, id_map.json and suggestions.json in work dir, and clean public bundle."""
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    out_dir = tmp_path / "export"
    work_dir = tmp_path / "export.work"

    # Create 3 synthetic photos with distinct content (different colors so hash differs)
    p1 = photos_dir / "img1.jpg"
    p2 = photos_dir / "img2.jpg"
    p3 = photos_dir / "img3.jpg"
    for i, p in enumerate([p1, p2, p3]):
        img = Image.new("RGB", (200, 200), color=(100 + i * 20, 120 + i * 20, 140 + i * 20))
        img.save(p)

    # Pre-populate cache in work_dir so detector is not invoked
    cache = EmbeddingCache(work_dir)
    e0 = np.zeros(512, dtype=np.float32)
    e0[0] = 1.0
    e1 = np.zeros(512, dtype=np.float32)
    e1[1] = 1.0

    # Photos with faces
    f1 = FaceDetection(
        face_id="f_p1_001",
        photo_id="img1_id",
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=0.92,
        embedding=e0,
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )
    f2 = FaceDetection(
        face_id="f_p2_001",
        photo_id="img2_id",
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=0.91,
        embedding=e0,  # Same embedding -> merges/clusters with f1
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )
    f3 = FaceDetection(
        face_id="f_p3_001",
        photo_id="img3_id",
        bbox=[10.0, 10.0, 80.0, 80.0],
        det_score=0.90,
        embedding=e1,  # Different embedding -> separate cluster
        pose=[0.0, 0.0, 0.0],
        is_good_quality=True,
    )

    from backend.engine.scanner import PhotoScanner
    with PhotoScanner(photos_dir) as scanner:
        scanned = scanner.scan()
    assert len(scanned) == 3
    pid_map = {item.file_name: item.photo_id for item in scanned}

    # Save cached records with the scanned photo IDs
    for p_file, face_obj in [("img1.jpg", f1), ("img2.jpg", f2), ("img3.jpg", f3)]:
        real_pid = pid_map[p_file]
        face_obj.photo_id = real_pid
        face_obj.face_id = f"f_{real_pid}_001"
        rec = PhotoRecord(
            photo_id=real_pid,
            original_path=str(photos_dir / p_file),
            file_name=p_file,
            width=200,
            height=200,
            faces=[face_obj],
        )
        cache.save(rec)

    config = EngineConfig(
        input_path=photos_dir,
        output_dir=out_dir,
        cache_dir=work_dir,
        distance_threshold=0.50,
    )

    result = run_pipeline(config)
    assert len(result.people) == 2

    # Verify public bundle has exactly the 4 required entries
    allowed_public = {"config.json", "people.json", "faces", "thumbs"}
    actual_public = {p.name for p in out_dir.iterdir()}
    assert actual_public == allowed_public

    # Verify people.json contains merged_from and merged_from_numbering
    with open(out_dir / "people.json", "r", encoding="utf-8") as f:
        people_data = json.load(f)
    for p in people_data["people"]:
        assert "merged_from" in p
        assert isinstance(p["merged_from"], list)
        assert len(p["merged_from"]) >= 1
        assert "merged_from_numbering" in p
        assert p["merged_from_numbering"].startswith("pre-merge")

    # Verify work directory contains id_map.json and suggestions.json
    assert (work_dir / "id_map.json").is_file()
    assert (work_dir / "suggestions.json").is_file()

    with open(work_dir / "id_map.json", "r", encoding="utf-8") as f:
        id_map_data = json.load(f)
    assert "_metadata" in id_map_data
    assert "p001" in id_map_data
