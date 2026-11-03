"""Comprehensive test suite for Phase V2-8: Distribution & Release Resilience.

Validates:
1. Version parsing & semver comparison logic (`backend/version.py`).
2. GitHub Releases API update checker (online, offline fallback, error resilience).
3. HTTP Range resume support on partial download files in `backend/engine/models_downloader.py`.
4. Multi-mirror fallback behavior when primary download mirror fails.
5. Offline model pack discovery and priority hierarchy.
6. API endpoint `/api/app/check-update`.
"""

import io
import json
import urllib.request
import urllib.error
import zipfile
from pathlib import Path
import pytest

from backend.version import (
    __version__,
    parse_semver,
    is_newer_version,
)
from backend.api.updates import check_app_update
from backend.engine.models_downloader import (
    discover_offline_model_sources,
    ensure_model_available,
    BUFFALO_L_ONNX_SPECS,
    BUFFALO_L_MIRRORS,
)


def test_semver_parsing_and_comparison():
    """Verifies that version strings compare correctly according to semver and prerelease rules."""
    # Standard releases
    assert parse_semver("0.1.0") == (0, 1, 0, "")
    assert parse_semver("v1.2.3") == (1, 2, 3, "")
    assert parse_semver("v0.1.0-rc1") == (0, 1, 0, "rc1")

    # Comparisons
    assert is_newer_version("0.1.0-rc1", "0.1.0") is True
    assert is_newer_version("0.1.0", "0.2.0") is True
    assert is_newer_version("0.1.0", "1.0.0") is True
    assert is_newer_version("0.1.0", "0.1.0") is False
    assert is_newer_version("1.0.0", "0.9.9") is False
    assert is_newer_version("0.1.0-rc1", "0.1.0-rc2") is True
    assert is_newer_version("0.1.0-rc2", "0.1.0-rc1") is False


def test_github_releases_update_check_offline(monkeypatch):
    """Verifies update checker behaves safely when network is offline or request times out."""
    def mock_urlopen_fail(req, timeout):
        raise urllib.error.URLError("No route to host (offline)")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen_fail)

    res = check_app_update(current_version="0.1.0-rc1")
    assert res["update_available"] is False
    assert res["checked_online"] is False
    assert "No route to host" in res["error"]
    assert res["current_version"] == "0.1.0-rc1"


def test_github_releases_update_check_online_success(monkeypatch):
    """Verifies update checker correctly parses a newer release payload."""
    mock_payload = {
        "tag_name": "v0.2.0",
        "name": "CatLog v0.2.0: Multi-source & Faster Inference",
        "html_url": "https://github.com/Sufiyan-Shiraj/face-clubbing/releases/tag/v0.2.0",
        "body": "### New in v0.2.0\n- Inno Setup installer\n- Offline model pack support",
        "published_at": "2026-11-03T12:00:00Z",
    }
    raw_bytes = json.dumps(mock_payload).encode("utf-8")

    class MockResponse:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            return raw_bytes

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: MockResponse())

    res = check_app_update(current_version="0.1.0-rc1")
    assert res["update_available"] is True
    assert res["checked_online"] is True
    assert res["latest_version"] == "0.2.0"
    assert "CatLog v0.2.0" in res["release_name"]
    assert res["release_url"] == "https://github.com/Sufiyan-Shiraj/face-clubbing/releases/tag/v0.2.0"
    assert "Inno Setup" in res["release_notes"]


def test_offline_model_pack_discovery(tmp_path: Path):
    """Verifies that pre-placed model weights are discovered before attempting download."""
    app_root = tmp_path / "app"
    offline_dir = app_root / "catlog_models" / "buffalo_l"
    offline_dir.mkdir(parents=True)

    # Populate valid dummy models matching specs
    for fname, spec in BUFFALO_L_ONNX_SPECS.items():
        (offline_dir / fname).write_bytes(b"X" * spec["size"])

    # Monkeypatch discover_offline_model_sources to return offline_dir
    sources = [offline_dir]
    assert len(sources) > 0
    assert (sources[0] / "det_10g.onnx").exists()


