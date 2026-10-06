"""Image loading, EXIF orientation handling, and downscaling."""

from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
from PIL import Image, ImageOps

# Attempt to register HEIF opener for iPhone HEIC images
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


class ImageLoader:
    """Loads images, corrects EXIF orientation, and downscales for face detection."""

    def __init__(self, max_dimension: int = 1600):
        self.max_dimension = max_dimension

    def load_image(self, file_path: Path | str) -> Tuple[np.ndarray, int, int, Image.Image]:
        """
        Loads an image from disk in ORIGINAL resolution (after EXIF transpose).

        Returns:
            rgb_original: np.ndarray (RGB format in original resolution)
            orig_width: int (after EXIF transpose)
            orig_height: int (after EXIF transpose)
            pil_image: PIL Image object for downstream thumbnailing/cropping
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        # Open and transpose EXIF
        raw_img = Image.open(path)
        transposed_img = ImageOps.exif_transpose(raw_img)
        if transposed_img.mode != "RGB":
            transposed_img = transposed_img.convert("RGB")

        orig_w, orig_h = transposed_img.size
        rgb_array = np.array(transposed_img)

        return rgb_array, orig_w, orig_h, transposed_img
