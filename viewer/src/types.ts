export interface ViewerConfig {
  title: string;
  subtitle?: string;
  logo?: string | null;
  accent?: string;
  font?: string;
  footer?: string;
  show_labels?: boolean;
  include_maybe?: boolean;
  hide_single_photo_default?: boolean;
}

export interface PhotoInfo {
  name: string;
  thumb: string;
  download?: string | null;
  width?: number;
  height?: number;
}

export interface FaceRef {
  face_id?: string;
  photo_id: string;
  file_name?: string;
  det_score?: number;
  bbox?: number[];
}

export interface MaybePhotoRef {
  photo_id: string;
  source_cluster: string;
  distance: number;
}

export interface PersonCluster {
  id: string;
  label?: string | null;
  face: string;
  photo_ids: string[];
  photos?: string[];
  faces?: FaceRef[];
  maybe_photos?: MaybePhotoRef[];
}

export interface UnrecognizedFace {
  face_id?: string;
  photo_id: string;
  file_name?: string;
  face: string;
  rejection_reason?: string;
  det_score?: number;
}

export interface UnrecognizedGroup {
  photo_ids: string[];
  faces: UnrecognizedFace[];
}

export interface PeopleData {
  version: number;
  generated_at: string;
  photos: Record<string, PhotoInfo>;
  people: PersonCluster[];
  unrecognized: UnrecognizedGroup;
}
