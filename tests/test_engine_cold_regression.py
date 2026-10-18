"""Cold end-to-end regression tests verifying clustering stability and avatar bbox integrity.

Requirements (SPEC & Task 5):
1. A cold E2E run (empty cache) on a fixed subset of at least 40 photos from test_photos,
   compared against pinned expected output:
   - cluster count, clustered face count, unrecognized face/photo counts
   - per-face cluster membership via face IDs
   - representative face matches the cluster's own face IDs
2. A second test verifying that the avatar/crop for every face ID is cut from that face's own bbox,
   with exact dimensions (256x256 per SPEC 6.2) and no cross-person avatar reuse.
3. Skip only when test_photos is absent, and the skip is explicitly reported.
"""

from __future__ import annotations
import json
import shutil
from pathlib import Path
import numpy as np
import pytest
from PIL import Image, ImageOps

from backend.engine.pipeline import EngineConfig, run_pipeline
from backend.engine.models import PhotoRecord
from backend.engine.thumbnails import ThumbnailGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_PHOTOS_DIR = REPO_ROOT / "test_photos"
EXPECTED_FIXTURE = REPO_ROOT / "eval" / "regression_40_expected.json"


def _get_sorted_test_photos(limit: int = 40) -> list[Path]:
    if not TEST_PHOTOS_DIR.exists():
        return []
    photos = sorted([
        p for p in TEST_PHOTOS_DIR.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic", ".webp")
    ])
    return photos[:limit]


@pytest.mark.skipif(
    not TEST_PHOTOS_DIR.exists(),
    reason="test_photos/ directory is absent (photos not tracked in git per privacy rules)",
)
def test_cold_e2e_regression_on_fixed_subset(tmp_path: Path):
    """Verifies that a cold run (empty cache) on 40 photos matches the pinned baseline exactly."""
    assert EXPECTED_FIXTURE.exists(), f"Missing pinned expected output fixture: {EXPECTED_FIXTURE}"
    expected = json.loads(EXPECTED_FIXTURE.read_text(encoding="utf-8"))

    photos = _get_sorted_test_photos(limit=40)
    assert len(photos) >= 40, f"Expected at least 40 photos in test_photos, found {len(photos)}"

    photos_in = tmp_path / "photos"
    photos_in.mkdir(parents=True)
    out_dir = tmp_path / "export"
    work_dir = tmp_path / "export.work"

    for p in photos:
        shutil.copy2(p, photos_in / p.name)

    # Completely cold run with empty cache
    cfg = EngineConfig(
        input_path=photos_in,
        output_dir=out_dir,
        cache_dir=work_dir,
        face_crop_size=256,
    )
    result = run_pipeline(cfg)

    # 1. Check top-level counts
    clustered_faces = sum(len(p.faces) for p in result.people)
    assert len(result.people) == expected["people_count"], (
        f"People count mismatch: got {len(result.people)}, expected {expected['people_count']}"
    )
    assert clustered_faces == expected["clustered_faces"], (
        f"Clustered faces mismatch: got {clustered_faces}, expected {expected['clustered_faces']}"
    )
    assert len(result.unrecognized.faces) == expected["unrec_faces"], (
        f"Unrecognized faces mismatch: got {len(result.unrecognized.faces)}, expected {expected['unrec_faces']}"
    )
    assert len(result.unrecognized.photo_ids) == expected["unrec_photos"], (
        f"Unrecognized photos mismatch: got {len(result.unrecognized.photo_ids)}, expected {expected['unrec_photos']}"
    )

    # 2. Check cluster membership and representative face matching
    actual_clusters = {}
    for p in result.people:
        rep_fid = p.rep_face.face_id if p.rep_face else None
        fids = sorted([f.face_id for f in p.faces])
        assert rep_fid is not None, f"Cluster {p.id} has no representative face"
        assert rep_fid in fids, f"Cluster {p.id} representative {rep_fid} not among its face IDs: {fids}"
        actual_clusters[p.id] = {
            "face_ids": fids,
            "representative_face_id": rep_fid,
        }

    for cid, exp_c in expected["clusters"].items():
        assert cid in actual_clusters, f"Expected cluster {cid} missing in result"
        assert actual_clusters[cid]["face_ids"] == exp_c["face_ids"], (
            f"Cluster {cid} face ID membership differs: {set(actual_clusters[cid]['face_ids']) ^ set(exp_c['face_ids'])}"
        )
        assert actual_clusters[cid]["representative_face_id"] == exp_c["representative_face_id"], (
            f"Cluster {cid} representative face differs: got {actual_clusters[cid]['representative_face_id']}, "
            f"expected {exp_c['representative_face_id']}"
        )

    # 3. Check unrecognized face IDs
    actual_unrec_fids = sorted([f["face_id"] for f in result.unrecognized.faces])
    assert actual_unrec_fids == expected["unrec_face_ids"], "Unrecognized face IDs differ from pinned expected"

    # 4. Check exported people.json and avatar files
    people_json_path = out_dir / "people.json"
    assert people_json_path.exists(), "people.json was not generated"
    people_data = json.loads(people_json_path.read_text(encoding="utf-8"))
    assert len(people_data["people"]) == expected["people_count"]

    for pentry in people_data["people"]:
        face_path = out_dir / pentry["face"]
        assert face_path.exists(), f"Avatar crop missing: {face_path}"
        with Image.open(face_path) as im:
            assert im.size == (256, 256), f"Avatar crop size is {im.size}, expected (256, 256) per SPEC 6.2"


