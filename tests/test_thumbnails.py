"""Unit tests for avatar selection quality scoring and high-definition face crops."""

import math
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
import pytest

from backend.engine.models import FaceDetection
from backend.engine.thumbnails import (
    ThumbnailGenerator,
    compute_face_quality_score,
    compute_image_sharpness,
    select_representative_face,
)


def test_sharpness_calculation_differentiates_sharp_and_blurry(tmp_path: Path):
    # Sharp image with distinct checkerboard high frequency edges
    arr = np.zeros((100, 100), dtype=np.uint8)
    arr[::4, :] = 255
    arr[:, ::4] = 255
    sharp_img = Image.fromarray(arr)
    sharp_path = tmp_path / "sharp.jpg"
    sharp_img.save(sharp_path, format="JPEG", quality=95)

    # Blurry image
    blurry_img = sharp_img.filter(ImageFilter.GaussianBlur(radius=5.0))
    blurry_path = tmp_path / "blurry.jpg"
    blurry_img.save(blurry_path, format="JPEG", quality=95)

    score_sharp = compute_image_sharpness(sharp_path)
    score_blurry = compute_image_sharpness(blurry_path)

    assert score_sharp > score_blurry * 3.0
    assert score_blurry < 50.0


def test_avatar_selection_prefers_clear_large_frontal_face():
    # Face A: Small, distant face (50x50), blurry, slightly turned
    face_small = FaceDetection(
        face_id="face_small",
        photo_id="photo_1",
        bbox=[100.0, 100.0, 150.0, 150.0],
        det_score=0.88,
        pose=[15.0, 30.0, 12.0],  # turned yaw 30 deg
        sharpness=22.0,  # blurry
        is_good_quality=True,
    )

    # Face B: High-res portrait face (260x260), clear, sharp, frontal
    face_large_frontal = FaceDetection(
        face_id="face_large_frontal",
        photo_id="photo_2",
        bbox=[200.0, 200.0, 460.0, 460.0],
        det_score=0.94,
        pose=[2.0, 3.0, 1.0],  # frontal eye-level
        sharpness=185.0,  # sharp
        landmarks=[
            [260.0, 280.0],  # left eye
            [380.0, 280.0],  # right eye
            [320.0, 340.0],  # nose (centered)
            [280.0, 400.0],  # left mouth
            [360.0, 400.0],  # right mouth
        ],
        is_good_quality=True,
    )

    score_small = compute_face_quality_score(face_small)
    score_large = compute_face_quality_score(face_large_frontal)

    assert score_large > score_small + 20.0

    chosen = select_representative_face([face_small, face_large_frontal])
    assert chosen.face_id == "face_large_frontal"


def test_avatar_selection_penalizes_profile_and_extreme_tilt():
    # Face 1: Frontal, upright (200x200)
    face_frontal = FaceDetection(
        face_id="f_frontal",
        photo_id="p1",
        bbox=[100.0, 100.0, 300.0, 300.0],
        det_score=0.91,
        pose=[0.0, 0.0, 0.0],
        landmarks=[[150.0, 160.0], [250.0, 160.0], [200.0, 200.0], [170.0, 250.0], [230.0, 250.0]],
    )

    # Face 2: Same size, but extreme profile turned 45 degrees
    face_profile = FaceDetection(
        face_id="f_profile",
        photo_id="p2",
        bbox=[100.0, 100.0, 300.0, 300.0],
        det_score=0.91,
        pose=[0.0, 45.0, 0.0],
        landmarks=[[150.0, 160.0], [250.0, 160.0], [240.0, 200.0], [170.0, 250.0], [230.0, 250.0]],
    )

    score_f = compute_face_quality_score(face_frontal)
    score_p = compute_face_quality_score(face_profile)

    assert score_f > score_p + 10.0


def test_thumbnail_generator_creates_high_quality_384_square_crop(tmp_path: Path):
    gen = ThumbnailGenerator(thumb_size=400, face_crop_size=384)
    assert gen.face_crop_size == 384

    # Create test image
    img = Image.new("RGB", (800, 600), color=(180, 200, 220))
    # Draw some detail so it's not solid
    detail = Image.new("RGB", (200, 200), color=(80, 120, 160))
    img.paste(detail, (250, 150))

    out_crop = tmp_path / "avatar_high_quality.jpg"
    gen.generate_square_face_crop_from_image(
        img=img,
        bbox=[250.0, 150.0, 450.0, 350.0],
        output_path=out_crop,
    )

    assert out_crop.exists()
    with Image.open(out_crop) as res:
        assert res.size == (384, 384)
        assert res.format == "JPEG"


def test_boundary_handling_prevents_black_bars_near_photo_edges(tmp_path: Path):
    gen = ThumbnailGenerator(thumb_size=400, face_crop_size=384)

    # Face positioned right against the top-left boundary [0, 0, 120, 120]
    img = Image.new("RGB", (500, 500), color=(255, 128, 64))
    out_edge = tmp_path / "avatar_edge.jpg"

    gen.generate_square_face_crop_from_image(
        img=img,
        bbox=[0.0, 0.0, 120.0, 120.0],
        output_path=out_edge,
    )

    assert out_edge.exists()
    with Image.open(out_edge) as res:
        assert res.size == (384, 384)
        # Verify no pure black (0, 0, 0) border was pasted
        arr = np.array(res)
        # Background was (255, 128, 64), so corners should NOT be (0, 0, 0)
        assert arr[0, 0, 0] > 100
