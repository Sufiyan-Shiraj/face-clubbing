"""Unit tests for the EmbeddingCache module."""

import numpy as np
import pytest
from pathlib import Path

from backend.engine.cache import EmbeddingCache
from backend.engine.models import FaceDetection, PhotoRecord


def test_cache_miss(tmp_path: Path):
    cache = EmbeddingCache(tmp_path)
    assert not cache.has("nonexistent_photo")
    assert cache.get("nonexistent_photo") is None


def test_cache_save_and_get(tmp_path: Path):
    cache = EmbeddingCache(tmp_path)
    emb = np.random.randn(512).astype(np.float32)
    emb /= np.linalg.norm(emb)

    face = FaceDetection(
        face_id="f_p1_001",
        photo_id="p1",
        bbox=[10.0, 20.0, 100.0, 120.0],
        det_score=0.95,
        embedding=emb,
        landmarks=[[30.0, 40.0], [70.0, 40.0], [50.0, 60.0], [40.0, 90.0], [60.0, 90.0]],
        pose=[10.0, -5.0, 2.0],
        is_good_quality=True,
        rejection_reason=None,
    )
    record = PhotoRecord(
        photo_id="p1",
        original_path="/path/to/img1.jpg",
        file_name="img1.jpg",
        width=1920,
        height=1080,
        faces=[face],
    )

    cache.save(record)
    assert cache.has("p1")

    loaded = cache.get("p1")
    assert loaded is not None
    assert loaded.photo_id == "p1"
    assert loaded.width == 1920
    assert loaded.height == 1080
    assert len(loaded.faces) == 1
    loaded_face = loaded.faces[0]
    assert loaded_face.face_id == "f_p1_001"
    assert loaded_face.det_score == pytest.approx(0.95)
    assert loaded_face.bbox == [10.0, 20.0, 100.0, 120.0]
    assert loaded_face.embedding is not None
    assert np.allclose(loaded_face.embedding, emb, atol=1e-5)
    assert loaded_face.pose == [10.0, -5.0, 2.0]


def test_cache_load_all(tmp_path: Path):
    cache = EmbeddingCache(tmp_path)
    for i in range(3):
        pid = f"p{i}"
        rec = PhotoRecord(
            photo_id=pid,
            original_path=f"/path/{pid}.jpg",
            file_name=f"{pid}.jpg",
            width=800,
            height=600,
            faces=[],
        )
        cache.save(rec)

    all_records = cache.load_all()
    assert len(all_records) == 3
    assert set(all_records.keys()) == {"p0", "p1", "p2"}


def test_cache_invalidation_on_version_mismatch(tmp_path: Path):
    """Old cache entries with missing or old cache_version are ignored."""
    import json
    legacy_file = tmp_path / "legacy.json"
    legacy_file.write_text(json.dumps({
        "photo_id": "legacy",
        "original_path": "/path/legacy.jpg",
        "file_name": "legacy.jpg",
        "width": 800,
        "height": 600,
        "faces": [],
        # No cache_version or old version 1
        "cache_version": 1,
    }))

    cache = EmbeddingCache(tmp_path, cache_version=2)
    assert not cache.has("legacy")
    assert cache.get("legacy") is None
    assert "legacy" not in cache.load_all()


def test_cache_invalidation_on_settings_mismatch(tmp_path: Path):
    """Cache entries created under different detector settings are invalidated."""
    from backend.engine.cache import compute_settings_hash

    hash_a = compute_settings_hash(min_face_size=64)
    hash_b = compute_settings_hash(min_face_size=80)
    assert hash_a != hash_b

    cache_a = EmbeddingCache(tmp_path, settings_hash=hash_a)
    rec = PhotoRecord(
        photo_id="photo1",
        original_path="/path/photo1.jpg",
        file_name="photo1.jpg",
        width=800,
        height=600,
        faces=[],
    )
    cache_a.save(rec)
    assert cache_a.has("photo1")

    # Cache with different settings hash rejects photo1
    cache_b = EmbeddingCache(tmp_path, settings_hash=hash_b)
    assert not cache_b.has("photo1")
    assert cache_b.get("photo1") is None

