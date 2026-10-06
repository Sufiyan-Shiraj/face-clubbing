"""Unit tests for the BundleExporter module."""

import json
from pathlib import Path
from PIL import Image
import numpy as np
import pytest

from backend.engine.exporter import BundleExporter
from backend.engine.models import (
    EngineResult,
    FaceDetection,
    PersonCluster,
    PhotoRecord,
    UnrecognizedGroup,
)


def _create_dummy_image(path: Path, width: int = 200, height: int = 200):
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(path, format="JPEG")


def test_bundle_exporter(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    export_dir = tmp_path / "export"

    img1_path = src_dir / "img1.jpg"
    img2_path = src_dir / "img2.jpg"
    _create_dummy_image(img1_path)
    _create_dummy_image(img2_path)

    f1 = FaceDetection(
        face_id="f_pid1_001",
        photo_id="pid1",
        bbox=[20.0, 20.0, 80.0, 80.0],
        det_score=0.92,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=True,
    )
    f2 = FaceDetection(
        face_id="f_pid2_001",
        photo_id="pid2",
        bbox=[30.0, 30.0, 70.0, 70.0],
        det_score=0.45,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=False,
        rejection_reason="unattached_lowscore",
    )

    photo1 = PhotoRecord(
        photo_id="pid1",
        original_path=str(img1_path),
        file_name="img1.jpg",
        width=200,
        height=200,
        faces=[f1],
    )
    photo2 = PhotoRecord(
        photo_id="pid2",
        original_path=str(img2_path),
        file_name="img2.jpg",
        width=200,
        height=200,
        faces=[f2],
    )

    person1 = PersonCluster(
        id="c_01",
        label=None,
        face_path="faces/c_01.jpg",
        rep_face=f1,
        photo_ids=["pid1"],
        faces=[f1],
        merged_from=["pre_01"],
        merged_from_numbering="pre-merge 1",
    )

    unrecognized = UnrecognizedGroup(
        photo_ids=["pid2"],
        faces=[{"photo_id": "pid2", "face": "faces/u001.jpg"}],
    )
    unrecognized._face_items = [
        {"photo_id": "pid2", "face": "faces/u001.jpg", "face_obj": f2}
    ]

    result = EngineResult(
        photos={"pid1": photo1, "pid2": photo2},
        people=[person1],
        unrecognized=unrecognized,
        distance_threshold=0.5,
    )

    exporter = BundleExporter(output_dir=export_dir)
    out_path = exporter.export(
        result=result,
        title="Test Event",
        subtitle="Test Subtitle",
        config_override={"accent": "#10b981"},
    )

    assert out_path == export_dir.resolve()
    assert (export_dir / "people.json").is_file()
    assert (export_dir / "config.json").is_file()
    assert (export_dir / "thumbs" / "pid1.jpg").is_file()
    assert (export_dir / "thumbs" / "pid2.jpg").is_file()
    assert (export_dir / "faces" / "c_01.jpg").is_file()
    assert (export_dir / "faces" / "u001.jpg").is_file()

    with open(export_dir / "people.json", "r", encoding="utf-8") as f:
        people_data = json.load(f)

    assert people_data["version"] == 1
    assert "pid1" in people_data["photos"]
    assert "pid2" in people_data["photos"]
    assert len(people_data["people"]) == 1
    assert people_data["people"][0]["id"] == "c_01"
    assert people_data["people"][0]["photo_ids"] == ["pid1"]
    assert people_data["people"][0]["photos"] == ["pid1"]
    assert people_data["people"][0]["merged_from"] == ["pre_01"]
    assert people_data["people"][0]["merged_from_numbering"] == "pre-merge 1"

    with open(export_dir / "config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["title"] == "Test Event"
    assert cfg["accent"] == "#10b981"
    assert cfg["hide_single_photo_default"] is False


def test_public_bundle_hygiene(tmp_path: Path):
    """Verifies that the export directory contains strictly and only the four public entries."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    export_dir = tmp_path / "export"

    img_path = src_dir / "img1.jpg"
    _create_dummy_image(img_path)

    f1 = FaceDetection(
        face_id="f_pid1_001",
        photo_id="pid1",
        bbox=[10.0, 10.0, 50.0, 50.0],
        det_score=0.95,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=True,
    )
    photo1 = PhotoRecord(
        photo_id="pid1",
        original_path=str(img_path),
        file_name="img1.jpg",
        width=200,
        height=200,
        faces=[f1],
    )
    person1 = PersonCluster(
        id="c_01",
        face_path="faces/c_01.jpg",
        rep_face=f1,
        photo_ids=["pid1"],
        faces=[f1],
        merged_from=["pre_01"],
        merged_from_numbering="pre-merge 1",
    )
    result = EngineResult(
        photos={"pid1": photo1},
        people=[person1],
        unrecognized=UnrecognizedGroup(),
        distance_threshold=0.5,
    )

    exporter = BundleExporter(output_dir=export_dir)
    exporter.export(result)

    allowed_entries = {"config.json", "people.json", "faces", "thumbs"}
    actual_entries = {p.name for p in export_dir.iterdir()}
    assert actual_entries == allowed_entries, f"Export directory contains unexpected files: {actual_entries - allowed_entries}"
    
    # Explicitly assert organizer-only files are NOT present
    for forbidden in [".cache", "suggestions.json", "edits.json", "id_map.json"]:
        assert not (export_dir / forbidden).exists(), f"Forbidden organizer file found in public export: {forbidden}"

