"""Face detection, embedding extraction, and quality filtering using InsightFace buffalo_l."""

from __future__ import annotations
from typing import List, Optional, Tuple
import numpy as np
import cv2

from backend.engine.models import FaceDetection, PhotoRecord


class FaceDetector:
    """Detects faces and extracts 512-d normalized embeddings using InsightFace buffalo_l."""

    def __init__(
        self,
        model_name: str = "buffalo_l",
        model_root: Optional[str] = None,
        det_size: Tuple[int, int] = (640, 640),
        min_det_score: float = 0.5,
        min_face_size: int = 64,
        max_yaw: float = 70.0,
        max_image_dim: int = 1600,
        providers: Optional[List[str]] = None,
    ):
        self.model_name = model_name
        self.model_root = model_root
        self.det_size = det_size
        self.min_det_score = min_det_score
        self.min_face_size = min_face_size
        self.max_yaw = max_yaw
        self.max_image_dim = max_image_dim
        self.providers = providers
        self._app = None

    def _init_app(self):
        if self._app is None:
            from insightface.app import FaceAnalysis

            kwargs = {"name": self.model_name}
            if self.model_root:
                kwargs["root"] = self.model_root
            if self.providers:
                kwargs["providers"] = self.providers

            app = FaceAnalysis(**kwargs)
            # ctx_id=0, prepare with detection size
            app.prepare(ctx_id=0, det_size=self.det_size)
            self._app = app

    def detect_and_embed(
        self,
        orig_rgb: np.ndarray,
        photo_id: str,
    ) -> List[FaceDetection]:
        """
        Detect faces on a downscaled copy (longest side 1600 per SPEC),
        scale landmarks back to the original, then align and embed from the
        ORIGINAL-resolution image. Also computes head pose (pitch, yaw, roll).

        Args:
            orig_rgb: HxWx3 RGB numpy array in ORIGINAL resolution
            photo_id: Unique photo identifier

        Returns:
            List of FaceDetection objects with bboxes and landmarks in original coordinates,
            ArcFace embeddings, and 3D head pose.
        """
        self._init_app()

        orig_h, orig_w = orig_rgb.shape[:2]
        orig_bgr = cv2.cvtColor(orig_rgb, cv2.COLOR_RGB2BGR)

        # 1. Downscale for detection if longest side exceeds max_image_dim (1600)
        max_side = max(orig_w, orig_h)
        if max_side > self.max_image_dim:
            scale = max_side / float(self.max_image_dim)
            down_w = max(1, int(round(orig_w / scale)))
            down_h = max(1, int(round(orig_h / scale)))
            down_bgr = cv2.resize(orig_bgr, (down_w, down_h), interpolation=cv2.INTER_AREA)
        else:
            scale = 1.0
            down_bgr = orig_bgr

        # 2. Detect on downscaled copy
        bboxes, kpss = self._app.det_model.detect(down_bgr, max_num=0, metric="default")

        detections: List[FaceDetection] = []
        if bboxes is None or bboxes.shape[0] == 0:
            return detections

        from insightface.app.common import Face

        for i in range(bboxes.shape[0]):
            face_id = f"f_{photo_id}_{i+1:03d}"

            raw_bbox = bboxes[i, 0:4]
            det_score = float(bboxes[i, 4])

            # Scale bounding box back to original coordinates
            orig_bbox = [
                float(raw_bbox[0] * scale),
                float(raw_bbox[1] * scale),
                float(raw_bbox[2] * scale),
                float(raw_bbox[3] * scale),
            ]

            # Scale landmarks back to original coordinates
            orig_kps = None
            if kpss is not None and i < len(kpss):
                orig_kps = kpss[i] * scale

            # 3. Align, embed, and estimate head pose from ORIGINAL-resolution image
            embedding = None
            pose = None
            if orig_kps is not None:
                face_obj = Face(bbox=np.array(orig_bbox), kps=orig_kps, det_score=det_score)

                # Recognition embedding
                if "recognition" in self._app.models:
                    self._app.models["recognition"].get(orig_bgr, face_obj)
                    if hasattr(face_obj, "embedding") and face_obj.embedding is not None:
                        norm = np.linalg.norm(face_obj.embedding)
                        embedding = (face_obj.embedding / norm).astype(np.float32) if norm > 1e-8 else face_obj.embedding.astype(np.float32)

                # 3D Landmark & Pose estimation: [pitch, yaw, roll]
                if "landmark_3d_68" in self._app.models:
                    self._app.models["landmark_3d_68"].get(orig_bgr, face_obj)
                    if hasattr(face_obj, "pose") and face_obj.pose is not None:
                        pose = [float(p) for p in face_obj.pose]

            # 4. Quality filtering: score, min size, and extreme head pose
            face_w = orig_bbox[2] - orig_bbox[0]
            face_h = orig_bbox[3] - orig_bbox[1]
            face_dim = min(face_w, face_h)

            is_good = True
            rejection_reason = None

            yaw = abs(pose[1]) if pose and len(pose) >= 2 else 0.0

            if det_score < self.min_det_score:
                is_good = False
                rejection_reason = f"low_det_score ({det_score:.2f} < {self.min_det_score})"
            elif face_dim < self.min_face_size:
                is_good = False
                rejection_reason = f"face_too_small ({face_dim:.0f}px < {self.min_face_size}px)"
            elif pose is not None and yaw > self.max_yaw:
                is_good = False
                rejection_reason = "extreme_pose"

            landmarks = [[float(pt[0]), float(pt[1])] for pt in orig_kps] if orig_kps is not None else None

            detections.append(
                FaceDetection(
                    face_id=face_id,
                    photo_id=photo_id,
                    bbox=orig_bbox,
                    det_score=det_score,
                    embedding=embedding,
                    landmarks=landmarks,
                    pose=pose,
                    is_good_quality=is_good,
                    rejection_reason=rejection_reason,
                )
            )

        return detections
