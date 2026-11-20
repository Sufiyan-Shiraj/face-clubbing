"""Automated tests for Google Drive quality tiers and small face handling (BUILD_PLAN Phase V2-6).

Covers:
1. Preset target size mapping (fast -> 1000, better -> 1600, best -> 2000, original -> 0).
2. URL rewriting with =s1000, =s1600, =s2000.
3. Resumable cache invalidation on quality tier change (re-downloads when quality changes, caches when unchanged).
4. SPEC 6.2 default preservation: min_face_size=64 and seed_min_face_size=64 remain unchanged.
5. Invariant preservation: Clustered + Unattached == Total Detected Faces across quality settings.
"""

from __future__ import annotations
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import numpy as np

from backend.drive.client import (
    DriveClient,
    DriveFile,
    DRIVE_QUALITY_SIZES,
    get_drive_target_size,
    resize_thumbnail_link,
)
from backend.engine.pipeline import EngineConfig
from backend.api.models import SettingsModel, JobStartRequest
from backend.engine.models import FaceDetection, PhotoRecord
from backend.engine.clusterer import FaceClusterer


class TestQualityTierPresets:
    """Verifies target size mappings and URL rewriting for quality presets."""

    def test_preset_mappings(self):
        assert DRIVE_QUALITY_SIZES["fast"] == 1000
        assert DRIVE_QUALITY_SIZES["better"] == 1600
        assert DRIVE_QUALITY_SIZES["best"] == 2000
        assert DRIVE_QUALITY_SIZES["original"] == 0

        assert get_drive_target_size("fast") == 1000
        assert get_drive_target_size("better") == 1600
        assert get_drive_target_size("best") == 2000
        assert get_drive_target_size("original") == 0
        assert get_drive_target_size(None) == 0  # Default is original
        assert get_drive_target_size("nonexistent") == 0

    def test_custom_target_size_override(self):
        # Explicit target_size overrides quality string
        assert get_drive_target_size("fast", target_size=1200) == 1200
        assert get_drive_target_size("better", target_size=800) == 800

    def test_thumbnail_link_rewriting(self):
        base_thumb = "https://lh3.googleusercontent.com/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs=s220"
        assert resize_thumbnail_link(base_thumb, 1000) == "https://lh3.googleusercontent.com/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs=s1000"
        assert resize_thumbnail_link(base_thumb, 1600) == "https://lh3.googleusercontent.com/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs=s1600"
        assert resize_thumbnail_link(base_thumb, 2000) == "https://lh3.googleusercontent.com/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs=s2000"

        # No dimension parameter present -> appends ?sz=s1000
        url_without_dim = "https://lh3.googleusercontent.com/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"
        assert resize_thumbnail_link(url_without_dim, 1000) == "https://lh3.googleusercontent.com/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs?sz=s1000"


