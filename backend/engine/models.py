"""Data structures and schemas for the PhotoSorter engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class FaceDetection:
    """Represents a single detected face in an image."""
    face_id: str
    photo_id: str
    bbox: List[float]  # [x1, y1, x2, y2] in original image coordinates
    det_score: float
    embedding: Optional[np.ndarray] = None  # 512-d normalized embedding
    embedding_flipped: Optional[np.ndarray] = None  # 512-d normalized flipped embedding
    landmarks: Optional[List[List[float]]] = None  # 5 facial landmarks
    pose: Optional[List[float]] = None  # [pitch, yaw, roll] in degrees
    is_good_quality: bool = True
    rejection_reason: Optional[str] = None
    cluster_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "face_id": self.face_id,
            "photo_id": self.photo_id,
            "bbox": self.bbox,
            "det_score": float(self.det_score),
            "is_good_quality": self.is_good_quality,
            "rejection_reason": self.rejection_reason,
            "cluster_id": self.cluster_id,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "embedding_flipped": self.embedding_flipped.tolist() if self.embedding_flipped is not None else None,
            "landmarks": self.landmarks,
            "pose": self.pose,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FaceDetection:
        emb = data.get("embedding")
        if emb is not None:
            emb = np.array(emb, dtype=np.float32)
        emb_flipped = data.get("embedding_flipped")
        if emb_flipped is not None:
            emb_flipped = np.array(emb_flipped, dtype=np.float32)
        return cls(
            face_id=data["face_id"],
            photo_id=data["photo_id"],
            bbox=data["bbox"],
            det_score=float(data["det_score"]),
            embedding=emb,
            embedding_flipped=emb_flipped,
            landmarks=data.get("landmarks"),
            pose=data.get("pose"),
            is_good_quality=data.get("is_good_quality", True),
            rejection_reason=data.get("rejection_reason"),
            cluster_id=data.get("cluster_id"),
        )


@dataclass
class PhotoRecord:
    """Represents an indexed photo and its detected faces."""
    photo_id: str
    original_path: str
    file_name: str
    width: int
    height: int
    download_url: Optional[str] = None
    faces: List[FaceDetection] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "photo_id": self.photo_id,
            "original_path": self.original_path,
            "file_name": self.file_name,
            "width": self.width,
            "height": self.height,
            "download_url": self.download_url,
            "faces": [f.to_dict() for f in self.faces],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PhotoRecord:
        faces = [FaceDetection.from_dict(f) for f in data.get("faces", [])]
        return cls(
            photo_id=data["photo_id"],
            original_path=data["original_path"],
            file_name=data["file_name"],
            width=data["width"],
            height=data["height"],
            download_url=data.get("download_url"),
            faces=faces,
        )


@dataclass
class PersonCluster:
    """A cluster of photos associated with a detected person."""
    id: str  # e.g., 'p001'
    label: Optional[str] = None
    face_path: str = ""  # e.g., 'faces/p001.jpg'
    rep_face: Optional[FaceDetection] = None
    photo_ids: List[str] = field(default_factory=list)
    faces: List[FaceDetection] = field(default_factory=list)
    maybe_photos: List[Dict[str, Any]] = field(default_factory=list)
    merged_from: List[str] = field(default_factory=list)
    merged_from_numbering: str = ""

    @property
    def photos(self) -> List[str]:
        return self.photo_ids


@dataclass
class UnrecognizedGroup:
    """Photos with no detected faces or faces below quality thresholds."""
    photo_ids: List[str] = field(default_factory=list)
    faces: List[Dict[str, str]] = field(default_factory=list)  # [{"photo_id": ..., "face": "faces/u001.jpg"}]


@dataclass
class EngineResult:
    """The complete result of an engine clustering run."""
    photos: Dict[str, PhotoRecord]
    people: List[PersonCluster]
    unrecognized: UnrecognizedGroup
    distance_threshold: float
    id_map: Dict[str, Any] = field(default_factory=dict)

