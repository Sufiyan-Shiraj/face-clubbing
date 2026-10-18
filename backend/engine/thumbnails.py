"""Thumbnail generation and representative square face crop extraction."""

from __future__ import annotations
import math
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageOps, ImageFilter
import numpy as np
import cv2

from backend.engine.models import FaceDetection, PersonCluster

# Ensure HEIF support if available
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def compute_image_sharpness(img_input: Path | str | Image.Image | np.ndarray) -> float:
    """Computes the sharpness score of an image or crop using variance of Laplacian.
    Higher values indicate sharp, in-focus images, while lower values (< 30) indicate blurriness."""
    try:
        if isinstance(img_input, (str, Path)):
            p = Path(img_input)
            if not p.exists():
                return 0.0
            gray = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                return 0.0
        elif isinstance(img_input, Image.Image):
            gray = np.array(img_input.convert("L"))
        elif isinstance(img_input, np.ndarray):
            if img_input.ndim == 3:
                gray = cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY if img_input.shape[2] == 3 else cv2.COLOR_RGB2GRAY)
            else:
                gray = img_input
        else:
            return 0.0
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())
    except Exception:
        return 0.0


def compute_face_quality_score(
    face: FaceDetection,
    crop_path: Optional[Path | str] = None,
) -> float:
    """
    Computes a composite quality score for selecting an optimal, high-quality avatar for a person.
    Prioritizes:
      1. Resolution & Face Size: strongly rewards large faces; penalizes tiny distant faces (< 70px)
      2. Detection Confidence: favors high detector certainty (det_score)
      3. Flattering Pose: rewards frontal eye-level view; penalizes severe yaw/profile (> 25°), pitch (> 15°), or tilted roll (> 8°)
      4. Facial Symmetry: rewards horizontal eyes, centered nose, and upright proportions
      5. Sharpness / In-focus: rewards in-focus faces and penalizes motion-blurred or soft faces
      6. Quality Flag: penalizes faces marked as poor quality or rejected
    """
    x1, y1, x2, y2 = face.bbox
    w = max(1.0, x2 - x1)
    h = max(1.0, y2 - y1)
    min_dim = min(w, h)

    # 1. Size & Resolution (progressive square root curve)
    size_score = math.sqrt(min(min_dim, 400.0)) * 1.6
    if min_dim < 70.0:
        size_score -= (70.0 - min_dim) * 0.35

    # 2. Confidence component (quadratic scaling)
    conf_score = (face.det_score ** 2) * 15.0
    if face.det_score < 0.65:
        conf_score -= (0.65 - face.det_score) * 20.0

    # 3. 3D Head Pose (pitch, yaw, roll)
    pose_score = 0.0
    if face.pose and len(face.pose) >= 3:
        pitch, yaw, roll = face.pose[:3]
        abs_yaw = abs(yaw)
        abs_pitch = abs(pitch)
        abs_roll = abs(roll)

        if abs_yaw <= 10.0:
            pose_score += 4.0
        elif abs_yaw <= 20.0:
            pose_score += 2.0
        elif abs_yaw > 25.0:
            pose_score -= min(14.0, (abs_yaw - 20.0) * 0.6)

        if abs_pitch <= 10.0:
            pose_score += 2.0
        elif abs_pitch > 15.0:
            pose_score -= min(8.0, (abs_pitch - 12.0) * 0.4)

        if abs_roll <= 6.0:
            pose_score += 2.0
        elif abs_roll > 10.0:
            pose_score -= min(8.0, (abs_roll - 8.0) * 0.5)

    # 4. 5-point facial landmarks geometry & symmetry:
    if face.landmarks and len(face.landmarks) >= 5:
        le, re, nose, lm, rm = face.landmarks[:5]
        eye_dx = re[0] - le[0]
        eye_dy = re[1] - le[1]
        eye_dist = math.hypot(eye_dx, eye_dy)

        if eye_dist > 1e-4:
            tilt_ratio = abs(eye_dy) / eye_dist
            if tilt_ratio > 0.12:
                pose_score -= min(6.0, (tilt_ratio - 0.12) * 20.0)

            d_left = abs(nose[0] - le[0])
            d_right = abs(re[0] - nose[0])
            max_d = max(d_left, d_right)
            if max_d > 1e-4:
                symmetry = min(d_left, d_right) / max_d
                if symmetry > 0.7:
                    pose_score += (symmetry - 0.7) * 5.0
                elif symmetry < 0.5:
                    pose_score -= (0.5 - symmetry) * 10.0

            mouth_mid_y = (lm[1] + rm[1]) / 2.0
            if mouth_mid_y < nose[1]:
                pose_score -= 20.0

    # 5. Sharpness & Clarity
    sharpness = getattr(face, "sharpness", None)
    if sharpness is None and crop_path:
        sharpness = compute_image_sharpness(crop_path)
        face.sharpness = sharpness

    sharpness_score = 0.0
    if sharpness is not None and sharpness > 0.0:
        if sharpness < 35.0:
            sharpness_score -= min(10.0, (35.0 - sharpness) * 0.3)
        else:
            sharpness_score += min(10.0, math.log10(max(1.0, sharpness)) * 3.5)

    # 6. Quality flag & rejection penalty
    quality_penalty = 0.0
    if not getattr(face, "is_good_quality", True):
        quality_penalty += 25.0
    if getattr(face, "rejection_reason", None):
        quality_penalty += 15.0

    return size_score + conf_score + pose_score + sharpness_score - quality_penalty