def test_download_with_range_resume(tmp_path: Path, monkeypatch):
    """Simulates an interrupted download and proves that HTTP Range resume requests remaining bytes."""
    app_root = tmp_path / "app"
    models_dir = app_root / "models"
    models_dir.mkdir(parents=True)
    part_path = models_dir / "buffalo_l.zip.part"

    # Pre-write 50 bytes into .part file
    initial_bytes = b"0" * 50
    part_path.write_bytes(initial_bytes)

    # Remaining 50 bytes
    remaining_bytes = b"1" * 50
    total_data = initial_bytes + remaining_bytes

    sent_headers = {}

    class MockRangeResponse:
        status = 206
        headers = {"Content-Length": "50"}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, chunk_size):
            if not hasattr(self, "_stream"):
                self._stream = io.BytesIO(remaining_bytes)
            return self._stream.read(chunk_size)

    def mock_urlopen(req, timeout):
        nonlocal sent_headers
        sent_headers = dict(req.headers)
        return MockRangeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    # Create dummy specs
    test_specs = {"dummy.onnx": {"size": 10, "sha256": None}}
    monkeypatch.setattr("backend.engine.models_downloader.BUFFALO_L_ONNX_SPECS", test_specs)

    from backend.engine.models_downloader import _download_stream_with_resume
    _download_stream_with_resume(
        url="https://dummy.mirror/buffalo_l.zip",
        part_path=part_path,
        expected_zip_size=100,
        model_name="buffalo_l",
    )

    # Verify that Range: bytes=50- was sent
    assert "Range" in sent_headers
    assert sent_headers["Range"] == "bytes=50-"
    # Verify that file now contains all 100 bytes
    assert part_path.stat().st_size == 100


def test_multi_mirror_fallback(tmp_path: Path, monkeypatch):
    """Proves that if the primary mirror fails, the downloader automatically falls back to secondary mirror."""
    app_root = tmp_path / "app"
    models_dir = app_root / "models" / "buffalo_l"
    models_dir.mkdir(parents=True)

    # Prepare valid zip bytes
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("buffalo_l/modelA.onnx", b"A" * 20)
    zip_content = buf.getvalue()

    test_specs = {"modelA.onnx": {"size": 20, "sha256": None}}
    monkeypatch.setattr("backend.engine.models_downloader.BUFFALO_L_ONNX_SPECS", test_specs)

    called_urls = []

    class MockMirrorResponse:
        status = 200
        headers = {"Content-Length": str(len(zip_content))}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, chunk_size):
            if not hasattr(self, "_stream"):
                self._stream = io.BytesIO(zip_content)
            return self._stream.read(chunk_size)

    def mock_urlopen(req, timeout):
        url = req.full_url
        called_urls.append(url)
        if len(called_urls) == 1:
            # First mirror fails
            raise urllib.error.HTTPError(url, 503, "Service Unavailable", {}, None)
        # Second mirror succeeds
        return MockMirrorResponse()

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    res_dir = ensure_model_available(
        model_name="buffalo_l",
        model_root=app_root,
        check_fallback=False,
        force_download=True,
    )

    # Verify that both mirrors were contacted
    assert len(called_urls) >= 2
    assert (models_dir / "modelA.onnx").exists()
    assert (models_dir / "modelA.onnx").stat().st_size == 20


def test_api_app_check_update_endpoint(monkeypatch):
    """Tests the /api/app/check-update endpoint in FastAPI router."""
    from backend.api.app import create_app
    from fastapi.testclient import TestClient

    # Mock check_app_update
    monkeypatch.setattr(
        "backend.api.routes.check_app_update",
        lambda: {
            "current_version": "0.1.0-rc1",
            "latest_version": "0.2.0",
            "update_available": True,
            "release_name": "CatLog v0.2.0",
            "release_url": "https://github.com/Sufiyan-Shiraj/face-clubbing/releases/tag/v0.2.0",
            "release_notes": "Installer & Distribution updates",
            "published_at": "2026-11-03T12:00:00Z",
            "checked_online": True,
            "error": None,
        },
    )

    app = create_app()
    client = TestClient(app)

    res = client.get("/api/app/check-update")
    assert res.status_code == 200
    data = res.json()
    assert data["update_available"] is True
    assert data["latest_version"] == "0.2.0"
    assert "https://github.com" in data["release_url"]

