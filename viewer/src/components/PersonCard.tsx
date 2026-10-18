import React, { useState, useRef } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { Image as ImageIcon, Download, Check, RefreshCw } from 'lucide-react';
import {
  isDrivePhoto,
  downloadLocalZip,
  downloadDriveSequential,
  PhotoDownloadItem,
} from '../utils/downloader';

interface PersonCardProps {
  person: PersonCluster;
  photos?: Record<string, PhotoInfo>;
  showLabel?: boolean;
  onClick: () => void;
  onDownloadAll?: (person: PersonCluster) => void;
}

export const PersonCard: React.FC<PersonCardProps> = ({
  person,
  photos = {},
  showLabel = true,
  onClick,
  onDownloadAll,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<{ current: number; total: number } | null>(null);
  const [isDownloaded, setIsDownloaded] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const displayName = person.label || person.id.toUpperCase();
  const photoIds = person.photos || person.photo_ids || [];
  const photoCount = photoIds.length;

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (onDownloadAll) {
      onDownloadAll(person);
      return;
    }

    if (isDownloading || photoCount === 0) return;

    setIsDownloading(true);
    setDownloadProgress({ current: 0, total: photoCount });
    setIsDownloaded(false);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      // Build download items
      const items: PhotoDownloadItem[] = photoIds
        .map((pid) => {
          const photo = photos[pid] || {
            name: `${pid}.jpg`,
            thumb: `thumbs/${pid}.jpg`,
            download: `thumbs/${pid}.jpg`,
          };
          return { id: pid, photo };
        });

      const hasDrive = items.some((it) => isDrivePhoto(it.photo));

      if (hasDrive) {
        await downloadDriveSequential(
          items,
          (curr, tot) => setDownloadProgress({ current: curr, total: tot }),
          abortController.signal
        );
      } else {
        await downloadLocalZip(
          person.label || person.id,
          items,
          (curr, tot) => setDownloadProgress({ current: curr, total: tot }),
          abortController.signal
        );
      }

      setIsDownloaded(true);
      setTimeout(() => setIsDownloaded(false), 3000);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Download error for person:', person.id, err);
      }
    } finally {
      setIsDownloading(false);
      setDownloadProgress(null);
    }
  };

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      className="group relative flex flex-col items-center text-center p-3 rounded-xl glass-card focus:outline-none focus-visible:ring-2 transition-all duration-150 w-full cursor-pointer select-none"
      aria-label={`View photos for ${displayName} (${photoCount} photos)`}
      style={{
        background: 'var(--card-bg)',
        border: '2px solid var(--line)',
        boxShadow: '3px 3px 0px var(--line)',
      }}
    >
      {/* Square Face Thumbnail Container */}
      <div
        className="relative w-full aspect-square rounded-lg overflow-hidden bg-[var(--bg)] border-2 border-[var(--line)] group-hover:border-[var(--accent)] transition-all duration-200"
        style={{
          boxShadow: '2px 2px 0px var(--line)',
        }}
      >
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 shimmer-placeholder" />
        )}

        {imageError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-[var(--muted)] bg-[var(--panel)]">
            <ImageIcon className="w-8 h-8 mb-1 opacity-50 text-[var(--muted)]" />
            <span className="text-[10px] font-mono font-bold">No Preview</span>
          </div>
        ) : (
          <img
            src={person.face}
            alt={displayName}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            className={`w-full h-full object-cover transition-transform duration-200 group-hover:scale-105 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Photo Count Badge (Overlay in corner) */}
        <div
          className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[11px] font-mono font-bold border border-[var(--line)] shadow-sm"
          style={{
            background: 'var(--panel)',
            color: 'var(--text)',
          }}
        >
          {photoCount} {photoCount === 1 ? 'photo' : 'photos'}
        </div>
      </div>

      {/* Label / ID */}
      {showLabel && (
        <div className="mt-2.5 w-full px-1">
          <p className="text-xs sm:text-sm font-bold font-mono text-[var(--text)] group-hover:text-[var(--accent)] transition-colors truncate">
            {displayName}
          </p>
        </div>
      )}

      {/* Direct Action: Download All Pics Button for this Person */}
      <div className="mt-2.5 w-full pt-1">
        <button
          type="button"
          onClick={handleDownload}
          disabled={isDownloading || photoCount === 0}
          title={`Download all ${photoCount} photos of ${displayName}`}
          aria-label={`Download all ${photoCount} photos for ${displayName}`}
          className={`btn-tactile btn-sm w-full py-1.5 px-2 text-xs flex items-center justify-center gap-1.5 font-mono ${
            isDownloaded ? 'bg-green-700 text-white' : ''
          }`}
          style={{
            width: '100%',
            padding: '6px 8px',
            fontSize: '11px',
            backgroundColor: isDownloaded ? 'var(--accent)' : 'var(--panel)',
            color: isDownloaded ? 'var(--on-accent)' : 'var(--text)',
          }}
        >
          {isDownloading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[var(--accent)]" />
              <span>
                {downloadProgress
                  ? `${downloadProgress.current}/${downloadProgress.total}`
                  : 'Packing...'}
              </span>
            </>
          ) : isDownloaded ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Downloaded!</span>
            </>
          ) : (
            <>
              <Download className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span>Download All ({photoCount})</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
export default PersonCard;
