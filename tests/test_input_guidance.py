"""Unit tests for Phase V2-7: Input Guidance, Cloud Link Detection, Nested Archives, and Unsupported File Reporting."""

from pathlib import Path
import zipfile
import pytest

from backend.drive.parser import detect_unsupported_cloud_link, parse_drive_folder_id
from backend.api.diagnostics import classify_error
from backend.engine.scanner import PhotoScanner, SUPPORTED_EXTENSIONS
from backend.engine.models import EngineResult
from backend.engine.exporter import BundleExporter


def test_detect_unsupported_cloud_link_google_photos():
    """Detect Google Photos share and album links."""
    share_url = "https://photos.google.com/share/AF1QipNxyz123abc?key=SecretKey99"
    detected = detect_unsupported_cloud_link(share_url)
    assert detected is not None
    assert detected["service"] == "Google Photos"
    assert detected["code"] == "GOOGLE_PHOTOS_LINK"
    assert "March 2025" in detected["message"] or "Google Photos" in detected["message"]
    assert "ZIP" in detected["how_to_fix"] or "Google Drive" in detected["how_to_fix"]

    short_url = "https://photos.app.goo.gl/9xYzAbCdEf123"
    detected_short = detect_unsupported_cloud_link(short_url)
    assert detected_short is not None
    assert detected_short["service"] == "Google Photos"
    assert detected_short["code"] == "GOOGLE_PHOTOS_LINK"


def test_detect_unsupported_cloud_links_other_providers():
    """Detect Dropbox, OneDrive, SharePoint, iCloud, and Box links."""
    dropbox_url = "https://www.dropbox.com/scl/fo/abc123xyz/h?rlkey=secret"
    d = detect_unsupported_cloud_link(dropbox_url)
    assert d is not None
    assert d["code"] == "DROPBOX_LINK"

    onedrive_url = "https://onedrive.live.com/?id=root&cid=12345"
    d_od = detect_unsupported_cloud_link(onedrive_url)
    assert d_od is not None
    assert d_od["code"] == "ONEDRIVE_LINK"

    sharepoint_url = "https://mycorp.sharepoint.com/:f:/s/team/abc123xyz"
    d_sp = detect_unsupported_cloud_link(sharepoint_url)
    assert d_sp is not None
    assert d_sp["code"] == "ONEDRIVE_LINK"

    onedrive_short = "https://1drv.ms/f/s!Ap345"
    d_short = detect_unsupported_cloud_link(onedrive_short)
    assert d_short is not None
    assert d_short["code"] == "ONEDRIVE_LINK"

    icloud_url = "https://www.icloud.com/sharedalbum/#B0xyz123"
    d_ic = detect_unsupported_cloud_link(icloud_url)
    assert d_ic is not None
    assert d_ic["code"] == "ICLOUD_LINK"

    box_url = "https://app.box.com/s/folderhash123"
    d_bx = detect_unsupported_cloud_link(box_url)
    assert d_bx is not None
    assert d_bx["code"] == "BOX_LINK"


def test_detect_unsupported_cloud_link_allows_valid_drive():
    """Google Drive URLs and folder IDs return None (not unsupported)."""
    assert detect_unsupported_cloud_link("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up08") is None
    assert detect_unsupported_cloud_link(
        "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up08"
    ) is None
    assert detect_unsupported_cloud_link("C:\\Photos\\Event") is None
    assert detect_unsupported_cloud_link("") is None


def test_parse_drive_folder_id_rejects_unsupported_cloud_links():
    """parse_drive_folder_id raises descriptive ValueError when given Google Photos or Dropbox."""
    with pytest.raises(ValueError) as exc:
        parse_drive_folder_id("https://photos.app.goo.gl/testAlbum")
    assert "Google Photos" in str(exc.value)
    assert "ZIP" in str(exc.value) or "Google Drive" in str(exc.value)

    with pytest.raises(ValueError) as exc_db:
        parse_drive_folder_id("https://www.dropbox.com/scl/fo/abc/h")
    assert "Dropbox" in str(exc_db.value)


