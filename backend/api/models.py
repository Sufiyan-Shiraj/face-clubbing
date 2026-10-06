"""Pydantic models and schemas for PhotoSorter FastAPI layer (SPEC 5, BUILD_PLAN Phase 3)."""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class SettingsModel(BaseModel):
    """Clustering parameters and system configuration from SPEC 6.2."""
    input_path: Optional[str] = None
    output_dir: str = "export"
    cache_dir: Optional[str] = None
    work_dir: Optional[str] = None
    distance_threshold: float = 0.50
    min_det_score: float = 0.50
    min_face_size: int = 64
    max_yaw: float = 70.0
    seed_min_det_score: float = 0.70
    seed_min_face_size: int = 64
    seed_max_yaw: float = 60.0
    max_image_dim: int = 1600
    thumb_size: int = 400
    face_crop_size: int = 256
    second_pass_merge: bool = True
    merge_threshold: float = 0.50
    maybe_threshold: float = 0.65
    same_photo_merge_max: float = 0.40
    attach_distance_cap: float = 0.45
    flip_average: bool = False
    include_maybe: bool = False
    event_title: str = "Event Gallery"
    event_subtitle: str = "Photos grouped by person"


class JobStartRequest(BaseModel):
    input_path: Optional[str] = None
    output_dir: Optional[str] = "export"
    cache_dir: Optional[str] = None
    settings: Optional[SettingsModel] = None


class JobStatusResponse(BaseModel):
    job_id: Optional[str] = None
    status: str  # "idle" | "running" | "completed" | "failed" | "cancelled"
    stage: str = "idle"
    current: int = 0
    total: int = 0
    percent: float = 0.0
    current_file: Optional[str] = None
    eta_seconds: Optional[float] = None
    message: str = ""
    error: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None


class FaceItem(BaseModel):
    face_id: str
    photo_id: str
    det_score: Optional[float] = None
    bbox: Optional[List[float]] = None
    file_name: Optional[str] = None


class PersonClusterResponse(BaseModel):
    id: str  # cluster ID display handle (e.g. p001)
    label: Optional[str] = None
    face: str
    photo_ids: List[str]
    photos: List[str]
    photo_count: int
    faces: List[FaceItem]
    anchor_face_ids: List[str]


class UnrecognizedFaceResponse(BaseModel):
    face_id: Optional[str] = None
    photo_id: str
    face: str
    rejection_reason: Optional[str] = None
    det_score: Optional[float] = None
    file_name: Optional[str] = None


class UnrecognizedResponse(BaseModel):
    total_unrecognized_photos: int
    no_face_photos: List[str]
    faces: List[UnrecognizedFaceResponse]


class RankedPairSuggestion(BaseModel):
    person_a_id: str
    person_b_id: str
    person_a_anchors: List[str]
    person_b_anchors: List[str]
    distance: float
    confidence: str  # "medium" | "low"
    reason: str
    person_a_photos: int
    person_b_photos: int
    person_a_best_face: Optional[str] = None
    person_b_best_face: Optional[str] = None


class AmbiguousCandidate(BaseModel):
    candidate_id: str
    distance: float
    anchor_face_ids: List[str]


class AmbiguousFaceSuggestion(BaseModel):
    face_id: str
    photo_id: str
    rejection_reason: str
    top_candidates: List[AmbiguousCandidate]


class SuggestionsResponse(BaseModel):
    maybe_groups_count: int
    maybe_groups: List[Dict[str, Any]]
    possibly_the_same_count: int
    possibly_the_same: List[RankedPairSuggestion]
    ambiguous_faces_count: int
    ambiguous_faces: List[AmbiguousFaceSuggestion]


class EditRequest(BaseModel):
    op: str  # "merge" | "remove" | "assign" | "hide" | "name" | "undo"
    # Handles accepted from UI
    person_id: Optional[str] = None
    person_ids: Optional[List[str]] = None
    # Raw anchor face IDs (if supplied directly by caller or test)
    person: Optional[List[str]] = None
    anchors: Optional[List[List[str]]] = None
    # For remove or assign
    face_id: Optional[str] = None
    photo_id: Optional[str] = None
    # For name
    label: Optional[str] = None


class EditResponse(BaseModel):
    success: bool
    op: str
    message: str
    applied_count: int
    unapplied_edits: List[Dict[str, Any]] = []
    people_count: int
    unrecognized_photos_count: int
    unrecognized_faces_count: int


class RerunRequest(BaseModel):
    settings: Optional[SettingsModel] = None


class RerunResponse(BaseModel):
    success: bool
    applied_count: int
    unapplied_edits: List[Dict[str, Any]]
    people_count: int
    unrecognized_photos_count: int
    unrecognized_faces_count: int
    stats: Dict[str, Any]


class ExportRequest(BaseModel):
    output_dir: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    include_maybe: Optional[bool] = None


class ExportResponse(BaseModel):
    success: bool
    output_dir: str
    files_exported: List[str]
    people_count: int
    photos_count: int
