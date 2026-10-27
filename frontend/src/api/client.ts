import {
  JobStatus,
  PersonCluster,
  UnrecognizedData,
  SuggestionsData,
  EditResponse,
  Settings,
  PhotoInfo,
  DriveVerifyResult,
  BrowseFolderResult,
  ProjectItem,
  OpenProjectResponse,
  ModelStatus,
  ScanSourceItem,
  ProjectSourcesResponse,
  WhatChangedResponse,
  SnapshotItem,
  UndoSnapshotResponse,
} from '../types';

const BASE_URL = '/api';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!resp.ok) {
    let errorDetail = resp.statusText;
    try {
      const errJson = await resp.json();
      if (errJson && errJson.detail) errorDetail = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export const api = {
  async getHealth(): Promise<{ status: string; version: string }> {
    return fetchJson(`${BASE_URL}/health`);
  },

  async getJobStatus(): Promise<JobStatus> {
    return fetchJson(`${BASE_URL}/jobs/status`);
  },

  async startJob(
    inputPath?: string,
    driveFolderOrOutputDir?: string,
    driveApiKey?: string,
    outputDir: string = 'export',
    keepEdits?: boolean,
    scanOptions?: { scan_subfolders?: boolean; max_subfolder_depth?: number; follow_shortcuts?: boolean },
    sources?: ScanSourceItem[]
  ): Promise<JobStatus> {
    let driveFolder: string | undefined = undefined;
    let apiKey: string | undefined = driveApiKey;
    let actualOutputDir: string = outputDir || 'export';

    if (driveFolderOrOutputDir) {
      if (
        driveFolderOrOutputDir.includes('drive.google.com') ||
        driveFolderOrOutputDir.startsWith('http://') ||
        driveFolderOrOutputDir.startsWith('https://') ||
        !inputPath
      ) {
        driveFolder = driveFolderOrOutputDir;
      } else if (driveFolderOrOutputDir === 'export' || !driveApiKey) {
        actualOutputDir = driveFolderOrOutputDir;
      } else {
        driveFolder = driveFolderOrOutputDir;
      }
    }

    if (
      actualOutputDir.includes('drive.google.com') ||
      actualOutputDir.startsWith('http://') ||
      actualOutputDir.startsWith('https://')
    ) {
      if (!driveFolder) driveFolder = actualOutputDir;
      actualOutputDir = 'export';
    }

    return fetchJson(`${BASE_URL}/jobs/start`, {
      method: 'POST',
      body: JSON.stringify({
        input_path: driveFolder ? undefined : (inputPath || undefined),
        drive_folder: driveFolder || undefined,
        drive_api_key: apiKey || undefined,
        output_dir: actualOutputDir || 'export',
        keep_edits: !!keepEdits,
        scan_subfolders: scanOptions?.scan_subfolders,
        max_subfolder_depth: scanOptions?.max_subfolder_depth,
        follow_shortcuts: scanOptions?.follow_shortcuts,
        ...(sources && sources.length > 0 ? { sources } : {}),
      }),
    });
  },

  async cancelJob(): Promise<JobStatus> {
    return fetchJson(`${BASE_URL}/jobs/cancel`, {
      method: 'POST',
    });
  },

  async verifyDriveFolder(
    driveFolder: string,
    driveApiKey?: string,
    scanOptions?: { scan_subfolders?: boolean; max_subfolder_depth?: number; follow_shortcuts?: boolean }
  ): Promise<DriveVerifyResult> {
    return fetchJson(`${BASE_URL}/drive/verify`, {
      method: 'POST',
      body: JSON.stringify({
        drive_folder: driveFolder,
        drive_api_key: driveApiKey || undefined,
        scan_subfolders: scanOptions?.scan_subfolders,
        max_subfolder_depth: scanOptions?.max_subfolder_depth,
        follow_shortcuts: scanOptions?.follow_shortcuts,
      }),
    });
  },

  subscribeProgress(
    onMessage: (status: JobStatus) => void,
    onError?: (err: any) => void
  ): () => void {
    let eventSource: EventSource | null = null;
    let isClosed = false;
    let reconnectTimeout: any = null;
    let retryCount = 0;
    const MAX_RETRIES = 3;

    const connect = () => {
      if (isClosed) return;
      if (retryCount >= MAX_RETRIES) {
        if (onError) onError(new Error("Progress subscription paused after maximum retries."));
        return;
      }
      try {
        eventSource = new EventSource(`${BASE_URL}/jobs/progress`);
        eventSource.onopen = () => {
          retryCount = 0;
        };
        eventSource.onmessage = (event) => {
          retryCount = 0;
          try {
            const data = JSON.parse(event.data);
            onMessage(data);
          } catch (err) {
            if (onError) onError(err);
          }
        };
        eventSource.onerror = (err) => {
          if (onError) onError(err);
          if (eventSource) {
            eventSource.close();
            eventSource = null;
          }
          if (!isClosed) {
            retryCount++;
            if (retryCount < MAX_RETRIES) {
              reconnectTimeout = setTimeout(connect, 2000 * retryCount);
            }
          }
        };
      } catch (err) {
        if (onError) onError(err);
        if (!isClosed) {
          retryCount++;
          if (retryCount < MAX_RETRIES) {
            reconnectTimeout = setTimeout(connect, 2000 * retryCount);
          }
        }
      }
    };

    connect();

    return () => {
      isClosed = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    };
  },

  async getPeople(): Promise<PersonCluster[]> {
    return fetchJson(`${BASE_URL}/people`);
  },

  async getUnrecognized(): Promise<UnrecognizedData> {
    return fetchJson(`${BASE_URL}/unrecognized`);
  },

  async getSuggestions(): Promise<SuggestionsData> {
    return fetchJson(`${BASE_URL}/suggestions`);
  },

  async getPhotos(): Promise<Record<string, PhotoInfo>> {
    return fetchJson(`${BASE_URL}/photos`);
  },

  async applyEdit(req: {
    op: 'merge' | 'remove' | 'assign' | 'hide' | 'name' | 'undo';
    person_id?: string | null;
    person_ids?: string[];
    face_id?: string;
    face_ids?: string[];
    photo_id?: string;
    photo_ids?: string[];
    label?: string;
    anchors?: string[][];
  }): Promise<EditResponse> {
    return fetchJson(`${BASE_URL}/edits`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  async mergePeople(personIds: string[]): Promise<EditResponse> {
    return this.applyEdit({
      op: 'merge',
      person_ids: personIds,
    });
  },

  async removeFace(personId: string, faceId: string): Promise<EditResponse> {
    return this.applyEdit({
      op: 'remove',
      person_id: personId,
      face_id: faceId,
    });
  },

  async removePhoto(personId: string, photoId: string): Promise<EditResponse> {
    return this.applyEdit({
      op: 'remove',
      person_id: personId,
      photo_id: photoId,
    });
  },

  async assignFace(faceId: string, personId?: string | null): Promise<EditResponse> {
    return this.applyEdit({
      op: 'assign',
      face_id: faceId,
      person_id: personId || null,
    });
  },

  async assignFaces(faceIds: string[], personId?: string | null): Promise<EditResponse> {
    return this.applyEdit({
      op: 'assign',
      face_ids: faceIds,
      person_id: personId || null,
    });
  },

  async assignPhotos(photoIds: string[], personId?: string | null): Promise<EditResponse> {
    return this.applyEdit({
      op: 'assign',
      photo_ids: photoIds,
      person_id: personId || null,
    });
  },

  async hidePerson(personId: string): Promise<EditResponse> {
    return this.applyEdit({
      op: 'hide',
      person_id: personId,
    });
  },

  async namePerson(personId: string, label: string): Promise<EditResponse> {
    return this.applyEdit({
      op: 'name',
      person_id: personId,
      label,
    });
  },

  async undo(): Promise<EditResponse> {
    return this.applyEdit({
      op: 'undo',
    });
  },

  async rerun(settingsOverride?: Partial<Settings>): Promise<{
    success: boolean;
    applied_count: number;
    unapplied_edits: Array<Record<string, any>>;
    people_count: number;
    unrecognized_photos_count: number;
    unrecognized_faces_count: number;
    stats: Record<string, any>;
  }> {
    return fetchJson(`${BASE_URL}/rerun`, {
      method: 'POST',
      body: JSON.stringify({ settings: settingsOverride }),
    });
  },

  async exportBundle(options: {
    output_dir?: string;
    title?: string;
    subtitle?: string;
    include_maybe?: boolean;
    theme?: string;
  }): Promise<{
    success: boolean;
    output_dir: string;
    files_exported: string[];
    people_count: number;
    photos_count: number;
  }> {
    return fetchJson(`${BASE_URL}/export`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  },

  async getSettings(): Promise<Settings> {
    return fetchJson(`${BASE_URL}/settings`);
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    return fetchJson(`${BASE_URL}/settings`, {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  },

  async browseFolder(path?: string): Promise<BrowseFolderResult> {
    const q = path ? `?path=${encodeURIComponent(path)}` : '';
    return fetchJson(`${BASE_URL}/fs/browse${q}`);
  },

  async createFolder(parentPath: string, folderName: string): Promise<BrowseFolderResult> {
    return fetchJson(`${BASE_URL}/fs/mkdir`, {
      method: 'POST',
      body: JSON.stringify({ parent_path: parentPath, folder_name: folderName }),
    });
  },

  async openFolderDialog(initialDir?: string): Promise<{ selected: string | null; cancelled: boolean }> {
    return fetchJson(`${BASE_URL}/fs/select-dialog`, {
      method: 'POST',
      body: JSON.stringify({ initial_dir: initialDir || undefined }),
    });
  },

  async getRecentProjects(): Promise<ProjectItem[]> {
    return fetchJson(`${BASE_URL}/projects`);
  },

  async openProject(req: {
    project_id?: string;
    work_dir?: string;
    export_path?: string;
  }): Promise<OpenProjectResponse> {
    return fetchJson(`${BASE_URL}/projects/open`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  async removeProject(projectId: string): Promise<{ success: boolean; message: string }> {
    return fetchJson(`${BASE_URL}/projects/${encodeURIComponent(projectId)}`, {
      method: 'DELETE',
    });
  },

  async newProject(): Promise<{ success: boolean; message: string }> {
    return fetchJson(`${BASE_URL}/projects/new`, {
      method: 'POST',
    });
  },

  async getActiveProject(): Promise<{ active: boolean; name?: string; people_count: number; photos_count: number }> {
    return fetchJson(`${BASE_URL}/projects/active`);
  },

  async getProjectSources(): Promise<ProjectSourcesResponse> {
    return fetchJson(`${BASE_URL}/project/sources`);
  },

  async addProjectSource(
    source: ScanSourceItem,
    driveApiKey?: string,
    frozenMode: boolean = true
  ): Promise<WhatChangedResponse> {
    return fetchJson(`${BASE_URL}/project/sources/add`, {
      method: 'POST',
      body: JSON.stringify({
        source,
        drive_api_key: driveApiKey,
        frozen_mode: frozenMode,
      }),
    });
  },

  async getWhatChanged(): Promise<WhatChangedResponse> {
    return fetchJson(`${BASE_URL}/project/what-changed`);
  },

  async undoLastSnapshot(): Promise<UndoSnapshotResponse> {
    return fetchJson(`${BASE_URL}/project/snapshots/undo`, {
      method: 'POST',
    });
  },

  async getProjectSnapshots(): Promise<SnapshotItem[]> {
    return fetchJson(`${BASE_URL}/project/snapshots`);
  },

  async selectFolderDialog(title?: string): Promise<{ selected?: string; cancelled: boolean }> {
    return fetchJson(`${BASE_URL}/fs/select-dialog`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  async selectFileDialog(title?: string): Promise<{ selected?: string; cancelled: boolean }> {
    return fetchJson(`${BASE_URL}/fs/select-file-dialog`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  async checkEdits(workDir?: string, inputPath?: string): Promise<{
    has_saved_edits: boolean;
    saved_edits_count: number;
    work_dir: string;
    is_different_source: boolean;
    default_action: 'keep' | 'fresh';
    previous_source?: string;
    message: string;
  }> {
    const params = new URLSearchParams();
    if (workDir) params.append('work_dir', workDir);
    if (inputPath) params.append('input_path', inputPath);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJson(`${BASE_URL}/projects/check-edits${qs}`);
  },

  async getModelStatus(): Promise<ModelStatus> {
    return fetchJson(`${BASE_URL}/models/status`);
  },

  async checkModelUpdates(simulate: boolean = false): Promise<{
    installed: boolean;
    update_available: boolean;
    version?: string;
    latest_version?: string;
    message?: string;
  }> {
    return fetchJson(`${BASE_URL}/models/check-update`, {
      method: 'POST',
      body: JSON.stringify({ simulate }),
    });
  },

  async downloadModels(force: boolean = false): Promise<ModelStatus> {
    return fetchJson(`${BASE_URL}/models/download`, {
      method: 'POST',
      body: JSON.stringify({ force }),
    });
  },
};

export const apiClient = api;

