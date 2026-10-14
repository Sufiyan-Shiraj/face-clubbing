"""Mocked HTTP tests for Google Drive integration (BUILD_PLAN Phase 6).

Covers all Phase 6 specifications with strictly mocked HTTP (no network, CI-safe):
1. Parse Drive folder URL or ID (all common URL forms, unit tests including invalid inputs and file link rejection).
2. List files with an API key (paginated, images only), skipping folders and non-images, reporting counts.
3. Download size-limited thumbnails (thumbnailLink resized =s1000), fallback to original (alt=media)
   when no thumbnail, retry with backoff on 403/429/5xx, resumable on re-run (skip files already
   cached by file ID + modifiedTime), clear domain errors for private folder, bad key, quota exceeded.
4. Pipeline integration: record Drive file ID per photo, verify exporter public bundle fills `download`
   with https://drive.google.com/uc?id=<ID>&export=download.
5. API key masking in UI/logs/config, storage outside repository in ~/.photosorter/settings.json,
   and DRIVE_API_KEY environment variable fallback.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from backend.drive.client import (
    DriveClient,
    DriveFile,
    DriveAuthError,
    DrivePermissionError,
    DriveQuotaError,
)
from backend.drive.config import (
    get_drive_api_key,
    set_drive_api_key,
    mask_api_key,
    get_masked_drive_api_key,
    sanitize_drive_logs,
)
from backend.drive.parser import (
    parse_drive_folder_id,
    is_drive_folder_input,
)
from backend.engine.models import PhotoRecord
from backend.engine.pipeline import EngineConfig, run_pipeline


# ---------------------------------------------------------------------------
# 1. URL and ID Parsing
# ---------------------------------------------------------------------------

class TestDriveUrlParser:
    """Test parse_drive_folder_id across all standard and mobile Google Drive URL formats."""

    VALID_CASES = [
        # Standard web link
        ("https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        # Link with query parameters (sharing, usp, etc.)
        ("https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs?usp=sharing", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        # Multi-user account URL (/u/0/, /u/1/)
        ("https://drive.google.com/drive/u/0/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        ("https://drive.google.com/drive/u/2/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs?usp=drive_link", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        # Mobile app link
        ("https://drive.google.com/drive/mobile/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        # Legacy open?id= format
        ("https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        # Legacy folderview?id= format
        ("https://drive.google.com/folderview?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs&usp=sharing", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        # Raw alphanumeric folder ID
        ("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"),
        ("0B_1234567890abcdefghijklmnopqrstuv", "0B_1234567890abcdefghijklmnopqrstuv"),
    ]

    @pytest.mark.parametrize("url_or_id,expected_id", VALID_CASES)
    def test_parse_valid_urls_and_ids(self, url_or_id: str, expected_id: str):
        assert parse_drive_folder_id(url_or_id) == expected_id
        assert is_drive_folder_input(url_or_id) is True

    def test_reject_drive_file_url(self):
        file_url = "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs/view?usp=sharing"
        with pytest.raises(ValueError, match="file link.*folder"):
            parse_drive_folder_id(file_url)
        assert is_drive_folder_input(file_url) is False

    @pytest.mark.parametrize("invalid_input", [
        "",
        "   ",
        "https://example.com/not/drive",
        "short_id",
        "https://drive.google.com/drive/my-drive",
        "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs/edit",
        "123!@#invalid_symbols$$$",
    ])
    def test_reject_invalid_inputs(self, invalid_input: str):
        with pytest.raises(ValueError):
            parse_drive_folder_id(invalid_input)
        assert is_drive_folder_input(invalid_input) is False


# ---------------------------------------------------------------------------
# 2. Key Masking and Config Storage
# ---------------------------------------------------------------------------

class TestDriveConfig:
    def test_mask_api_key(self):
        assert mask_api_key("AIzaSyA1B2C3D4E5F6G7H8") == "AIzaSy...G7H8"
        assert mask_api_key("") == ""
        assert mask_api_key("short") == "***"

    def test_env_var_precedence(self, monkeypatch):
        monkeypatch.setenv("DRIVE_API_KEY", "AIzaSyEnvVarKey1234567890")
        assert get_drive_api_key() == "AIzaSyEnvVarKey1234567890"
        assert get_masked_drive_api_key() == "AIzaSy...7890"

    def test_local_settings_file_storage(self, monkeypatch, tmp_path):
        monkeypatch.delenv("DRIVE_API_KEY", raising=False)
        fake_profile = tmp_path / "fake_profile"
        monkeypatch.setenv("USERPROFILE", str(fake_profile))
        monkeypatch.setenv("HOME", str(fake_profile))

        # Initially unset
        assert get_drive_api_key() is None

        # Set key
        set_drive_api_key("AIzaSySettingsFileKey987654321")
        assert get_drive_api_key() == "AIzaSySettingsFileKey987654321"

        # Check file was written outside repo in ~/.photosorter/settings.json
        settings_file = fake_profile / ".photosorter" / "settings.json"
        assert settings_file.exists()
        with open(settings_file, "r") as f:
            data = json.load(f)
        assert data.get("drive_api_key") == "AIzaSySettingsFileKey987654321"

        # Clear key
        set_drive_api_key("")
        assert get_drive_api_key() is None

    def test_sanitize_logs(self, monkeypatch):
        monkeypatch.setenv("DRIVE_API_KEY", "AIzaSySecretKey999")
        log_line = "Calling https://www.googleapis.com/drive/v3/files?key=AIzaSySecretKey999&pageSize=100"
        sanitized = sanitize_drive_logs(log_line)
        assert "AIzaSySecretKey999" not in sanitized
        assert "AIzaSy...y999" in sanitized


# ---------------------------------------------------------------------------
# 3. File Listing with Mocked HTTP (Pagination, Image Filter, Skipping)
# ---------------------------------------------------------------------------

class TestDriveClientListing:
    @patch.object(requests.Session, "get")
    def test_paginated_listing_and_filtering(self, mock_get):
        """Verify pagination across 2 pages, skipping folders, non-images, and reporting counts."""
        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "nextPageToken": "token_page_2",
            "files": [
                {
                    "id": "file_img_1",
                    "name": "photo_01.jpg",
                    "mimeType": "image/jpeg",
                    "modifiedTime": "2026-10-14T01:00:00Z",
                    "size": "2048000",
                    "thumbnailLink": "https://lh3.googleusercontent.com/drive-viewer/photo1=s220",
                },
                {
                    "id": "folder_sub_1",
                    "name": "Subfolder",
                    "mimeType": "application/vnd.google-apps.folder",
                    "modifiedTime": "2026-10-14T01:00:00Z",
                },
                {
                    "id": "file_doc_1",
                    "name": "notes.pdf",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-10-14T01:00:00Z",
                },
            ],
        }

        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.json.return_value = {
            "files": [
                {
                    "id": "file_img_2",
                    "name": "photo_02.png",
                    "mimeType": "image/png",
                    "modifiedTime": "2026-10-14T01:05:00Z",
                    "size": "1500000",
                    "thumbnailLink": "https://lh3.googleusercontent.com/drive-viewer/photo2=s220",
                },
                {
                    "id": "file_video_1",
                    "name": "clip.mp4",
                    "mimeType": "video/mp4",
                    "modifiedTime": "2026-10-14T01:10:00Z",
                },
            ],
        }

        mock_get.side_effect = [page1_response, page2_response]

        client = DriveClient(api_key="AIzaSyMockKeyForListing123")
        res = client.list_folder_images("test_folder_id")

        # 2 pages called
        assert mock_get.call_count == 2

        # 2 images retained, subfolder and pdf and mp4 skipped
        assert len(res.files) == 2
        assert res.files[0].id == "file_img_1"
        assert res.files[1].id == "file_img_2"

        # Verification of counts
        assert res.total_files_in_folder == 5
        assert res.image_count == 2
        assert res.skipped_folders_count == 1
        assert res.skipped_non_images_count == 2


# ---------------------------------------------------------------------------
# 4. Error Handling (Auth, Permission, Quota)
# ---------------------------------------------------------------------------

class TestDriveClientErrorHandling:
    @patch.object(requests.Session, "get")
    def test_bad_api_key_raises_auth_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 400
        resp.json.return_value = {
            "error": {
                "message": "API key not valid. Please pass a valid API key.",
                "status": "INVALID_ARGUMENT",
                "details": [{"reason": "API_KEY_INVALID"}],
            }
        }
        mock_get.return_value = resp

        client = DriveClient(api_key="AIzaSyInvalidKey")
        with pytest.raises(DriveAuthError, match="Invalid Google Drive API key"):
            client.list_folder_images("any_folder")

    @patch.object(requests.Session, "get")
    def test_private_folder_raises_permission_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 404
        resp.json.return_value = {
            "error": {
                "message": "File not found: private_folder_id",
                "status": "NOT_FOUND",
            }
        }
        mock_get.return_value = resp

        client = DriveClient(api_key="AIzaSyValidKey")
        with pytest.raises(DrivePermissionError, match="Google Drive folder was not found"):
            client.list_folder_images("private_folder_id")

    @patch.object(requests.Session, "get")
    def test_quota_exceeded_raises_quota_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 403
        resp.json.return_value = {
            "error": {
                "message": "Daily Limit Exceeded. The sub-quota 'Queries' exceeded.",
                "errors": [{"reason": "dailyLimitExceeded"}],
            }
        }
        mock_get.return_value = resp

        client = DriveClient(api_key="AIzaSyValidKey")
        with pytest.raises(DriveQuotaError, match="Google Drive API quota exceeded"):
            client.list_folder_images("test_folder")


# ---------------------------------------------------------------------------
# 5. Thumbnail Download, Fallback, Retry, and Resumable Cache
# ---------------------------------------------------------------------------

class TestDriveDownloadAndCache:
    @patch.object(requests.Session, "get")
    def test_thumbnail_s1000_resize_and_alt_media_fallback(self, mock_get, tmp_path):
        """Verify:
        1. thumbnailLink is rewritten to =s1000
        2. when thumbnailLink is missing, falls back to alt=media
        """
        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 300 + b"\xff\xd9"

        resp1 = MagicMock()
        resp1.status_code = 200
        resp1.content = fake_jpeg

        resp2 = MagicMock()
        resp2.status_code = 200
        resp2.content = fake_jpeg

        mock_get.side_effect = [resp1, resp2]

        client = DriveClient(api_key="AIzaSyTestKey")
        files = [
            DriveFile(
                id="file_thumb_yes",
                name="has_thumb.jpg",
                mime_type="image/jpeg",
                modified_time="2026-10-14T02:00:00Z",
                thumbnail_link="https://lh3.googleusercontent.com/drive-viewer/abc=s220",
            ),
            DriveFile(
                id="file_thumb_no",
                name="no_thumb.jpg",
                mime_type="image/jpeg",
                modified_time="2026-10-14T02:00:00Z",
                thumbnail_link=None,  # triggers fallback
            ),
        ]

        dest_dir = tmp_path / "cache_thumbs"
        downloaded = client.download_thumbnails(files, dest_dir=dest_dir, max_workers=1)

        assert len(downloaded) == 2

        # First call should request resized thumbnail =s1000
        first_call_url = mock_get.call_args_list[0][0][0]
        assert "=s1000" in first_call_url

        # Second call should request alt=media
        assert mock_get.call_args_list[1][1]["params"]["alt"] == "media"

    @patch("time.sleep", return_value=None)
    @patch.object(requests.Session, "get")
    def test_retry_with_backoff_on_transient_error(self, mock_get, mock_sleep, tmp_path):
        """Verify retry with backoff on 429 / 503 before successful download."""
        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 300 + b"\xff\xd9"

        # 429 Rate limit, then 503 Service Unavailable, then 200 Success
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.text = "Too many requests"

        resp_503 = MagicMock()
        resp_503.status_code = 503
        resp_503.text = "Service unavailable"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.content = fake_jpeg

        mock_get.side_effect = [resp_429, resp_503, resp_200]

        client = DriveClient(api_key="AIzaSyTestKey")
        files = [
            DriveFile(
                id="file_retry_test",
                name="retry.jpg",
                mime_type="image/jpeg",
                modified_time="2026-10-14T03:00:00Z",
                thumbnail_link="https://lh3.googleusercontent.com/test=s220",
            )
        ]

        downloaded = client.download_thumbnails(files, dest_dir=tmp_path / "retry_cache", max_workers=1)
        assert len(downloaded) == 1
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2

    @patch.object(requests.Session, "get")
    def test_resumable_caching_skips_unchanged_files(self, mock_get, tmp_path):
        """Verify re-running skips already downloaded files if file ID and modifiedTime match."""
        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 300 + b"\xff\xd9"
        resp = MagicMock()
        resp.status_code = 200
        resp.content = fake_jpeg
        mock_get.return_value = resp

        client = DriveClient(api_key="AIzaSyTestKey")
        files = [
            DriveFile(
                id="file_cache_1",
                name="cached_photo.jpg",
                mime_type="image/jpeg",
                modified_time="2026-10-14T01:00:00Z",
                thumbnail_link="https://lh3.googleusercontent.com/cache=s220",
            )
        ]

        cache_dir = tmp_path / "resume_dir"

        # First run: downloads file
        res1 = client.download_thumbnails(files, dest_dir=cache_dir, max_workers=1)
        assert len(res1) == 1
        assert mock_get.call_count == 1

        # Second run: file already exists and modifiedTime is unchanged -> NO HTTP call
        res2 = client.download_thumbnails(files, dest_dir=cache_dir, max_workers=1)
        assert len(res2) == 1
        assert mock_get.call_count == 1  # Unchanged!


# ---------------------------------------------------------------------------
# 6. Pipeline Integration & Exporter Public Bundle Contract
# ---------------------------------------------------------------------------

class TestDrivePipelineIntegration:
    @patch("backend.drive.client.DriveClient.download_thumbnails")
    @patch("backend.drive.client.DriveClient.list_folder_images")
    def test_pipeline_drive_branch_records_id_and_sets_download_url(
        self, mock_list, mock_download, tmp_path
    ):
        """Verify:
        1. run_pipeline parses Drive folder ID and invokes DriveClient.
        2. PhotoRecord has drive_file_id recorded.
        3. Exporter fills download with https://drive.google.com/uc?id=<ID>&export=download.
        """
        # Create a small valid test photo
        from PIL import Image
        img_path = tmp_path / "drive_photo.jpg"
        img = Image.new("RGB", (200, 200), color=(128, 128, 128))
        img.save(img_path)

        mock_drive_file = DriveFile(
            id="drive_file_abc123",
            name="drive_photo.jpg",
            mime_type="image/jpeg",
            modified_time="2026-10-14T05:00:00Z",
            thumbnail_link="https://lh3.googleusercontent.com/p=s220",
        )

        mock_list.return_value = MagicMock(
            files=[mock_drive_file],
            total_files_in_folder=1,
            image_count=1,
            skipped_folders_count=0,
            skipped_non_images_count=0,
        )
        mock_download.return_value = [(mock_drive_file, img_path)]

        export_dir = tmp_path / "export"
        config = EngineConfig(
            input_path="https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
            output_dir=str(export_dir),
            drive_api_key="AIzaSyMockKeyForPipeline",
        )

        # Mock detector so engine does not need heavy ONNX model weights during unit test
        with patch("backend.engine.pipeline.FaceDetector") as mock_detector_cls:
            mock_detector = mock_detector_cls.return_value
            mock_detector.detect_and_embed.return_value = []
            mock_detector.detect_faces.return_value = []

            result = run_pipeline(config)

        # Check that photos were scanned and drive_file_id was assigned
        assert len(result.photos) == 1
        photo_record = next(iter(result.photos.values()))
        assert photo_record.drive_file_id == "drive_file_abc123"
        assert photo_record.download_url == "https://drive.google.com/uc?id=drive_file_abc123&export=download"

        # Check exported public bundle people.json contract
        people_json_path = export_dir / "people.json"
        assert people_json_path.exists()
        with open(people_json_path, "r", encoding="utf-8") as f:
            exported_bundle = json.load(f)

        assert "photos" in exported_bundle
        assert photo_record.photo_id in exported_bundle["photos"]
        assert exported_bundle["photos"][photo_record.photo_id]["download"] == (
            "https://drive.google.com/uc?id=drive_file_abc123&export=download"
        )

