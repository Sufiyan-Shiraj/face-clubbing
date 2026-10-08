import {
  JobStatus,
  PersonCluster,
  UnrecognizedData,
  SuggestionsData,
  EditResponse,
  Settings,
  PhotoInfo,
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

  async startJob(inputPath?: string, outputDir: string = 'export'): Promise<JobStatus> {
    return fetchJson(`${BASE_URL}/jobs/start`, {
      method: 'POST',
      body: JSON.stringify({
        input_path: inputPath || 'test_photos',
        output_dir: outputDir,
      }),
    });
  },

  async cancelJob(): Promise<JobStatus> {
    return fetchJson(`${BASE_URL}/jobs/cancel`, {
      method: 'POST',
    });
  },

  subscribeProgress(
    onMessage: (status: JobStatus) => void,
    onError?: (err: any) => void
  ): () => void {
    let eventSource: EventSource | null = null;
    let isClosed = false;
    let reconnectTimeout: any = null;

    const connect = () => {
      if (isClosed) return;
      try {
        eventSource = new EventSource(`${BASE_URL}/jobs/progress`);
        eventSource.onmessage = (event) => {
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
            reconnectTimeout = setTimeout(connect, 1500);
          }
        };
      } catch (err) {
        if (onError) onError(err);
        if (!isClosed) {
          reconnectTimeout = setTimeout(connect, 2000);
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
    photo_id?: string;
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
};
