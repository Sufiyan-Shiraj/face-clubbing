import { downloadZip } from 'client-zip';
import { PhotoInfo, PersonCluster } from '../types';

/**
 * Generates clean, private-data-free filenames in the format:
 *   personname_001.jpg, personname_002.jpg, ...
 */
export function getCleanDownloadName(
  personLabelOrId: string | null | undefined,
  index: number,
  originalFileName?: string
): string {
  // Sanitize person name: lowercase, alphanumeric and underscores only
  const raw = (personLabelOrId || 'person').trim().toLowerCase();
  const sanitized = raw.replace(/[^a-z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'person';
  
  // Extract extension from original file name, fallback to .jpg
  let ext = 'jpg';
  if (originalFileName) {
    const parts = originalFileName.split('.');
    if (parts.length > 1) {
      ext = parts[parts.length - 1].toLowerCase().replace(/[^a-z0-9]/g, '');
      if (!ext) ext = 'jpg';
    }
  }

  const num = String(index + 1).padStart(3, '0');
  return `${sanitized}_${num}.${ext}`;
}

/**
 * Checks whether a photo comes from Google Drive.
 */
export function isDrivePhoto(photo: PhotoInfo): boolean {
  if (photo.drive_file_id) return true;
  if (photo.drive_url) return true;
  const dl = photo.download_url || photo.download || '';
  return dl.includes('drive.google.com') || dl.includes('uc?id=');
}

/**
 * Extracts Google Drive file ID from photo metadata or URL.
 */
export function getDriveFileId(photo: PhotoInfo): string | null {
  if (photo.drive_file_id) return photo.drive_file_id;
  const dUrl = photo.drive_url || photo.download_url || photo.download || '';
  const m1 = dUrl.match(/\/d\/([a-zA-Z0-9_-]{15,})/);
  if (m1) return m1[1];
  const m2 = dUrl.match(/[?&]id=([a-zA-Z0-9_-]{15,})/);
  if (m2) return m2[1];
  return null;
}

/**
 * Resolves the original full quality photo URL for both Drive and local storage.
 * Google Drive photos use the Google UserContent CDN (=s0) which provides full native
 * resolution without downscaling and includes Access-Control-Allow-Origin: * headers.
 */
export function getOriginalPhotoUrl(photo: PhotoInfo): string {
  const driveId = getDriveFileId(photo);
  if (driveId) {
    return `https://lh3.googleusercontent.com/d/${driveId}=s0`;
  }
  return photo.download || photo.download_url || photo.thumb || '';
}

export interface PhotoDownloadItem {
  id: string;
  photo: PhotoInfo;
}

/**
 * Streamingly builds and downloads a zip archive for photos using client-zip.
 * Does not buffer all files in memory at once; streams file entries sequentially.
 * Works seamlessly for both Google Drive and local photos in original full quality.
 */
export async function downloadLocalZip(
  personLabelOrId: string,
  items: PhotoDownloadItem[],
  onProgress: (current: number, total: number) => void,
  signal: AbortSignal
): Promise<void> {
  const total = items.length;
  if (total === 0) return;

  async function* makeFileEntries() {
    for (let i = 0; i < items.length; i++) {
      if (signal.aborted) {
        throw new DOMException('Download cancelled by user', 'AbortError');
      }

      onProgress(i + 1, total);
      const item = items[i];
      const filename = getCleanDownloadName(personLabelOrId, i, item.photo.name);
      
      // Resolve download URL (prefer full original photo download, fallback to thumbnail)
      const primaryUrl = getOriginalPhotoUrl(item.photo);
      
      let response: Response;
      try {
        response = await fetch(primaryUrl, { signal });
        if (!response.ok) {
          throw new Error(`Failed to fetch photo "${item.photo.name}" (${response.status})`);
        }
      } catch (err: any) {
        if (signal.aborted) throw err;
        // Fallback: try photo.download or photo.thumb if primaryUrl failed
        const fallback = item.photo.download || item.photo.download_url || item.photo.thumb;
        if (fallback && fallback !== primaryUrl) {
          response = await fetch(fallback, { signal });
          if (!response.ok) {
            throw new Error(`Failed to fetch photo "${item.photo.name}" (${response.status})`);
          }
        } else {
          throw err;
        }
      }

      yield {
        name: filename,
        input: response,
      };
    }
  }

  const zipResponse = downloadZip(makeFileEntries());
  const blob = await zipResponse.blob();

  if (signal.aborted) {
    throw new DOMException('Download cancelled by user', 'AbortError');
  }

  // Trigger browser file save
  const raw = (personLabelOrId || 'person').trim().toLowerCase();
  const sanitized = raw.replace(/[^a-z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'person';
  const zipName = `${sanitized}_photos.zip`;

  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = zipName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}

export const downloadPersonZip = downloadLocalZip;

/**
 * Downloads Google Drive photos sequentially one-by-one reusing existing download_url.
 * Browsers cannot zip Drive files due to lack of CORS headers on Drive CDN.
 */
export async function downloadDriveSequential(
  items: PhotoDownloadItem[],
  onProgress: (current: number, total: number) => void,
  signal: AbortSignal,
  delayMs = 400
): Promise<void> {
  const total = items.length;
  if (total === 0) return;

  for (let i = 0; i < items.length; i++) {
    if (signal.aborted) {
      throw new DOMException('Download cancelled by user', 'AbortError');
    }

    onProgress(i + 1, total);
    const item = items[i];
    
    // Reuse existing download_url field
    let url = item.photo.download_url || item.photo.download;
    if (!url && item.photo.drive_file_id) {
      url = `https://drive.google.com/uc?id=${item.photo.drive_file_id}&export=download`;
    }

    if (url) {
      const a = document.createElement('a');
      a.href = url;
      a.download = item.photo.name;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    // Delay between downloads to prevent browser popup suppression
    if (i < items.length - 1) {
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          signal.removeEventListener('abort', onAbort);
          resolve();
        }, delayMs);
        const onAbort = () => {
          clearTimeout(timeout);
          reject(new DOMException('Download cancelled by user', 'AbortError'));
        };
        signal.addEventListener('abort', onAbort, { once: true });
      });
    }
  }
}
