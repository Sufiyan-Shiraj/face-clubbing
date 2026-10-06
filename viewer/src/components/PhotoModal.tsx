import React, { useEffect, useCallback } from 'react';
import { PhotoInfo } from '../types';
import { X, Download, ChevronLeft, ChevronRight } from 'lucide-react';

interface PhotoModalProps {
  photo: PhotoInfo;
  photoId: string;
  hasPrev: boolean;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
}

export const PhotoModal: React.FC<PhotoModalProps> = ({
  photo,
  photoId,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
  onClose,
}) => {
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md animate-fadeIn">
      {/* Top action bar */}
      <div className="absolute top-0 inset-x-0 p-3.5 sm:p-6 flex items-center justify-between z-10 bg-gradient-to-b from-black/90 via-black/50 to-transparent">
        <div className="text-white min-w-0 pr-2">
          <p className="text-xs sm:text-base font-semibold truncate max-w-[160px] sm:max-w-md font-mono">
            {photo.name}
          </p>
          {photo.width && photo.height && (
            <p className="text-[10px] sm:text-xs text-neutral-400">
              {photo.width} × {photo.height} px
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {photo.download && (
            <a
              href={photo.download}
              target="_blank"
              rel="noopener noreferrer"
              download={photo.name}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-accent text-white text-xs sm:text-sm font-medium hover:brightness-110 transition-all shadow-lg"
              title="Download original photo"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </a>
          )}

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-neutral-900/80 text-neutral-300 hover:text-white hover:bg-neutral-800 transition-colors"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Image Container */}
      <div className="relative max-w-5xl max-h-[85vh] w-full px-4 flex items-center justify-center">
        <img
          src={photo.thumb}
          alt={photo.name}
          className="max-h-[80vh] max-w-full object-contain rounded-lg shadow-2xl"
        />

        {/* Previous Button */}
        {hasPrev && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPrev();
            }}
            className="absolute left-6 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-neutral-900/80 hover:bg-neutral-800 text-white transition-all backdrop-blur-md"
            title="Previous (Left Arrow)"
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
            className="absolute right-6 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-neutral-900/80 hover:bg-neutral-800 text-white transition-all backdrop-blur-md"
            title="Next (Right Arrow)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        )}
      </div>
    </div>
  );
};
