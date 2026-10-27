export interface FaceItem {
  face_id: string;
  photo_id: string;
  det_score?: number | null;
  bbox?: number[] | null;
  file_name?: string | null;
}

export interface PersonCluster {
  id: string;
  label?: string | null;
  face: string;
  photo_ids: string[];
  photos: string[];
  photo_count: number;
  faces: FaceItem[];
  anchor_face_ids: string[];
}

export interface UnrecognizedFace {
  face_id?: string | null;
  photo_id: string;
  face: string;
  rejection_reason?: string | null;
  det_score?: number | null;
  file_name?: string | null;
  bbox?: number[] | null;
}

export interface UnrecognizedData {
  total_unrecognized_photos: number;
  no_face_photos: string[];
  faces: UnrecognizedFace[];
}

export interface RankedPairSuggestion {
  person_a_id: string;
  person_b_id: string;
  person_a_anchors: string[];
  person_b_anchors: string[];
  distance: number;
  confidence: 'medium' | 'low';
  reason: string;
  person_a_photos: number;
  person_b_photos: number;
  person_a_best_face?: string | null;
  person_b_best_face?: string | null;
}

export interface AmbiguousCandidate {
  candidate_id: string;
  distance: number;
  anchor_face_ids: string[];
}

export interface AmbiguousFaceSuggestion {
  face_id: string;
  photo_id: string;
  rejection_reason: string;
  top_candidates: AmbiguousCandidate[];
}

export interface MaybeGroup {
  group_id: number;
  clusters: string[];
  cluster_count: number;
  photos_count: number;
  links: Array<{
    cluster_a: string;
    cluster_b: string;
    distance: number;
    cluster_a_photos: number;
    cluster_b_photos: number;
    cluster_a_best_face: string;
    cluster_b_best_face: string;
    reason: string;
  }>;
}

export interface SuggestionsData {
  maybe_groups_count: number;
  maybe_groups: MaybeGroup[];
  possibly_the_same_count: number;
  possibly_the_same: RankedPairSuggestion[];
  ambiguous_faces_count: number;
  ambiguous_faces: AmbiguousFaceSuggestion[];
}

export interface JobStatus {
  job_id?: string | null;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  stage: string;
  current: number;
  total: number;
  percent: number;
  current_file?: string | null;
  eta_seconds?: number | null;
  elapsed_seconds?: number | null;
  start_time?: number | null;
  message: string;
  error?: string | null;
  error_code?: string | null;
  error_title?: string | null;
  plain_language_fix?: string | null;
  diagnostics_report?: string | null;
  result_summary?: Record<string, any> | null;
  recent_faces?: string[];
}

export interface DriveVerifyResult {
  valid: boolean;
  folder_id?: string;
  folder_name?: string;
  has_images?: boolean;
  image_count_preview?: number;
  error_type?: string;
  error_code?: string | null;
  plain_language_fix?: string | null;
  diagnostics_report?: string | null;
  message?: string;
  summary?: Record<string, any>;
}

export interface DiagnosticsReport {
  version: string;
  os_name: string;
  os_release: string;
  architecture: string;
  python_version: string;
  settings_hash: string;
  error_code: string;
  error_title?: string | null;
  plain_language_fix?: string | null;
  sanitized_error?: string | null;
  status: string;
  stage: string;
  counts: {
    total_photos: number;
    people_count: number;
    clustered_faces: number;
    unrecognized_faces: number;
    unrecognized_photos: number;
    edits_count: number;
    drive_images_found: number;
    drive_folders_scanned: number;
    drive_folders_failed: number;
    drive_shortcuts_skipped: number;
    drive_non_images_skipped: number;
  };
  formatted_report: string;
}

export interface EditResponse {
  success: boolean;
  op: string;
  message: string;
  applied_count: number;
  unapplied_edits: Array<Record<string, any>>;
  people_count: number;
  unrecognized_photos_count: number;
  unrecognized_faces_count: number;
}

