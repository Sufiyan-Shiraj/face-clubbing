"""Unit tests for the exporter module."""

import json
from pathlib import Path
import tempfile
import unittest

from backend.engine.clustering import PersonCluster, UnrecognizedData
from backend.engine.detector import DetectedFace
from backend.engine.exporter import export_bundle
from backend.engine.scanner import ScanItem


class TestExporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_bundle_schema_and_validation(self):
        photo1 = ScanItem(
            photo_id="pid1",
            path=self.export_dir / "p1.jpg",
            filename="p1.jpg",
            relative_path="p1.jpg",
            file_size=1024,
        )
        photo2 = ScanItem(
            photo_id="pid2",
            path=self.export_dir / "p2.jpg",
            filename="p2.jpg",
            relative_path="p2.jpg",
            file_size=2048,
        )
        photos = {"pid1": photo1, "pid2": photo2}
        photo_dimensions = {"pid1": (1920, 1080), "pid2": (1280, 720)}

        # Person 1 appears in photo1
        person1 = PersonCluster(
            person_id="p001",
            face_ids=["pid1_0"],
            photo_ids=["pid1"],
            faces=[],
            crop_path="faces/p001.jpg",
            label="Alice",
        )

        # photo2 is unrecognized (no faces)
        unrecognized = UnrecognizedData(
            photo_ids=["pid2"],
            faces=[],
            face_crops=[],
        )

        bundle = export_bundle(
            export_dir=self.export_dir,
            photos=photos,
            photo_dimensions=photo_dimensions,
            people=[person1],
            unrecognized=unrecognized,
        )

        # Verify files exist
        self.assertTrue((self.export_dir / "people.json").is_file())
        self.assertTrue((self.export_dir / "config.json").is_file())
        self.assertTrue((self.export_dir / "faces").is_dir())
        self.assertTrue((self.export_dir / "thumbs").is_dir())

        # Verify bundle contents
        self.assertEqual(bundle["version"], 1)
        self.assertIn("pid1", bundle["photos"])
        self.assertIn("pid2", bundle["photos"])
        self.assertEqual(bundle["photos"]["pid1"]["name"], "p1.jpg")
        self.assertEqual(len(bundle["people"]), 1)
        self.assertEqual(bundle["people"][0]["id"], "p001")
        self.assertIn("pid2", bundle["unrecognized"]["photo_ids"])

        # Check config.json
        with open(self.export_dir / "config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertEqual(cfg["font"], "Inter")


if __name__ == "__main__":
    unittest.main()
