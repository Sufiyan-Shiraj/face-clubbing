import React, { useEffect, useCallback, useState } from 'react';
import { PhotoInfo } from '../types';
import { X, Download, ChevronLeft, ChevronRight, ExternalLink, ImageOff } from 'lucide-react';
import { getCleanDownloadName, isDrivePhoto } from '../utils/downloader';

interface PhotoModalProps {
  photo: PhotoInfo;
  photoId: string;
  hasPrev: boolean;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
  personLabel?: string;
}

export const PhotoModal: React.FC<PhotoModalProps> = ({
  photo,
  photoId,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
  onClose,
  personLabel,
}) => {
  const [imageError, setImageError] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && hasPrev) onPrev();
      if (e.key === 'ArrowRight' && hasNext) onNext();
    },
    [onClose, onPrev, onNext, hasPrev, hasNext]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  const isDrive = isDrivePhoto(photo);
  const downloadUrl = photo.download_url || photo.download || (photo.drive_file_id ? `https://drive.google.com/uc?id=${photo.drive_file_id}&export=download` : null);
  const driveViewUrl = photo.drive_url || (photo.drive_file_id ? `https://drive.google.com/file/d/${photo.drive_file_id}/view` : null);
  const cleanFileName = getCleanDownloadName(personLabel || 'photo', 0, photo.name);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/92 backdrop-blur-md animate-fadeIn">
      {/* Top action bar */}
      <div className="absolute top-0 inset-x-0 p-3.5 sm:p-5 flex items-center justify-between z-10 bg-gradient-to-b from-black/90 via-black/50 to-transparent">
        <div className="text-white min-w-0 pr-2">
          <p className="text-xs sm:text-sm font-bold truncate max-w-[180px] sm:max-w-md font-mono">
            {photo.name}
          </p>
          {photo.width && photo.height && (
            <p className="text-[10px] sm:text-xs text-neutral-400">
              {photo.width} × {photo.height} px
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {downloadUrl && (
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              download={cleanFileName}
              className="btn-tactile btn-accent btn-sm"
              style={{ padding: '8px 14px', fontSize: '13px' }}
              title="Download photo"
            >
              <Download className="w-4 h-4" />
              <span className="font-mono font-bold">Download</span>
            </a>
          )}

          {isDrive && driveViewUrl && (
            <a
              href={driveViewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-tactile btn-sm"
              style={{ padding: '8px 14px', fontSize: '13px' }}
              title="Open in Google Drive"
            >
              <ExternalLink className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span className="font-mono font-bold">Drive</span>
            </a>
          )}

          <button
            onClick={onClose}
            className="btn-tactile btn-sm"
            style={{ padding: '8px', minWidth: '36px' }}
            title="Close (Esc)"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Image Container */}
      <div className="relative max-w-5xl max-h-[85vh] w-full px-4 flex items-center justify-center">
        {imageError ? (
          <div
            className="p-8 rounded-xl border-2 border-[var(--line)] text-center max-w-sm space-y-3 shadow-[4px_4px_0px_var(--line)]"
            style={{ background: 'var(--panel)' }}
          >
            <ImageOff className="w-10 h-10 mx-auto text-[var(--muted)]" />
            <p className="text-sm font-bold font-mono text-[var(--text)]">Image Preview Unavailable</p>
            {isDrive && driveViewUrl ? (
              <a
                href={driveViewUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-tactile btn-accent btn-sm inline-flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span className="font-mono">Open in Drive ↗</span>
              </a>
            ) : (
              <p className="text-xs font-mono text-[var(--muted)]">Could not load image file from disk.</p>
            )}
          </div>
        ) : (
          <img
            src={photo.thumb}
            alt={photo.name}
            onError={() => setImageError(true)}
            className="max-h-[80vh] max-w-full object-contain rounded-xl border-2 border-[var(--line)] shadow-[6px_6px_0px_var(--line)]"
          />
        )}

        {/* Previous Button */}
        {hasPrev && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPrev();
            }}
            className="btn-tactile absolute left-4 sm:left-6 top-1/2 -translate-y-1/2 rounded-full"
            style={{ padding: '12px' }}
            title="Previous (Left Arrow)"
            aria-label="Previous photo"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        )}

        {/* Next Button */}
        {hasNext && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onNext();
            }}
            className="btn-tactile absolute right-4 sm:right-6 top-1/2 -translate-y-1/2 rounded-full"
            style={{ padding: '12px' }}
            title="Next (Right Arrow)"
            aria-label="Next photo"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        )}
      </div>
    </div>
  );
};
export default PhotoModal;
