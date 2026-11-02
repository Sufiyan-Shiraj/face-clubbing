"""Tests for multi-source mixed export and viewer bundling (Phase V2-5).

Verifies:
- Mixed local + Google Drive photo bundle exports with per-photo download link semantics.
- Album label extraction from folder_path, relative_path, and source_label.
- Public bundle hygiene (zero organizer files, zero full-size copies for cloud photos).
- Standalone HTML gallery embedding album filtering controls and metadata.
"""

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
from backend.engine.scanner import PhotoScanner


def _create_dummy_image(path: Path, width: int = 200, height: int = 200):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(path, format="JPEG")


def test_multi_source_mixed_export(tmp_path: Path):
    src_dir = tmp_path / "src"
    export_dir = tmp_path / "export"
    cache_dir = tmp_path / "cache"
    (cache_dir / "thumbs").mkdir(parents=True, exist_ok=True)
    (cache_dir / "crops").mkdir(parents=True, exist_ok=True)

    img_local = src_dir / "Day1" / "local01.jpg"
    _create_dummy_image(img_local)

    # Put cached thumb and crop
    _create_dummy_image(cache_dir / "thumbs" / "p_local01.jpg", 100, 100)
    _create_dummy_image(cache_dir / "thumbs" / "p_drive02.jpg", 100, 100)
    _create_dummy_image(cache_dir / "crops" / "f_loc01.jpg", 80, 80)
    _create_dummy_image(cache_dir / "crops" / "f_drv02.jpg", 80, 80)

    f_local = FaceDetection(
        face_id="f_loc01",
        photo_id="p_local01",
        bbox=[20.0, 20.0, 80.0, 80.0],
        det_score=0.95,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=True,
    )
    f_drive = FaceDetection(
        face_id="f_drv02",
        photo_id="p_drive02",
        bbox=[30.0, 30.0, 90.0, 90.0],
        det_score=0.96,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=True,
    )

    rec_local = PhotoRecord(
        photo_id="p_local01",
        original_path=str(img_local),
        file_name="local01.jpg",
        relative_path="Day1/local01.jpg",
        folder_path="Day1",
        album="Day1",
        source_id="src_sdcard",
        source_label="Camera SD",
        width=2000,
        height=1500,
        faces=[f_local],
    )

    rec_drive = PhotoRecord(
        photo_id="p_drive02",
        original_path="/tmp/nonexistent_drive_temp.jpg",
        file_name="drive02.jpg",
        folder_path="Reception",
        album="Reception",
        source_id="src_drive",
        source_label="Drive Cloud",
        width=1920,
        height=1080,
        drive_file_id="1DriveMultiSourceFileId999",
        faces=[f_drive],
    )

    person = PersonCluster(
        id="c_vip_01",
        label="VIP Guest",
        face_path="faces/c_vip_01.jpg",
        photo_ids=["p_local01", "p_drive02"],
        faces=[f_local, f_drive],
    )

    engine_res = EngineResult(
        photos={"p_local01": rec_local, "p_drive02": rec_drive},
        people=[person],
        unrecognized=UnrecognizedGroup(photo_ids=[], faces=[]),
        distance_threshold=0.50,
        id_map={},
    )

    exporter = BundleExporter(output_dir=export_dir, cache_dir=cache_dir)
    exporter.export(result=engine_res, title="Mixed Multi-Source Event", generate_html=True)

    # 1. Verify people.json
    with open(export_dir / "people.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    photos = data["photos"]
    p_loc = photos["p_local01"]
    p_drv = photos["p_drive02"]

    # Local photo download is null, Drive photo has direct download URL
    assert p_loc["download"] is None
    assert p_drv["download"] == "https://drive.google.com/uc?id=1DriveMultiSourceFileId999&export=download"
    assert p_drv["drive_url"] == "https://drive.google.com/file/d/1DriveMultiSourceFileId999/view"

    # Albums and sources preserved
    assert p_loc["album"] == "Day1"
    assert p_loc["source_label"] == "Camera SD"
    assert p_drv["album"] == "Reception"
    assert p_drv["source_label"] == "Drive Cloud"

    # 2. Public bundle hygiene
    forbidden = {"edits.json", "suggestions.json", "id_map.json", ".state.json", ".cache"}
    for child in export_dir.rglob("*"):
        assert child.name not in forbidden

    # 3. Full-size photo check: Drive photo should NOT have a local full-size image in export
    for img_file in export_dir.rglob("*.jpg"):
        rel_parts = img_file.relative_to(export_dir).parts
        assert rel_parts[0] in ("thumbs", "faces")

    # 4. Standalone gallery.html check
    gallery_html = (export_dir / "gallery.html").read_text(encoding="utf-8")
    assert "album-select" in gallery_html
    assert "selectedAlbum" in gallery_html


def test_scanner_extracts_folder_path_and_album(tmp_path: Path):
    root_dir = tmp_path / "photos"
    p1 = root_dir / "SubA" / "img1.jpg"
    p2 = root_dir / "SubB" / "Deep" / "img2.jpg"
    p3 = root_dir / "img3.jpg"

    _create_dummy_image(p1)
    _create_dummy_image(p2)
    _create_dummy_image(p3)

    with PhotoScanner(root_dir) as scanner:
        scanned = scanner.scan()
    by_name = {s.file_name: s for s in scanned}

    assert by_name["img1.jpg"].folder_path == "SubA"
    assert by_name["img1.jpg"].album == "SubA"

    assert by_name["img2.jpg"].folder_path == "SubB/Deep"
    assert by_name["img2.jpg"].album == "SubB/Deep"

    assert by_name["img3.jpg"].folder_path is None
    assert by_name["img3.jpg"].album is None


def test_per_photo_download_link_semantics(tmp_path: Path):
    export_dir = tmp_path / "export_semantics"
    cache_dir = tmp_path / "cache_semantics"
    (cache_dir / "thumbs").mkdir(parents=True, exist_ok=True)
    (cache_dir / "crops").mkdir(parents=True, exist_ok=True)

    _create_dummy_image(cache_dir / "thumbs" / "p_explicit.jpg", 100, 100)
    _create_dummy_image(cache_dir / "crops" / "f_exp.jpg", 80, 80)

    f_exp = FaceDetection(
        face_id="f_exp",
        photo_id="p_explicit",
        bbox=[10.0, 10.0, 50.0, 50.0],
        det_score=0.90,
        embedding=np.zeros(512, dtype=np.float32),
        is_good_quality=True,
    )

    rec_custom_dl = PhotoRecord(
        photo_id="p_explicit",
        original_path="/tmp/test.jpg",
        file_name="explicit.jpg",
        width=1920,
        height=1080,
        download_url="https://custom-storage.example.com/photos/explicit.jpg",
        source_label="CDN",
        faces=[f_exp],
    )

    res = EngineResult(
        photos={"p_explicit": rec_custom_dl},
        people=[PersonCluster(id="c_exp", label="Exp", face_path="faces/c_exp.jpg", photo_ids=["p_explicit"], faces=[f_exp])],
        unrecognized=UnrecognizedGroup(photo_ids=[], faces=[]),
        distance_threshold=0.50,
        id_map={},
    )

    exporter = BundleExporter(output_dir=export_dir, cache_dir=cache_dir)
    exporter.export(result=res, title="Semantics Test")

    with open(export_dir / "people.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    p_info = data["photos"]["p_explicit"]
    assert p_info["download"] == "https://custom-storage.example.com/photos/explicit.jpg"
    assert p_info["source_label"] == "CDN"
