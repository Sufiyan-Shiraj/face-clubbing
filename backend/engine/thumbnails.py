"""Thumbnail generation and representative square face crop extraction."""

from __future__ import annotations
import math
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageOps
import numpy as np

from backend.engine.models import FaceDetection, PersonCluster

# Ensure HEIF support if available
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def compute_face_quality_score(face: FaceDetection) -> float:
    """
    Computes a composite score for representative face selection.
    Favors higher detection score, larger face area, and frontal poses.
    """
    x1, y1, x2, y2 = face.bbox
    w = max(1.0, x2 - x1)
    h = max(1.0, y2 - y1)
    area = w * h

    # Area component (logarithmic scaling)
    area_score = math.log10(max(100.0, area))

    # Base score combines det_score and area
    score = face.det_score * 3.0 + area_score

    # Frontalness bonus if 5-point landmarks exist:
    # [left_eye, right_eye, nose, left_mouth, right_mouth]
    if face.landmarks and len(face.landmarks) >= 5:
        le, re, nose, lm, rm = face.landmarks[:5]
        eye_dx = re[0] - le[0]
        eye_dy = re[1] - le[1]
        eye_dist = math.hypot(eye_dx, eye_dy)

        if eye_dist > 1e-4:
            # 1. Roll penalty (eyes not horizontal)
            roll_ratio = abs(eye_dy) / eye_dist
            roll_penalty = min(2.0, roll_ratio * 4.0)

            # 2. Yaw symmetry: nose x relative to eye midpoint
            eye_mid_x = (le[0] + re[0]) / 2.0
            yaw_ratio = abs(nose[0] - eye_mid_x) / eye_dist
            yaw_penalty = min(2.0, yaw_ratio * 4.0)

            score -= (roll_penalty + yaw_penalty)

    return score


def select_representative_face(faces: List[FaceDetection]) -> FaceDetection:
    """Pick the highest scoring face in a cluster to represent the person."""
    if not faces:
        raise ValueError("Cannot select representative face from empty face list.")
    return max(faces, key=compute_face_quality_score)


class ThumbnailGenerator:
    """Generates photo thumbnails and square face crops for static export."""

    def __init__(self, thumb_size: int = 400, face_crop_size: int = 256):
        self.thumb_size = thumb_size
        self.face_crop_size = face_crop_size

    def generate_photo_thumbnail_from_image(
        self,
        img: Image.Image,
        output_path: Path | str,
        quality: int = 80,
    ) -> Tuple[int, int]:
        """
        Creates a thumbnail directly from an in-memory PIL Image.
        Returns (thumb_width, thumb_height).
        """
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        w, h = img.size
        max_side = max(w, h)
        if max_side > self.thumb_size:
            scale = max_side / self.thumb_size
            tw = max(1, int(round(w / scale)))
            th = max(1, int(round(h / scale)))
            img_thumb = img.resize((tw, th), Image.Resampling.LANCZOS)
        else:
            img_thumb = img
            tw, th = w, h

        img_thumb.save(out_p, format="JPEG", quality=quality, optimize=True)
        return tw, th

    def generate_photo_thumbnail(
        self,
        image_path: Path | str,
        output_path: Path | str,
        quality: int = 80,
    ) -> Tuple[int, int]:
        """
        Creates a thumbnail with max dimension capped at self.thumb_size.
        Returns (thumb_width, thumb_height).
        """
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")
            return self.generate_photo_thumbnail_from_image(img, output_path, quality)

    def generate_square_face_crop_from_image(
        self,
        img: Image.Image,
        bbox: List[float],
        output_path: Path | str,
        margin_factor: float = 1.45,
        quality: int = 88,
    ) -> None:
        """
        Generates a centered, square crop of the face with margin directly from a PIL Image.
        Handles image boundaries cleanly without aspect-ratio distortion or stitching artifacts.
        """
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        img_w, img_h = img.size
        x1, y1, x2, y2 = bbox
        w = max(1.0, x2 - x1)
        h = max(1.0, y2 - y1)

        # Center with slight upward bias to include hair/forehead
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0 - 0.06 * h

        side = max(w, h) * margin_factor

        # Calculate bounding box
        half = side / 2.0
        left = cx - half
        top = cy - half
        right = cx + half
        bottom = cy + half

        # Shift crop window so it stays within image boundaries without altering side dimension
        if left < 0:
            shift = -left
            left += shift
            right += shift
        if right > img_w:
            shift = right - img_w
            left -= shift
            right -= shift
        if top < 0:
            shift = -top
            top += shift
            bottom += shift
        if bottom > img_h:
            shift = bottom - img_h
            top -= shift
            bottom -= shift

        int_left = int(math.floor(left))
        int_top = int(math.floor(top))
        int_right = int(math.ceil(right))
        int_bottom = int(math.ceil(bottom))

        # Enforce exact 1:1 square integer dimensions
        side_px = max(int_right - int_left, int_bottom - int_top)
        int_right = int_left + side_px
        int_bottom = int_top + side_px

        # Extract valid overlap
        val_left = max(0, int_left)
        val_top = max(0, int_top)
        val_right = min(img_w, int_right)
        val_bottom = min(img_h, int_bottom)

        if val_right <= val_left or val_bottom <= val_top:
            # Fallback if entirely out of bounds
            cropped = img.crop((0, 0, min(img_w, img_h), min(img_w, img_h)))
        else:
            patch = img.crop((val_left, val_top, val_right, val_bottom))
            if patch.size == (side_px, side_px):
                cropped = patch
            else:
                # Square canvas with edge padding to avoid stretching/stitching
                cropped = Image.new("RGB", (side_px, side_px), (0, 0, 0))
                offset_x = val_left - int_left
                offset_y = val_top - int_top
                cropped.paste(patch, (offset_x, offset_y))

        cropped_resized = cropped.resize(
            (self.face_crop_size, self.face_crop_size),
            Image.Resampling.LANCZOS,
        )
        cropped_resized.save(out_p, format="JPEG", quality=quality, optimize=True)

    def generate_square_face_crop(
        self,
        image_path: Path | str,
        bbox: List[float],
        output_path: Path | str,
        margin_factor: float = 1.45,
        quality: int = 88,
    ) -> None:
        """
        Generates a centered, square crop of the face with margin from file path.
        """
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")
            self.generate_square_face_crop_from_image(img, bbox, output_path, margin_factor, quality)
