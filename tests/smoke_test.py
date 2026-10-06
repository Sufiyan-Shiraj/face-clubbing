"""Phase 0 Smoke Test: Verify InsightFace installation, model downloading, and face detection."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.engine.scanner import PhotoScanner
from backend.engine.loader import ImageLoader
from backend.engine.detector import FaceDetector


def main():
    print("=" * 60)
    print("PHASE 0 SMOKE TEST: InsightFace & Face Detection")
    print("=" * 60)

    test_photos_dir = PROJECT_ROOT / "test_photos"
    if not test_photos_dir.exists():
        print(f"ERROR: test_photos directory not found at {test_photos_dir}")
        sys.exit(1)

    with PhotoScanner(test_photos_dir) as scanner:
        photos = scanner.scan()
        print(f"Discovered {len(photos)} test photos.")
        if not photos:
            print("ERROR: No photos found in test_photos!")
            sys.exit(1)

        # Pick first 3 photos for smoke test
        sample_photos = photos[:3]
        loader = ImageLoader(max_dimension=1600)

        print("\nInitializing InsightFace FaceDetector (buffalo_l)...")
        detector = FaceDetector(model_name="buffalo_l", min_det_score=0.5, min_face_size=35)

        total_faces_detected = 0
        for i, photo in enumerate(sample_photos, 1):
            print(f"\n[{i}/{len(sample_photos)}] Testing on {photo.file_name}...")
            rgb_img, orig_w, orig_h, scale = loader.load_image(photo.file_path)
            print(f"  Loaded dimensions: {orig_w}x{orig_h} (scale: {scale:.2f})")

            faces = detector.detect_and_embed(rgb_img, photo.photo_id, scale)
            print(f"  Faces detected: {len(faces)}")
            for f in faces:
                print(f"    - ID: {f.face_id}, Score: {f.det_score:.3f}, Quality: {f.is_good_quality}, Reason: {f.rejection_reason}")
                if f.embedding is not None:
                    print(f"      Embedding norm: {float((f.embedding**2).sum()**0.5):.3f}, dim: {len(f.embedding)}")

            total_faces_detected += len(faces)

        print("\n" + "=" * 60)
        print(f"SMOKE TEST SUMMARY: Detected {total_faces_detected} faces across {len(sample_photos)} test photos.")
        print("InsightFace, ONNX Runtime, and image loaders are working correctly!")
        print("=" * 60)


if __name__ == "__main__":
    main()