def select_representative_face(
    faces: List[FaceDetection],
    cache_crops: Optional[Path | str] = None,
) -> FaceDetection:
    """Pick the highest scoring face in a cluster to represent the person."""
    if not faces:
        raise ValueError("Cannot select representative face from empty face list.")
    if len(faces) == 1:
        return faces[0]
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
        quality: int = 95,
    ) -> None:
        """
        Generates a centered, square crop of the face with margin directly from a PIL Image.
        Handles image boundaries cleanly without aspect-ratio distortion or stretching artifacts.
        Saves with 4:4:4 color subsampling (subsampling=0) and high quality for crystal-clear avatars.
        """
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        img_w, img_h = img.size
        x1, y1, x2, y2 = bbox
        w = max(1.0, x2 - x1)
        h = max(1.0, y2 - y1)

        # Center with slight upward bias to include hair/forehead
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0 - 0.07 * h

        side = max(w, h) * margin_factor
        # Prevent crop box from exceeding full image dimensions
        side = min(side, float(min(img_w, img_h)))

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

        int_left = max(0, int(math.floor(left)))
        int_top = max(0, int(math.floor(top)))
        int_right = min(img_w, int(math.ceil(right)))
        int_bottom = min(img_h, int(math.ceil(bottom)))

        # Enforce exact 1:1 square integer dimensions within image bounds
        side_px = min(max(int_right - int_left, int_bottom - int_top), img_w, img_h)
        if int_left + side_px > img_w:
            int_left = max(0, img_w - side_px)
        if int_top + side_px > img_h:
            int_top = max(0, img_h - side_px)
        int_right = int_left + side_px
        int_bottom = int_top + side_px

        cropped = img.crop((int_left, int_top, int_right, int_bottom))

        cropped_resized = cropped.resize(
            (self.face_crop_size, self.face_crop_size),
            Image.Resampling.LANCZOS,
        )

        # Subtle unsharp mask when upscaling to maintain crisp facial detail
        if side_px < self.face_crop_size:
            cropped_resized = cropped_resized.filter(
                ImageFilter.UnsharpMask(radius=1.0, percent=35, threshold=2)
            )

        # Save with quality=95 and subsampling=0 (4:4:4 lossless chroma, zero color bleeding)
        cropped_resized.save(
            out_p,
            format="JPEG",
            quality=quality,
            subsampling=0,
            optimize=True,
        )

    def generate_square_face_crop(
        self,
        image_path: Path | str,
        bbox: List[float],
        output_path: Path | str,
        margin_factor: float = 1.45,
        quality: int = 95,
    ) -> None:
        """
        Generates a centered, square crop of the face with margin from file path.
        """
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")
            self.generate_square_face_crop_from_image(img, bbox, output_path, margin_factor, quality)
