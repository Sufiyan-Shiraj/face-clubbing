"""Cropper module: selects representative faces and generates square crops."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence
import numpy as np
from PIL import Image, ImageOps

from .detector import DetectedFace

# Attempt to register HEIF opener
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def compute_frontal_score(kps: list[list[float]] | None) -> float:
    """Computes a frontalness score [0.0, 1.0] from 5 facial keypoints.
    Keypoint indices: 0: left eye, 1: right eye, 2: nose, 3: left mouth, 4: right mouth.
    """
    if not kps or len(kps) < 5:
        return 0.5

    left_eye = kps[0]
    right_eye = kps[1]
    nose = kps[2]

    eye_dx = right_eye[0] - left_eye[0]
    eye_dy = right_eye[1] - left_eye[1]
    eye_dist = math.hypot(eye_dx, eye_dy)

    if eye_dist < 1e-4:
        return 0.2

    # Tilt angle penalty (tilt from horizontal)
    tilt_ratio = abs(eye_dy) / eye_dist
    tilt_score = max(0.0, 1.0 - tilt_ratio * 1.5)

    # Symmetry score (nose horizontal placement between eyes)
    d_left = abs(nose[0] - left_eye[0])
    d_right = abs(right_eye[0] - nose[0])
    max_d = max(d_left, d_right)
    if max_d < 1e-4:
        symmetry_score = 0.5
    else:
        symmetry_score = min(d_left, d_right) / max_d

    return float(np.clip(0.6 * symmetry_score + 0.4 * tilt_score, 0.05, 1.0))


def pick_representative_face(faces: Sequence[DetectedFace]) -> DetectedFace:
    """Selects the best representative face for a person based on detection score,
    face resolution, sharpness, and frontalness.
    """
    if not faces:
        raise ValueError("Cannot select representative face from an empty list.")
    if len(faces) == 1:
        return faces[0]

    best_face = faces[0]
    best_score = -1e9

    for face in faces:
        w = max(1.0, face.bbox[2] - face.bbox[0])
        h = max(1.0, face.bbox[3] - face.bbox[1])
        min_dim = min(w, h)

        # Resolution score (smooth square root curve, penalized if tiny)
        size_score = math.sqrt(min(min_dim, 400.0)) * 1.6
        if min_dim < 70.0:
            size_score -= (70.0 - min_dim) * 0.35

        # Confidence component
        conf_score = (face.det_score ** 2) * 15.0

        # Frontal score
        frontal = compute_frontal_score(face.kps)
        frontal_score = (frontal - 0.5) * 10.0

        score = size_score + conf_score + frontal_score
        if score > best_score:
            best_score = score
            best_face = face

    return best_face


def crop_face_square(
    image_path: Path | str,
    face: DetectedFace,
    out_path: Path | str,
    crop_size: int = 384,
    margin_ratio: float = 0.35,
    vertical_shift: float = 0.08,
) -> None:
    """Extracts a square face crop with padding around the face and saves as high-quality JPEG.
    
    Args:
        image_path: Path to the original image file.
        face: DetectedFace instance containing bounding box in original image coordinates.
        out_path: Output JPEG path.
        crop_size: Target square dimension (pixels).
        margin_ratio: Extra margin added around the face bounding box (default 35%).
        vertical_shift: Fraction of face height to shift crop box upwards for forehead/hair.
    """
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")

        orig_w, orig_h = img.size
        x1, y1, x2, y2 = face.bbox

        face_w = max(1.0, x2 - x1)
        face_h = max(1.0, y2 - y1)
        side = max(face_w, face_h) * (1.0 + margin_ratio)

        # Clamp side to image dimensions if image is smaller than requested crop
        side = min(side, float(min(orig_w, orig_h)))

        # Center of face
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0 - (face_h * vertical_shift)

        half_side = side / 2.0
        left = cx - half_side
        right = cx + half_side
        top = cy - half_side
        bottom = cy + half_side

        # Shift window so it stays within image boundaries without altering side dimension
        if left < 0:
            shift = -left
            left += shift
            right += shift
        if right > orig_w:
            shift = right - orig_w
            left -= shift
            right -= shift
        if top < 0:
            shift = -top
            top += shift
            bottom += shift
        if bottom > orig_h:
            shift = bottom - orig_h
            top -= shift
            bottom -= shift

        int_left = max(0, int(math.floor(left)))
        int_top = max(0, int(math.floor(top)))
        int_right = min(orig_w, int(math.ceil(right)))
        int_bottom = min(orig_h, int(math.ceil(bottom)))

        side_px = min(max(int_right - int_left, int_bottom - int_top), orig_w, orig_h)
        if int_left + side_px > orig_w:
            int_left = max(0, orig_w - side_px)
        if int_top + side_px > orig_h:
            int_top = max(0, orig_h - side_px)
        int_right = int_left + side_px
        int_bottom = int_top + side_px

        cropped = img.crop((int_left, int_top, int_right, int_bottom))
        cropped = cropped.resize((crop_size, crop_size), Image.Resampling.LANCZOS)
        cropped.save(out_p, format="JPEG", quality=95, subsampling=0, optimize=True)
