import { downloadZip } from 'client-zip';
import { PhotoInfo, PersonCluster } from '../types';

export const SIZE_GUARD_THRESHOLD_BYTES = 500 * 1024 * 1024; // 500 MB
export const ESTIMATED_BYTES_PER_PHOTO = 2.5 * 1024 * 1024;  // ~2.5 MB average full resolution

export interface PhotoDownloadItem {
  id: string;
  photo: PhotoInfo;
}

export interface FallbackItem {
  filename: string;
  originalName: string;
  reason: string;
}

export interface FailedItem {
  filename: string;
  originalName: string;
  error: string;
}

export interface DownloadNotice {
  message: string;
  count: number;
  type: 'warning' | 'info';
}

export interface DownloadProgress {
  current: number;
  total: number;
  statusText?: string;
  isThrottled?: boolean;
}

export interface DownloadZipResult {
  total: number;
  fullResCount: number;
  fallbackCount: number;
  failedCount: number;
  throttledCount: number;
  hasNotes: boolean;
  notesContent?: string;
  partIndex?: number;
  totalParts?: number;
  zipName: string;
}

/**
 * Generates clean, private-data-free filenames in the format:
 *   personname_001.jpg, personname_002.jpg, ...
 */
export function getCleanDownloadName(
  personLabelOrId: string | null | undefined,
  index: number,
  originalFileName?: string
): string {
  const raw = (personLabelOrId || 'person').trim().toLowerCase();
  const sanitized = raw.replace(/[^a-z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'person';
  
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
 * Resolves the full resolution photo URL for both Drive and local storage.
 * Google Drive photos use Google UserContent CDN (=s0) for full native resolution
 * and unrestricted CORS headers.
 */
export function getFullResolutionPhotoUrl(photo: PhotoInfo): string {
  const driveId = getDriveFileId(photo);
  if (driveId) {
    return `https://lh3.googleusercontent.com/d/${driveId}=s0`;
  }
  return photo.download || photo.download_url || photo.thumb || '';
}

// Backwards-compatible alias
export const getOriginalPhotoUrl = getFullResolutionPhotoUrl;

/**
 * Estimates total download size in bytes.
 */
export function estimateDownloadSize(items: PhotoDownloadItem[]): number {
  return items.length * ESTIMATED_BYTES_PER_PHOTO;
}

/**
 * Checks if total download exceeds size guard threshold.
 */
export function checkDownloadSize(
  items: PhotoDownloadItem[],
  thresholdBytes = SIZE_GUARD_THRESHOLD_BYTES
): { isOverThreshold: boolean; estimatedBytes: number; proposedParts: number } {
  const estimatedBytes = estimateDownloadSize(items);
  const isOverThreshold = estimatedBytes > thresholdBytes;
  const proposedParts = isOverThreshold ? Math.ceil(estimatedBytes / (250 * 1024 * 1024)) : 1;
  return { isOverThreshold, estimatedBytes, proposedParts };
}

/**
 * Partitions items into balanced parts for split zip downloads.
 */
export function partitionDownloadItems(
  items: PhotoDownloadItem[],
  parts: number
): PhotoDownloadItem[][] {
  if (parts <= 1) return [items];
  const result: PhotoDownloadItem[][] = [];
  const chunkSize = Math.ceil(items.length / parts);
  for (let i = 0; i < items.length; i += chunkSize) {
    result.push(items.slice(i, i + chunkSize));
  }
  return result;
}

/**
 * Generates DOWNLOAD_NOTES.txt when fallback qualities or failures occur.
 */
export function generateDownloadNotes(
  personLabelOrId: string,
  totalPhotos: number,
  fullResCount: number,
  fallbackItems: FallbackItem[],
  failedItems: FailedItem[]
): string {
  const lines: string[] = [
    '================================================================================',
    'CATLOG DOWNLOAD NOTES & QUALITY REPORT',
    '================================================================================',
    `Person / Cluster : ${personLabelOrId}`,
    `Generated At     : ${new Date().toISOString()}`,
    `Total In Cluster : ${totalPhotos}`,
    `Full Resolution  : ${fullResCount}`,
    `Fell Back        : ${fallbackItems.length} (packaged at thumbnail resolution)`,
    `Failed           : ${failedItems.length}`,
    '',
    'ATTENTION — HONESTY INVOICE:',
    'Not all photos could be retrieved at full native resolution.',
    'To preserve complete photo sets without silently mixing qualities, any photo that',
    'failed full-resolution fetching is documented below.',
    '',
  ];

  if (fallbackItems.length > 0) {
    lines.push('--------------------------------------------------------------------------------');
    lines.push(`THUMBNAIL FALLBACKS (${fallbackItems.length} FILES):`);
    lines.push('--------------------------------------------------------------------------------');
    fallbackItems.forEach((item, idx) => {
      lines.push(`${idx + 1}. Archive Entry: ${item.filename}`);
      lines.push(`   Source File   : ${item.originalName || 'unknown'}`);
      lines.push(`   Reason        : ${item.reason}`);
    });
    lines.push('');
  }

  if (failedItems.length > 0) {
    lines.push('--------------------------------------------------------------------------------');
    lines.push(`FAILED DOWNLOADS (${failedItems.length} FILES):`);
    lines.push('--------------------------------------------------------------------------------');
    failedItems.forEach((item, idx) => {
      lines.push(`${idx + 1}. Missing Entry: ${item.filename}`);
      lines.push(`   Source File  : ${item.originalName || 'unknown'}`);
      lines.push(`   Error Detail : ${item.error}`);
    });
    lines.push('');
  }

  lines.push('================================================================================');
  return lines.join('\n');
}

/**
 * Streamingly builds and downloads a zip archive for photos using client-zip.
 * Never silently mixes qualities:
 * - Full resolution photos are preferred.
 * - If lh3 throttles/fails, attempts documented Drive download link and informs UI.
 * - If a photo falls back to thumbnail or fails, records it in DOWNLOAD_NOTES.txt inside the zip
 *   and reports the count to the UI.
 */
export async function downloadLocalZip(
  personLabelOrId: string,
  items: PhotoDownloadItem[],
  onProgress: (current: number, total: number) => void,
  signal: AbortSignal,
  options?: {
    partIndex?: number;
    totalParts?: number;
    onNotice?: (notice: { message: string; count: number; type: 'warning' | 'info' }) => void;
    onStatusText?: (statusText: string) => void;
  }
): Promise<DownloadZipResult> {
  const total = items.length;
  if (total === 0) {
    return {
      total: 0,
      fullResCount: 0,
      fallbackCount: 0,
      failedCount: 0,
      throttledCount: 0,
      hasNotes: false,
      zipName: '',
    };
  }

  const fallbackItems: FallbackItem[] = [];
  const failedItems: FailedItem[] = [];
  let fullResCount = 0;
  let throttledCount = 0;

  async function* makeFileEntries() {
    for (let i = 0; i < items.length; i++) {
      if (signal.aborted) {
        throw new DOMException('Download cancelled by user', 'AbortError');
      }

      const item = items[i];
      const filename = getCleanDownloadName(personLabelOrId, i, item.photo.name);
      const isDrive = isDrivePhoto(item.photo);
      const primaryUrl = getFullResolutionPhotoUrl(item.photo);
      
      onProgress(i + 1, total);
      options?.onStatusText?.(`Fetching ${i + 1}/${total}...`);

      let response: Response | null = null;
      let usedFallback = false;
      let fallbackReason = '';

      // 1. Try full resolution URL (lh3 CDN for Drive, or direct download for local)
      try {
        const resp = await fetch(primaryUrl, { signal });
        if (resp.ok) {
          response = resp;
          fullResCount++;
        } else {
          if (isDrive && (resp.status === 429 || resp.status === 403 || resp.status === 503)) {
            throttledCount++;
            options?.onStatusText?.(`Google CDN throttled (${resp.status}); checking documented Drive link...`);
            options?.onNotice?.({
              message: `Google CDN throttled for photo "${item.photo.name}" (${resp.status}); falling back to documented Drive download link`,
              count: throttledCount,
              type: 'warning',
            });
          }
          throw new Error(`HTTP ${resp.status}`);
        }
      } catch (err: any) {
        if (signal.aborted) throw err;

        // 2. Fallback attempt: Documented Drive link or photo.download
        let secondaryUrl = item.photo.download || item.photo.download_url;
        if (isDrive) {
          const driveId = getDriveFileId(item.photo);
          if (driveId) {
            secondaryUrl = `https://drive.google.com/uc?id=${driveId}&export=download`;
          }
        }

        if (secondaryUrl && secondaryUrl !== primaryUrl) {
          try {
            const sResp = await fetch(secondaryUrl, { signal });
            if (sResp.ok) {
              response = sResp;
              fullResCount++;
            }
          } catch (_) {
            // Documented Drive link may hit browser CORS restrictions; fall through to thumb
          }
        }

        // 3. Fallback to thumbnail if full resolution unreachable
        if (!response) {
          const thumbUrl = item.photo.thumb;
          if (thumbUrl) {
            try {
              const tResp = await fetch(thumbUrl, { signal });
              if (tResp.ok) {
                response = tResp;
                usedFallback = true;
                fallbackReason = `Full resolution endpoint failed (${err.message || 'network error'}); packaged thumbnail resolution`;
                fallbackItems.push({
                  filename,
                  originalName: item.photo.name,
                  reason: fallbackReason,
                });
                options?.onNotice?.({
                  message: `Photo "${item.photo.name}" fell back to thumbnail`,
                  count: fallbackItems.length,
                  type: 'warning',
                });
              }
            } catch (tErr: any) {
              if (signal.aborted) throw tErr;
            }
          }
        }

        // 4. Mark as completely failed if no response obtained
        if (!response) {
          failedItems.push({
            filename,
            originalName: item.photo.name,
            error: err.message || 'Fetch failed from all sources',
          });
        }
      }

      if (response) {
        yield {
          name: filename,
          input: response,
        };
      }
    }

    // 5. If any fallbacks or failures occurred, include DOWNLOAD_NOTES.txt inside the ZIP
    if (fallbackItems.length > 0 || failedItems.length > 0) {
      const notes = generateDownloadNotes(
        personLabelOrId,
        total,
        fullResCount,
        fallbackItems,
        failedItems
      );
      yield {
        name: 'DOWNLOAD_NOTES.txt',
        input: notes,
      };
    }
  }

  const zipResponse = downloadZip(makeFileEntries());
  const blob = await zipResponse.blob();

  if (signal.aborted) {
    throw new DOMException('Download cancelled by user', 'AbortError');
  }

  // File naming with optional parts
  const raw = (personLabelOrId || 'person').trim().toLowerCase();
  const sanitized = raw.replace(/[^a-z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'person';
  let zipName = `${sanitized}_photos.zip`;
  if (options?.totalParts && options.totalParts > 1) {
    zipName = `${sanitized}_photos_part${options.partIndex || 1}_of_${options.totalParts}.zip`;
  }

  // Trigger browser download
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = zipName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);

  const hasNotes = fallbackItems.length > 0 || failedItems.length > 0;
  return {
    total,
    fullResCount,
    fallbackCount: fallbackItems.length,
    failedCount: failedItems.length,
    throttledCount,
    hasNotes,
    notesContent: hasNotes
      ? generateDownloadNotes(personLabelOrId, total, fullResCount, fallbackItems, failedItems)
      : undefined,
    partIndex: options?.partIndex,
    totalParts: options?.totalParts,
    zipName,
  };
}

export const downloadPersonZip = downloadLocalZip;

/**
 * Downloads Google Drive photos sequentially one-by-one reusing existing download_url.
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
