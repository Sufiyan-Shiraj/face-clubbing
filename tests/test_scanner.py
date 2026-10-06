"""Unit tests for the scanner module."""

from pathlib import Path
import tempfile
import zipfile
import unittest
from backend.engine.scanner import compute_file_hash, scan_source, is_image_file


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_is_image_file(self):
        self.assertTrue(is_image_file("photo.jpg"))
        self.assertTrue(is_image_file("photo.JPEG"))
        self.assertTrue(is_image_file("photo.png"))
        self.assertTrue(is_image_file("photo.heic"))
        self.assertTrue(is_image_file("photo.HEIF"))
        self.assertFalse(is_image_file("document.pdf"))
        self.assertFalse(is_image_file("script.py"))

    def test_compute_file_hash_stability(self):
        f1 = self.root / "test1.jpg"
        f2 = self.root / "test2.jpg"
        content = b"fake-image-bytes-12345"
        f1.write_bytes(content)
        f2.write_bytes(content)

        h1 = compute_file_hash(f1)
        h2 = compute_file_hash(f2)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 16)

    def test_scan_folder(self):
        (self.root / "img1.jpg").write_bytes(b"content1")
        (self.root / "img2.PNG").write_bytes(b"content2")
        (self.root / "notes.txt").write_bytes(b"ignore me")

        sub = self.root / "subfolder"
        sub.mkdir()
        (sub / "img3.jpeg").write_bytes(b"content3")

        items, cleanup = scan_source(self.root)
        self.assertIsNone(cleanup)
        self.assertEqual(len(items), 3)

        filenames = [item.filename for item in items]
        self.assertIn("img1.jpg", filenames)
        self.assertIn("img2.PNG", filenames)
        self.assertIn("img3.jpeg", filenames)
        self.assertNotIn("notes.txt", filenames)

    def test_scan_zip(self):
        zip_path = self.root / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("event/photo_a.jpg", b"image-a")
            zf.writestr("event/photo_b.png", b"image-b")
            zf.writestr("event/readme.txt", b"text")

        items, cleanup = scan_source(zip_path)
        self.assertIsNotNone(cleanup)
        try:
            self.assertEqual(len(items), 2)
            filenames = [item.filename for item in items]
            self.assertIn("photo_a.jpg", filenames)
            self.assertIn("photo_b.png", filenames)
        finally:
            if cleanup and cleanup.exists():
                import shutil
                shutil.rmtree(cleanup, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
