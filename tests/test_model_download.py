"""Tests for model weight downloading, partial file handling, integrity checks, and offline/interruption resilience."""

from pathlib import Path
import hashlib
import io
import shutil
import urllib.request
import zipfile
import pytest

from backend.engine.models_downloader import (
    ensure_model_available,
    verify_model_dir,
    BUFFALO_L_ONNX_SPECS,
)


def _create_mock_model_zip(specs: dict) -> bytes:
    """Creates an in-memory zip file containing files matching the given specs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, info in specs.items():
            # Pad with null bytes or dummy data to match size
            data = b"X" * info["size"]
            zf.writestr(f"buffalo_l/{fname}", data)
    return buf.getvalue()


def test_verify_model_dir_valid_and_corrupt(tmp_path: Path):
    """Verifies that model directory integrity checking catches missing, truncated, or hash-mismatched files."""
    model_dir = tmp_path / "models" / "buffalo_l"
    model_dir.mkdir(parents=True)

    test_specs = {
        "modelA.onnx": {"size": 20, "sha256": hashlib.sha256(b"A" * 20).hexdigest()},
        "modelB.onnx": {"size": 30, "sha256": hashlib.sha256(b"B" * 30).hexdigest()},
    }

    # 1. Missing files
    valid, reason = verify_model_dir(model_dir, specs=test_specs)
    assert not valid
    assert "Missing model file" in reason

    # 2. Write valid files
    (model_dir / "modelA.onnx").write_bytes(b"A" * 20)
    (model_dir / "modelB.onnx").write_bytes(b"B" * 30)
    valid, reason = verify_model_dir(model_dir, specs=test_specs)
    assert valid
    assert reason is None

    # 3. Size mismatch
    (model_dir / "modelA.onnx").write_bytes(b"A" * 15)
    valid, reason = verify_model_dir(model_dir, specs=test_specs)
    assert not valid
    assert "size mismatch" in reason

    # 4. Content / Hash mismatch
    (model_dir / "modelA.onnx").write_bytes(b"Z" * 20)
    valid, reason = verify_model_dir(model_dir, specs=test_specs)
    assert not valid
    assert "SHA-256 mismatch" in reason


def test_simulated_interrupted_download(tmp_path: Path, monkeypatch):
    """Simulates a network drop during download: asserts .part file is removed on failure and no partial model remains."""
    root_dir = tmp_path / "app_root"
    models_dir = root_dir / "models" / "buffalo_l"
    part_file = root_dir / "models" / "buffalo_l.zip.part"

    class FailingResponse:
        headers = {"Content-Length": "1000000"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, chunk_size):
            # Stream one chunk, then fail mid-stream
            raise ConnectionResetError("Connection lost mid-download")

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: FailingResponse())

    with pytest.raises(RuntimeError) as exc_info:
        ensure_model_available(
            model_name="buffalo_l",
            model_root=root_dir,
            download_url="https://dummy.example.com/buffalo_l.zip",
            check_fallback=False,
        )

    assert "download failed" in str(exc_info.value).lower()
    # The .part file must be cleaned up, never left behind on disk
    assert not part_file.exists(), "Partial .part file must be deleted on failure"
    assert not models_dir.exists(), "Target model dir must not exist after failed download"


def test_offline_start_error_message(tmp_path: Path, monkeypatch):
    """Simulates an offline environment without existing model files: asserts informative error with target path."""
    root_dir = tmp_path / "app_root"

    def mock_offline(req, timeout):
        raise urllib.error.URLError("Name or service not known (offline)")

    monkeypatch.setattr(urllib.request, "urlopen", mock_offline)

    with pytest.raises(RuntimeError) as exc_info:
        ensure_model_available(
            model_name="buffalo_l",
            model_root=root_dir,
            download_url="https://dummy.example.com/buffalo_l.zip",
            check_fallback=False,
        )

    msg = str(exc_info.value)
    assert "internet connection" in msg.lower()
    assert str(root_dir / "models" / "buffalo_l") in msg


def test_re_download_on_corrupted_stored_file(tmp_path: Path, monkeypatch):
    """If stored model files fail verification, they are wiped and cleanly re-downloaded."""
    root_dir = tmp_path / "app_root"
    model_dir = root_dir / "models" / "buffalo_l"
    model_dir.mkdir(parents=True)

    # Put corrupted files in model_dir
    (model_dir / "1k3d68.onnx").write_bytes(b"corrupted_data")

    # Mock custom specs
    test_specs = {
        "model1.onnx": {"size": 25, "sha256": hashlib.sha256(b"1" * 25).hexdigest()},
    }
    monkeypatch.setattr("backend.engine.models_downloader.BUFFALO_L_ONNX_SPECS", test_specs)

    # Mock successful download
    zip_bytes = _create_mock_model_zip({"model1.onnx": {"size": 25}})
    # Write actual matching data
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("buffalo_l/model1.onnx", b"1" * 25)
    valid_zip_data = buf.getvalue()

    class SuccessResponse:
        headers = {"Content-Length": str(len(valid_zip_data))}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, chunk_size):
            if not hasattr(self, "_stream"):
                self._stream = io.BytesIO(valid_zip_data)
            return self._stream.read(chunk_size)

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: SuccessResponse())

    reports = []
    def progress_cb(evt):
        reports.append(evt)

    res_path = ensure_model_available(
        model_name="buffalo_l",
        model_root=root_dir,
        progress_callback=progress_cb,
    )

    assert res_path == model_dir
    assert (model_dir / "model1.onnx").exists()
    assert (model_dir / "model1.onnx").stat().st_size == 25
    # Verify notification that corrupt model was removed
    assert any("failed verification" in r.get("message", "") for r in reports)
    # Verify progress reported with size
    download_evts = [r for r in reports if r.get("stage") == "model_download"]
    assert len(download_evts) > 0
    assert any("MB" in r.get("message", "") for r in download_evts)
