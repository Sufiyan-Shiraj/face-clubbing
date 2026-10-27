import uuid
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class ScanSourceItem(BaseModel):
    id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:6]}")
    kind: str = "local"  # "local" | "zip" | "drive" | "project"
    type: Optional[str] = None
    path_or_url: str
    label: Optional[str] = None
    quality: Optional[str] = "original"
    status: str = "pending"  # "pending" | "scanning" | "completed" | "failed"
    error: Optional[str] = None
    photo_count: int = 0
    added_at: Optional[str] = None


class ProjectManifestV2(BaseModel):
    schema_version: int = 2
    project_name: str
    created_at: str
    settings_hash: Optional[str] = None
    sources: List[ScanSourceItem] = Field(default_factory=list)
    total_photos: int = 0
    total_people: int = 0
    photo_origins: Dict[str, str] = Field(default_factory=dict)


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
    drive_api_key: Optional[str] = None
    drive_api_key_masked: Optional[str] = None
    drive_api_key_configured: bool = False
    scan_subfolders: bool = True
    max_subfolder_depth: int = 5
    follow_shortcuts: bool = False


class JobStartRequest(BaseModel):
    input_path: Optional[str] = None
    source_path: Optional[str] = None
    drive_folder: Optional[str] = None
    drive_api_key: Optional[str] = None
    sources: Optional[List[ScanSourceItem]] = None
    output_dir: Optional[str] = "export"
    cache_dir: Optional[str] = None
    settings: Optional[SettingsModel] = None
    keep_edits: Optional[bool] = False
    replay_edits: Optional[bool] = False
    scan_subfolders: Optional[bool] = None
    max_subfolder_depth: Optional[int] = None
    follow_shortcuts: Optional[bool] = None


class DriveVerifyRequest(BaseModel):
    drive_folder: str
    drive_api_key: Optional[str] = None
    scan_subfolders: Optional[bool] = None
    max_subfolder_depth: Optional[int] = None
    follow_shortcuts: Optional[bool] = None


class DriveVerifyResponse(BaseModel):
    valid: bool
    folder_id: Optional[str] = None
    folder_name: Optional[str] = None
    has_images: bool = False
    image_count_preview: int = 0
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    plain_language_fix: Optional[str] = None
    diagnostics_report: Optional[str] = None
    message: str
    summary: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    job_id: Optional[str] = None
    status: str  # "idle" | "running" | "completed" | "failed" | "cancelled"
    stage: str = "idle"
    current: int = 0
    total: int = 0
    percent: float = 0.0
    progress: float = 0.0
    current_file: Optional[str] = None
    eta_seconds: Optional[float] = None
    elapsed_seconds: Optional[float] = None
    start_time: Optional[float] = None
    message: str = ""
    error: Optional[str] = None
    error_code: Optional[str] = None
    error_title: Optional[str] = None
    plain_language_fix: Optional[str] = None
    diagnostics_report: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    recent_faces: List[str] = Field(default_factory=list)


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
    bbox: Optional[List[float]] = None


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
    face_ids: Optional[List[str]] = None
    photo_id: Optional[str] = None
    photo_ids: Optional[List[str]] = None
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
    theme: Optional[str] = "t-dark"


class ExportResponse(BaseModel):
    success: bool
    output_dir: str
    files_exported: List[str]
    people_count: int
    photos_count: int


class DirectoryItem(BaseModel):
    name: str
    path: str
    modified_time: Optional[str] = None


class ShortcutItem(BaseModel):
    label: str
    path: str


class BrowseFolderResponse(BaseModel):
    current_path: str
    parent_path: Optional[str] = None
    name: str
    exists: bool = True
    is_directory: bool = True
    directories: List[DirectoryItem] = Field(default_factory=list)
    shortcuts: List[ShortcutItem] = Field(default_factory=list)


class MkdirRequest(BaseModel):
    parent_path: str
    folder_name: str


class SelectDialogRequest(BaseModel):
    initial_dir: Optional[str] = None
    title: Optional[str] = None


class SelectDialogResponse(BaseModel):
    selected: Optional[str] = None
    cancelled: bool = False


class ProjectItem(BaseModel):
    id: str
    name: str
    work_dir: str
    export_path: Optional[str] = None
    source_description: str
    last_opened: str
    counts: Dict[str, int] = Field(default_factory=dict)
    exists: bool = True
    schema_version: int = 1
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class OpenProjectRequest(BaseModel):
    project_id: Optional[str] = None
    work_dir: Optional[str] = None
    export_path: Optional[str] = None


class OpenProjectResponse(BaseModel):
    success: bool
    project: ProjectItem
    people_count: int
    photos_count: int
    unrecognized_faces_count: int
    read_only: bool = False
    edits_error: Optional[str] = None
    applied_edits_count: int = 0
    unapplied_edits: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectSourcesResponse(BaseModel):
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    total_sources: int = 0
    schema_version: int = 2


class CheckEditsResponse(BaseModel):
    has_saved_edits: bool = False
    saved_edits_count: int = 0
    work_dir: str = ""
    is_different_source: bool = False
    default_action: str = "fresh"  # "keep" or "fresh"
    previous_source: Optional[str] = None
    message: str = ""


class ModelCheckUpdateRequest(BaseModel):
    simulate: bool = False


class ModelDownloadRequest(BaseModel):
    force: bool = False


class ModelStatusResponse(BaseModel):
    model_name: str = "buffalo_l"
    installed: bool = False
    valid: bool = False
    status: str = "missing"
    target_dir: Optional[str] = None
    missing_files: List[str] = Field(default_factory=list)
    installed_files: List[str] = Field(default_factory=list)
    total_size_bytes: int = 0
    version: str = "1.0.0"
    latest_version: str = "1.0.0"
    update_available: bool = False
    update_message: Optional[str] = None
    is_downloading: bool = False
    stage: str = "idle"
    percent: float = 0.0
    current_bytes: int = 0
    error: Optional[str] = None


class AddSourceRequest(BaseModel):
    source: ScanSourceItem
    drive_api_key: Optional[str] = None
    frozen_mode: bool = True


class WhatChangedResponse(BaseModel):
    generated_at: str = ""
    new_photos_count: int = 0
    new_photo_ids: List[str] = Field(default_factory=list)
    skipped_duplicate_photos: int = 0
    new_people_count: int = 0
    new_people_ids: List[str] = Field(default_factory=list)
    joined_existing_count: int = 0
    joined_existing: Dict[str, Any] = Field(default_factory=dict)
    existing_people_membership_changed: int = 0
    new_unrecognized_faces_count: int = 0
    new_unrecognized_photos_count: int = 0


class SnapshotItem(BaseModel):
    snapshot_id: str
    created_at: str
    label: Optional[str] = None
    work_dir: Optional[str] = None
    export_dir: Optional[str] = None
    files_saved: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)


class UndoSnapshotResponse(BaseModel):
    success: bool
    restored_snapshot: Dict[str, Any] = Field(default_factory=dict)
    message: str