@pytest.mark.skipif(
    not TEST_PHOTOS_DIR.exists(),
    reason="test_photos/ directory is absent (photos not tracked in git per privacy rules)",
)
def test_avatar_and_face_crops_match_own_bboxes(tmp_path: Path):
    """Verifies that every face crop is cut from its own bbox in the original photo."""
    photos = _get_sorted_test_photos(limit=10)
    assert len(photos) >= 10, f"Expected at least 10 photos in test_photos, found {len(photos)}"

    photos_in = tmp_path / "photos"
    photos_in.mkdir(parents=True)
    out_dir = tmp_path / "export"
    work_dir = tmp_path / "export.work"

    for p in photos:
        shutil.copy2(p, photos_in / p.name)

    cfg = EngineConfig(
        input_path=photos_in,
        output_dir=out_dir,
        cache_dir=work_dir,
        face_crop_size=256,
    )
    result = run_pipeline(cfg)

    thumb_gen = ThumbnailGenerator(thumb_size=400, face_crop_size=256)

    # 1. Verify face crops in work_dir/crops match the ground-truth crop cut from original photo
    cached_records = [
        PhotoRecord.from_dict(json.loads(f.read_text(encoding="utf-8")))
        for f in work_dir.glob("*.json") if len(f.stem) == 16
    ]

    total_verified = 0
    for rec in cached_records:
        src_photo = photos_in / rec.file_name
        assert src_photo.exists(), f"Source photo missing: {src_photo}"
        with Image.open(src_photo) as raw_img:
            img = ImageOps.exif_transpose(raw_img)
            if img.mode != "RGB":
                img = img.convert("RGB")
            for f in rec.faces:
                crop_file = work_dir / "crops" / f"{f.face_id}.jpg"
                assert crop_file.exists(), f"Face crop missing: {crop_file}"

                # Generate ground-truth crop directly from image using face's own bbox
                tmp_crop_path = tmp_path / f"tmp_{f.face_id}.jpg"
                thumb_gen.generate_square_face_crop_from_image(img, f.bbox, tmp_crop_path)

                crop_a = np.array(Image.open(crop_file))
                crop_b = np.array(Image.open(tmp_crop_path))
                assert crop_a.shape == (256, 256, 3), f"Unexpected crop dimensions: {crop_a.shape}"
                mean_diff = float(np.abs(crop_a.astype(float) - crop_b.astype(float)).mean())
                assert mean_diff == 0.0, (
                    f"Face crop for {f.face_id} does not match its own bounding box! mean_diff={mean_diff}"
                )
                total_verified += 1

    assert total_verified > 0, "No faces were verified"

    # 2. Verify representative face avatars in export/faces match the representative face's crop
    # and guard against cross-person avatar reuse
    seen_rep_fids: dict[str, str] = {}
    for p in result.people:
        rep_fid = p.rep_face.face_id
        avatar_path = out_dir / "faces" / f"{p.id}.jpg"
        rep_crop_path = work_dir / "crops" / f"{rep_fid}.jpg"

        assert avatar_path.exists(), f"Person avatar missing: {avatar_path}"
        assert rep_crop_path.exists(), f"Representative crop missing: {rep_crop_path}"
        assert avatar_path.read_bytes() == rep_crop_path.read_bytes(), (
            f"Avatar {avatar_path} was not copied from representative face {rep_fid}"
        )

        if rep_fid in seen_rep_fids:
            # If two distinct clusters share a representative face ID, that indicates severe logic bug
            pytest.fail(f"Representative face {rep_fid} shared between {p.id} and {seen_rep_fids[rep_fid]}")
        seen_rep_fids[rep_fid] = p.id