export interface Settings {
  input_path?: string | null;
  output_dir: string;
  cache_dir?: string | null;
  work_dir?: string | null;
  distance_threshold: number;
  min_det_score: number;
  min_face_size: number;
  max_yaw: number;
  seed_min_det_score: number;
  seed_min_face_size: number;
  seed_max_yaw: number;
  max_image_dim: number;
  thumb_size: number;
  face_crop_size: number;
  second_pass_merge: boolean;
  merge_threshold: number;
  maybe_threshold: number;
  same_photo_merge_max: number;
  attach_distance_cap: number;
  flip_average: boolean;
  include_maybe: boolean;
  event_title: string;
  event_subtitle: string;
  drive_api_key?: string | null;
  drive_api_key_masked?: string | null;
  drive_api_key_configured?: boolean;
  scan_subfolders?: boolean;
  max_subfolder_depth?: number;
  follow_shortcuts?: boolean;
}

export interface PhotoInfo {
  photo_id: string;
  file_name: string;
  width?: number;
  height?: number;
  thumb?: string;
  download?: string;
  faces?: FaceItem[];
  source_exists?: boolean;
  original_path?: string | null;
  source_id?: string | null;
  source_label?: string | null;
}

export interface ScanSourceItem {
  id: string;
  kind?: string;
  type?: 'local' | 'drive' | 'zip' | 'project';
  path_or_url: string;
  label?: string;
  drive_api_key?: string;
  quality?: string;
  status?: string;
  error?: string | null;
  photo_count?: number;
  added_at?: string;
}

export interface ProjectSourcesResponse {
  sources: ScanSourceItem[];
  total_sources: number;
  schema_version: number;
  project_id?: string;
  photo_count?: number;
  photos_by_source?: Record<string, number>;
}

export interface JoinedExistingPersonInfo {
  person_name?: string;
  new_faces_count: number;
  new_photo_ids?: string[];
}

export interface WhatChangedResponse {
  generated_at?: string;
  new_photos_count: number;
  new_photo_ids: string[];
  skipped_duplicate_photos?: number;
  new_people_count: number;
  new_people_ids: string[];
  joined_existing_count: number;
  joined_existing: Record<string, JoinedExistingPersonInfo>;
  existing_people_membership_changed: number;
  new_unrecognized_faces_count: number;
  new_unrecognized_photos_count: number;
}

export interface SnapshotItem {
  snapshot_id: string;
  created_at: string;
  label?: string | null;
  work_dir?: string | null;
  export_dir?: string | null;
  files_saved?: string[];
  counts?: Record<string, number>;
}

export interface UndoSnapshotResponse {
  success: boolean;
  restored_snapshot: Record<string, any>;
  message: string;
}

export interface ProjectItem {
  id: string;
  name: string;
  work_dir: string;
  export_path?: string | null;
  source_description?: string | null;
  schema_version?: number;
  sources?: ScanSourceItem[];
  last_opened: string;
  counts: {
    people: number;
    photos: number;
    unrecognized?: number;
  };
  exists: boolean;
}

export interface OpenProjectResponse {
  success: boolean;
  message: string;
  project: ProjectItem;
  people_count: number;
  photos_count: number;
  unrecognized_faces_count: number;
  applied_edits_count: number;
  read_only: boolean;
  edits_error?: string | null;
}

export type ActiveTab = 'home' | 'progress' | 'people' | 'export' | 'settings';

export interface DirectoryItem {
  name: string;
  path: string;
  modified_time?: string | null;
}

export interface ShortcutItem {
  label: string;
  path: string;
}

export interface BrowseFolderResult {
  current_path: string;
  parent_path?: string | null;
  name: string;
  exists: boolean;
  is_directory: boolean;
  directories: DirectoryItem[];
  shortcuts: ShortcutItem[];
}

export interface ModelStatus {
  model_name: string;
  installed: boolean;
  valid: boolean;
  status: 'ready' | 'missing' | 'update_available' | 'downloading' | 'corrupt';
  target_dir?: string;
  missing_files?: string[];
  installed_files?: string[];
  total_size_bytes?: number;
  version?: string;
  latest_version?: string;
  update_available?: boolean;
  update_message?: string;
  is_downloading?: boolean;
  stage?: string;
  percent?: number;
  current_bytes?: number;
  total_bytes?: number;
  message?: string;
  error?: string | null;
}

declare global {
  interface Window {
    pywebview?: {
      api: {
        select_folder: (title?: string) => Promise<string>;
        select_file: (title?: string) => Promise<string>;
      };
    };
  }
}