def test_diagnostics_classifies_cloud_links():
    """classify_error identifies GOOGLE_PHOTOS_LINK and other providers."""
    err_photos = ValueError("Google Photos link detected: cannot access directly. Download as ZIP.")
    c_photos = classify_error(err_photos)
    assert c_photos.error_code == "GOOGLE_PHOTOS_LINK"
    assert "Google Photos" in c_photos.title
    assert "Download all" in c_photos.plain_language_fix or "ZIP" in c_photos.plain_language_fix

    err_db = ValueError("Dropbox links cannot be accessed directly via URL.")
    c_db = classify_error(err_db)
    assert c_db.error_code == "DROPBOX_LINK"

    err_od = ValueError("OneDrive / SharePoint links cannot be accessed directly via URL.")
    c_od = classify_error(err_od)
    assert c_od.error_code == "ONEDRIVE_LINK"

    err_ic = ValueError("iCloud links cannot be accessed directly via URL.")
    c_ic = classify_error(err_ic)
    assert c_ic.error_code == "ICLOUD_LINK"


def test_nested_zip_extraction(tmp_path: Path):
    """WhatsApp & phone export simulation: recursive extraction of nested archives up to 3 levels."""
    inner_zip_bytes_path = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner_zip_bytes_path, "w") as inner_zf:
        inner_zf.writestr("inner_folder/photo_nested.png", b"fake-png-content-1")
        inner_zf.writestr("inner_folder/deep.zip", b"dummy")

    outer_zip_path = tmp_path / "whatsapp_export.zip"
    with zipfile.ZipFile(outer_zip_path, "w") as outer_zf:
        outer_zf.writestr("chat.txt", b"chat text")
        outer_zf.writestr("root_photo.jpg", b"fake-jpeg-content-root")
        outer_zf.write(inner_zip_bytes_path, arcname="Media.zip")

    with PhotoScanner(outer_zip_path) as scanner:
        items = scanner.scan()
        file_names = [item.file_name for item in items]
        assert "root_photo.jpg" in file_names
        assert "photo_nested.png" in file_names
        assert len(scanner.extracted_nested_zips) >= 1


def test_scanner_unsupported_file_tracking(tmp_path: Path):
    """Scanner tracks skipped unsupported files by extension while ignoring system metadata."""
    (tmp_path / "valid1.jpg").write_bytes(b"image1")
    (tmp_path / "valid2.webp").write_bytes(b"image2")
    (tmp_path / "clip.mp4").write_bytes(b"video1")
    (tmp_path / "song.mp3").write_bytes(b"audio1")
    (tmp_path / "document.pdf").write_bytes(b"pdf1")
    (tmp_path / "notes.txt").write_bytes(b"text1")
    # System metadata files should be ignored
    (tmp_path / ".DS_Store").write_bytes(b"mac metadata")
    (tmp_path / "Thumbs.db").write_bytes(b"windows cache")
    (tmp_path / "desktop.ini").write_bytes(b"windows icon config")

    with PhotoScanner(tmp_path) as scanner:
        items = scanner.scan()
        assert len(items) == 2
        assert scanner.unsupported_count == 4
        assert scanner.unsupported_files[".mp4"] == 1
        assert scanner.unsupported_files[".mp3"] == 1
        assert scanner.unsupported_files[".pdf"] == 1
        assert scanner.unsupported_files[".txt"] == 1
        # System metadata must not be reported as unsupported files
        assert ".DS_Store" not in scanner.unsupported_files
        assert ".db" not in scanner.unsupported_files
        assert ".ini" not in scanner.unsupported_files

        summary = scanner.get_unsupported_summary()
        assert summary["total_unsupported"] == 4
        assert summary["extensions"][".mp4"] == 1
        assert summary["extensions"][".pdf"] == 1


def test_single_unsupported_file_raises_clear_error(tmp_path: Path):
    """Passing a single unsupported document/video directly raises ValueError with supported format guide."""
    bad_file = tmp_path / "presentation.pdf"
    bad_file.write_bytes(b"pdf data")

    with pytest.raises(ValueError) as exc:
        with PhotoScanner(bad_file) as scanner:
            scanner.scan()
    assert "unsupported format ('.pdf')" in str(exc.value)
    assert ".jpg" in str(exc.value)
    assert ".png" in str(exc.value)
    assert ".heic" in str(exc.value)


def test_exporter_manifest_includes_unsupported_summary(tmp_path: Path):
    """Manifest schema v2 includes unsupported_files and unsupported_count."""
    from backend.engine.models import UnrecognizedGroup
    result = EngineResult(
        photos={},
        people=[],
        unrecognized=UnrecognizedGroup(),
        distance_threshold=0.5,
        unsupported_files={".mp4": 3, ".mov": 2},
        unsupported_count=5,
    )
    exporter = BundleExporter(output_dir=tmp_path)
    exporter.export(result)

    manifest_file = tmp_path / "manifest.json"
    assert manifest_file.exists()
    import json
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["unsupported_count"] == 5
    assert data["unsupported_files"] == {".mp4": 3, ".mov": 2}
