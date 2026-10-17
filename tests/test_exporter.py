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

    # Public bundle definition: config.json, people.json, faces/, thumbs/, optional viewer build (index.html, assets/), and gallery.html
    allowed_public_entries = {"config.json", "people.json", "faces", "thumbs", "index.html", "assets", "gallery.html"}
    organizer_only = {"suggestions.json", "edits.json", "id_map.json", ".cache"}

    # 1. Base exporter produces core bundle
    actual_entries = {p.name for p in export_dir.iterdir()}
    assert actual_entries.issubset(allowed_public_entries), f"Export contains disallowed files: {actual_entries - allowed_public_entries}"
    assert actual_entries == {"config.json", "people.json", "faces", "thumbs"}

    # 2. Add optional viewer build files and standalone gallery.html -> all allowed
    (export_dir / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    (export_dir / "assets").mkdir()
    (export_dir / "gallery.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    updated_entries = {p.name for p in export_dir.iterdir()}
    assert updated_entries == allowed_public_entries

    # 3. Explicitly assert organizer-only files are rejected
    for forbidden in organizer_only:
        assert not (export_dir / forbidden).exists(), f"Forbidden organizer file found in public export: {forbidden}"
        # Negative check: injecting organizer file violates bundle hygiene
        bad_dir = tmp_path / f"bad_export_{forbidden.strip('.')}"
        bad_dir.mkdir()
        if forbidden == ".cache":
            (bad_dir / forbidden).mkdir()
        else:
            (bad_dir / forbidden).write_text("{}", encoding="utf-8")
        bad_entries = {p.name for p in bad_dir.iterdir()}
        assert not bad_entries.issubset(allowed_public_entries)
        assert bool(bad_entries & organizer_only)


def test_export_bundle_zero_unreferenced_files_and_cleans_orphans(tmp_path: Path):
    """Verifies that an export bundle contains zero unreferenced files and cleans orphans."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    img_path = src_dir / "valid_photo.jpg"
    _create_dummy_image(img_path)

    f1 = FaceDetection(
        face_id="f_valid_face_001",
        photo_id="photo_valid",
        bbox=[15.0, 15.0, 60.0, 60.0],
        det_score=0.96,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=True,
    )
    photo1 = PhotoRecord(
        photo_id="photo_valid",
        original_path=str(img_path),
        file_name="valid_photo.jpg",
        width=200,
        height=200,
        faces=[f1],
    )
    person1 = PersonCluster(
        id="c_valid_01",
        face_path="faces/c_valid_01.jpg",
        rep_face=f1,
        photo_ids=["photo_valid"],
        faces=[f1],
        merged_from=["pre_01"],
        merged_from_numbering="pre-merge 1",
    )
    result = EngineResult(
        photos={"photo_valid": photo1},
        people=[person1],
        unrecognized=UnrecognizedGroup(),
        distance_threshold=0.5,
    )

    # Pre-populate export directory with orphaned thumb and face crop
    (export_dir / "thumbs").mkdir(parents=True, exist_ok=True)
    (export_dir / "faces").mkdir(parents=True, exist_ok=True)
    orphan_thumb = export_dir / "thumbs" / "orphan_photo.jpg"
    orphan_face = export_dir / "faces" / "orphan_face.jpg"
    _create_dummy_image(orphan_thumb)
    _create_dummy_image(orphan_face)

    assert orphan_thumb.exists()
    assert orphan_face.exists()

    # Run export
    exporter = BundleExporter(output_dir=export_dir)
    exporter.export(result)

    # 1. Assert orphans were removed
    assert not orphan_thumb.exists(), "Orphaned thumbnail was not cleaned!"
    assert not orphan_face.exists(), "Orphaned face crop was not cleaned!"

    # 2. Assert zero unreferenced files exist
    with open(export_dir / "people.json", "r", encoding="utf-8") as f:
        pj = json.load(f)

    referenced_thumbs = {Path(pdata["thumb"]).name for pdata in pj["photos"].values()}
    actual_thumbs = {f.name for f in (export_dir / "thumbs").glob("*.jpg")}
    assert actual_thumbs == referenced_thumbs, f"Unreferenced thumbnails: {actual_thumbs - referenced_thumbs}"

    referenced_faces = {Path(p["face"]).name for p in pj["people"]}
    for uf in pj["unrecognized"]["faces"]:
        if isinstance(uf, dict) and uf.get("face"):
            referenced_faces.add(Path(uf["face"]).name)
    actual_faces = {f.name for f in (export_dir / "faces").glob("*.jpg")}
    assert actual_faces == referenced_faces, f"Unreferenced faces: {actual_faces - referenced_faces}"


