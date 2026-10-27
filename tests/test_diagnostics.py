"""Unit tests for Diagnostics, Error Classification, and Privacy Guarantees (BUILD_PLAN Phase V2-1)."""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.diagnostics import (
    classify_error,
    sanitize_sensitive_data,
    format_text_diagnostics,
    generate_diagnostics_report,
    DiagnosticsCounts,
    DiagnosticsReport,
)
from backend.api.state import AppState
from backend.api.jobs import JobManager


client = TestClient(app)


def test_sanitize_sensitive_data_removes_keys():
    """Ensure Google API keys are scrubbed."""
    raw = "Failed request with key AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q and extra info"
    sanitized = sanitize_sensitive_data(raw)
    assert "AIzaSy" not in sanitized
    assert "[MASKED_API_KEY]" in sanitized


def test_sanitize_sensitive_data_removes_urls_and_paths():
    """Ensure URLs, Windows paths, Unix paths, and emails are scrubbed."""
    raw_win = r"Error opening C:\Users\Alice\Pictures\Event2026\photo1.jpg"
    sanitized_win = sanitize_sensitive_data(raw_win)
    assert "C:\\Users" not in sanitized_win
    assert "photo1.jpg" not in sanitized_win
    assert "[LOCAL_PATH]" in sanitized_win

    raw_unix = "Cannot write to /home/bob/secret/export/bundle.zip"
    sanitized_unix = sanitize_sensitive_data(raw_unix)
    assert "/home/bob" not in sanitized_unix
    assert "[LOCAL_PATH]" in sanitized_unix

    raw_url = "Failed download from https://drive.google.com/drive/folders/1a2b3c4d5e?usp=sharing"
    sanitized_url = sanitize_sensitive_data(raw_url)
    assert "1a2b3c4d5e" not in sanitized_url
    assert "[MASKED_DRIVE_URL]" in sanitized_url

    raw_email = "Contact admin@example.org for support"
    sanitized_email = sanitize_sensitive_data(raw_email)
    assert "admin@example.org" not in sanitized_email
    assert "[MASKED_EMAIL]" in sanitized_email


def test_classify_error_disk_full():
    """Verify DISK_FULL classification."""
    err = OSError(28, "No space left on device")
    c = classify_error(err)
    assert c.error_code == "DISK_FULL"
    assert "Storage Full" in c.title
    assert "free space" in c.plain_language_fix.lower()


def test_classify_error_quota_403():
    """Verify QUOTA_403 classification."""
    msg = "HTTP 403: Rate Limit Exceeded or Daily Quota Exceeded"
    c = classify_error(msg)
    assert c.error_code == "QUOTA_403"
    assert "Quota" in c.title
    assert "api key" in c.plain_language_fix.lower()


def test_classify_error_private_folder_404():
    """Verify PRIVATE_FOLDER_404 classification."""
    msg = "DrivePermissionError: Google Drive folder is private or not found (404)"
    c = classify_error(msg)
    assert c.error_code == "PRIVATE_FOLDER_404"
    assert "Anyone with the link" in c.plain_language_fix


def test_classify_error_bad_key_400():
    """Verify BAD_KEY_400 classification."""
    msg = "DriveAuthError: API key not valid. Please pass a valid API key."
    c = classify_error(msg)
    assert c.error_code == "BAD_KEY_400"
    assert "Google Cloud Console" in c.plain_language_fix


def test_classify_error_offline():
    """Verify OFFLINE classification."""
    msg = "requests.exceptions.ConnectionError: Failed to establish a new connection: [Errno 11001] getaddrinfo failed"
    c = classify_error(msg)
    assert c.error_code == "OFFLINE"
    assert "internet connection" in c.plain_language_fix.lower()


def test_classify_error_corrupt_input():
    """Verify CORRUPT_INPUT classification."""
    msg = "zipfile.BadZipFile: File is not a zip file or archive is corrupt"
    c = classify_error(msg)
    assert c.error_code == "CORRUPT_INPUT"
    assert "damaged" in c.plain_language_fix.lower()


def test_classify_error_generic():
    """Verify fallback GENERIC_ERROR classification."""
    msg = "ValueError: unexpected token in parser line 12"
    c = classify_error(msg)
    assert c.error_code == "GENERIC_ERROR"
    assert c.title == "Processing Error Encountered"


def test_diagnostics_report_privacy_guarantee():
    """Ensure diagnostics report contains counts only and never sensitive paths or cluster IDs."""
    state = AppState()
    job_mgr = JobManager(state)
    report = generate_diagnostics_report(state, job_mgr, error_override=OSError(28, "C:\\Users\\John\\Documents: No space left on device"))

    assert report.error_code == "DISK_FULL"
    assert report.version is not None
    assert report.settings_hash is not None
    assert len(report.settings_hash) == 16

    # Verify formatted report contains zero file paths, zero photos, zero keys
    formatted = report.formatted_report
    assert "C:\\Users\\John" not in formatted
    assert "AIzaSy" not in formatted
    assert "CatLog Diagnostics Report" in formatted
    assert "Settings Hash:" in formatted
    assert "Counts:" in formatted
    assert "Privacy Notice:" in formatted


def test_api_diagnostics_endpoint():
    """Test GET /api/diagnostics returns 200 with valid DiagnosticsReport schema."""
    resp = client.get("/api/diagnostics")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "os_name" in data
    assert "settings_hash" in data
    assert "counts" in data
    assert "formatted_report" in data
    assert data["counts"]["total_photos"] >= 0
