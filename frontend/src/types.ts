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
  message: string;
  error?: string | null;
  result_summary?: Record<string, any> | null;
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
}

export interface PhotoInfo {
  photo_id: string;
  file_name: string;
  width?: number;
  height?: number;
  thumb?: string;
}

export type ActiveTab = 'home' | 'progress' | 'people' | 'export' | 'settings';
