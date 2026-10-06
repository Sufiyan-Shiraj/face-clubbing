"""Unit tests for the scanner module."""

from pathlib import Path
import zipfile
import pytest

from backend.engine.scanner import PhotoScanner, compute_file_hash, SUPPORTED_EXTENSIONS


def test_supported_extensions():
    assert ".jpg" in SUPPORTED_EXTENSIONS
    assert ".jpeg" in SUPPORTED_EXTENSIONS
    assert ".png" in SUPPORTED_EXTENSIONS
    assert ".webp" in SUPPORTED_EXTENSIONS
    assert ".heic" in SUPPORTED_EXTENSIONS
    assert ".pdf" not in SUPPORTED_EXTENSIONS
    assert ".txt" not in SUPPORTED_EXTENSIONS


def test_compute_file_hash_stability(tmp_path: Path):
    f1 = tmp_path / "test1.jpg"
    f2 = tmp_path / "test2.jpg"
    content = b"fake-image-bytes-12345"
    f1.write_bytes(content)
    f2.write_bytes(content)

    h1 = compute_file_hash(f1)
    h2 = compute_file_hash(f2)
    assert h1 == h2
    assert len(h1) == 16


def test_scan_folder(tmp_path: Path):
    (tmp_path / "img1.jpg").write_bytes(b"content1")
    (tmp_path / "img2.PNG").write_bytes(b"content2")
    (tmp_path / "notes.txt").write_bytes(b"ignore me")

    sub = tmp_path / "subfolder"
    sub.mkdir()
    (sub / "img3.jpeg").write_bytes(b"content3")

    with PhotoScanner(tmp_path) as scanner:
        items = scanner.scan()
        assert len(items) == 3
        filenames = [item.file_name for item in items]
        assert "img1.jpg" in filenames
        assert "img2.PNG" in filenames
        assert "img3.jpeg" in filenames
        assert "notes.txt" not in filenames


def test_scan_zip(tmp_path: Path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("event/photo_a.jpg", b"image-a")
        zf.writestr("event/photo_b.png", b"image-b")
        zf.writestr("event/readme.txt", b"text")

    with PhotoScanner(zip_path) as scanner:
        items = scanner.scan()
        assert len(items) == 2
        filenames = [item.file_name for item in items]
        assert "photo_a.jpg" in filenames
        assert "photo_b.png" in filenames


def test_scan_single_file(tmp_path: Path):
    img = tmp_path / "single.jpg"
    img.write_bytes(b"single-image-content")

    with PhotoScanner(img) as scanner:
        items = scanner.scan()
        assert len(items) == 1
        assert items[0].file_name == "single.jpg"
        assert items[0].photo_id == compute_file_hash(img)