class TestQualityTierCacheInvalidation:
    """Verifies that switching quality tiers invalidates cache and triggers re-download."""

    def test_resumable_cache_invalidation_on_quality_change(self):
        client = DriveClient(api_key="test_api_key_123")
        file_obj = DriveFile(
            id="file_001",
            name="photo.jpg",
            mime_type="image/jpeg",
            modified_time="2026-10-15T12:00:00Z",
            size=5000000,
            thumbnail_link="https://lh3.googleusercontent.com/d/file_001=s220",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_path = Path(tmp_dir)

            # 1. Download at 'fast' (=s1000)
            mock_resp_1000 = MagicMock()
            mock_resp_1000.status_code = 200
            mock_resp_1000.content = b"FAKEDATA_1000_BYTES_" * 20

            with patch.object(client, "_request_with_retry", return_value=mock_resp_1000) as mock_req:
                res1 = client.download_thumbnails([file_obj], cache_dir=cache_path, quality="fast")
                assert len(res1) == 1
                assert mock_req.call_count == 1
                # Check manifest records target_size: 1000
                manifest = json.loads((cache_path / "manifest.json").read_text(encoding="utf-8"))
                assert manifest["file_001"]["target_size"] == 1000

            # 2. Re-download at same 'fast' tier -> Cache hit (no network request)
            with patch.object(client, "_request_with_retry") as mock_req_skip:
                res2 = client.download_thumbnails([file_obj], cache_dir=cache_path, quality="fast")
                assert len(res2) == 1
                assert mock_req_skip.call_count == 0  # Reused from cache!

            # 3. Download at 'better' (=s1600) -> Target size differs (1600 != 1000) -> Must re-download!
            mock_resp_1600 = MagicMock()
            mock_resp_1600.status_code = 200
            mock_resp_1600.content = b"FAKEDATA_1600_BYTES_" * 40

            with patch.object(client, "_request_with_retry", return_value=mock_resp_1600) as mock_req_new:
                res3 = client.download_thumbnails([file_obj], cache_dir=cache_path, quality="better")
                assert len(res3) == 1
                assert mock_req_new.call_count == 1  # Re-download triggered!
                manifest = json.loads((cache_path / "manifest.json").read_text(encoding="utf-8"))
                assert manifest["file_001"]["target_size"] == 1600

            # 4. Re-download at 'better' -> Cache hit
            with patch.object(client, "_request_with_retry") as mock_req_skip2:
                res4 = client.download_thumbnails([file_obj], cache_dir=cache_path, quality="better")
                assert len(res4) == 1
                assert mock_req_skip2.call_count == 0


class TestSpecDefaultsPreservation:
    """Verifies that SPEC 6.2 defaults (min_face_size=64, seed_min_face_size=64) remain strictly preserved."""

    def test_engine_config_defaults(self):
        cfg = EngineConfig(input_path="dummy_path")
        assert cfg.drive_image_quality == "original"
        # SPEC 6.2 defaults MUST NOT be changed
        assert cfg.min_face_size == 64
        assert cfg.seed_min_face_size == 64
        assert cfg.distance_threshold == 0.50

    def test_settings_model_defaults(self):
        sm = SettingsModel()
        assert sm.drive_image_quality == "original"
        assert sm.min_face_size == 64
        assert sm.distance_threshold == 0.50

    def test_job_start_request_optional(self):
        req = JobStartRequest(path_or_url="https://drive.google.com/drive/folders/1abc")
        assert req.drive_image_quality is None  # Defaults to server settings if unspecified


class TestClusteringInvariantAcrossFaceSizes:
    """Verifies invariant Clustered + Unattached == Total Detected Faces holds with small faces."""

    def test_invariant_holds_with_small_and_large_faces(self):
        # Create synthetic detections: some seed-sized (>=64), some small (<64)
        emb1 = np.random.randn(512).astype(np.float32)
        emb1 /= np.linalg.norm(emb1)

        emb2 = np.random.randn(512).astype(np.float32)
        emb2 /= np.linalg.norm(emb2)

        # Seed face: 100x100
        face_seed = FaceDetection(
            face_id="f_001_seed",
            photo_id="p1",
            bbox=[100, 100, 200, 200],  # 100x100
            det_score=0.95,
            embedding=emb1,
            pose=[0.0, 5.0, 0.0],
            is_good_quality=True,
        )

        # Small face: 40x40 (under 64px) with high similarity to emb1 -> should attach
        face_small_attach = FaceDetection(
            face_id="f_002_small",
            photo_id="p2",
            bbox=[50, 50, 90, 90],  # 40x40
            det_score=0.85,
            embedding=emb1.copy(),
            pose=[0.0, 2.0, 0.0],
            is_good_quality=False,
            rejection_reason="face_too_small (40px < 64px)",
        )

        # Small face: 30x30 with unrelated embedding -> should stay unattached
        face_small_unrec = FaceDetection(
            face_id="f_003_unrec",
            photo_id="p3",
            bbox=[10, 10, 40, 40],  # 30x30
            det_score=0.80,
            embedding=emb2,
            pose=[0.0, 1.0, 0.0],
            is_good_quality=False,
            rejection_reason="face_too_small (30px < 64px)",
        )

        photos = {
            "p1": PhotoRecord("p1", "p1.jpg", "p1.jpg", 1000, 1000, faces=[face_seed]),
            "p2": PhotoRecord("p2", "p2.jpg", "p2.jpg", 1000, 1000, faces=[face_small_attach]),
            "p3": PhotoRecord("p3", "p3.jpg", "p3.jpg", 1000, 1000, faces=[face_small_unrec]),
        }

        clusterer = FaceClusterer(
            distance_threshold=0.50,
            seed_min_face_size=64,
            second_pass_merge=True,
        )
        people, unrec = clusterer.cluster(photos)

        total_faces = 3
        clustered_faces = sum(len(p.faces) for p in people)
        unrec_faces = len(unrec.faces)

        # Strict mathematical invariant: Clustered + Unattached == Total
        assert clustered_faces + unrec_faces == total_faces
        assert unrec_faces == 1
        assert clustered_faces == 2
        assert len(people) == 1
        assert people[0].photo_ids == ["p1", "p2"]
