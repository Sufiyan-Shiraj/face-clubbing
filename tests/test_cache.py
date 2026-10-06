"""Unit tests for the cache module."""

from pathlib import Path
import tempfile
import unittest
from backend.engine.cache import DiskCache
from backend.engine.detector import DetectedFace


class TestDiskCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = DiskCache(cache_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_miss(self):
        self.assertFalse(self.cache.has("missing_id"))
        self.assertIsNone(self.cache.load_detections("missing_id"))

    def test_save_and_load(self):
        face = DetectedFace(
            face_id="photo1_00",
            photo_id="photo1",
            bbox=[10.0, 20.0, 100.0, 120.0],
            det_score=0.95,
            kps=[[30.0, 40.0], [70.0, 40.0], [50.0, 60.0], [40.0, 90.0], [60.0, 90.0]],
            embedding=[0.1] * 512,
            is_quality=True,
            quality_reason="",
        )
        meta = {"width": 1920, "height": 1080}

        self.cache.save_detections("photo1", [face], meta)
        self.assertTrue(self.cache.has("photo1"))

        loaded = self.cache.load_detections("photo1")
        self.assertIsNotNone(loaded)
        faces, loaded_meta = loaded
        self.assertEqual(len(faces), 1)
        self.assertEqual(faces[0].face_id, "photo1_00")
        self.assertEqual(faces[0].det_score, 0.95)
        self.assertEqual(faces[0].bbox, [10.0, 20.0, 100.0, 120.0])
        self.assertEqual(len(faces[0].embedding), 512)
        self.assertEqual(loaded_meta.get("width"), 1920)


if __name__ == "__main__":
    unittest.main()
