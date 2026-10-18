import React, { useState, useRef } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import {
  ArrowLeft,
  Download,
  ZoomIn,
  HelpCircle,
  Check,
  X,
  ExternalLink,
  AlertCircle,
  CheckSquare,
  Square,
  ImageOff,
} from 'lucide-react';
import { PhotoModal } from './PhotoModal';
import {
  getCleanDownloadName,
  isDrivePhoto,
  downloadLocalZip,
  downloadDriveSequential,
  PhotoDownloadItem,
} from '../utils/downloader';

interface PhotoGalleryProps {
  person: PersonCluster;
  photos: Record<string, PhotoInfo>;
  includeMaybe?: boolean;
  onBack: () => void;
}

export const PhotoGallery: React.FC<PhotoGalleryProps> = ({
  person,
  photos,
  includeMaybe = false,
  onBack,
}) => {
  const [modalState, setModalState] = useState<{
    list: string[];
    index: number;
  } | null>(null);

  // Selection mode
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedPhotoIds, setSelectedPhotoIds] = useState<Set<string>>(new Set());

  // Download state & progress
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<{ current: number; total: number } | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [showDriveNoteModal, setShowDriveNoteModal] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Track failed images for fallback tile
  const [imageErrorMap, setImageErrorMap] = useState<Record<string, boolean>>({});

  const displayName = person.label || person.id.toUpperCase();
  const photoIds = person.photos || person.photo_ids || [];
  const maybePhotos = person.maybe_photos || [];

  // Determine if this person's photos are sourced from Google Drive
  const hasDrivePhotos = photoIds.some((pid) => {
    const p = photos[pid];
    return p ? isDrivePhoto(p) : false;
  });

  // Modal navigation
  const handleOpenModal = (list: string[], idx: number) => {
    if (isSelectMode) return;
    setModalState({ list, index: idx });
  };

  const handleCloseModal = () => {
    setModalState(null);
  };

  const handlePrev = () => {
    if (modalState && modalState.index > 0) {
      setModalState({ ...modalState, index: modalState.index - 1 });
    }
  };

  const handleNext = () => {
    if (modalState && modalState.index < modalState.list.length - 1) {
      setModalState({ ...modalState, index: modalState.index + 1 });
    }
  };

  const activePhotoId = modalState ? modalState.list[modalState.index] : null;
  const activePhoto = activePhotoId ? photos[activePhotoId] : null;

  // Selection toggle
  const toggleSelectPhoto = (pid: string) => {
    setSelectedPhotoIds((prev) => {
      const next = new Set(prev);
      if (next.has(pid)) {
        next.delete(pid);
      } else {
        next.add(pid);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedPhotoIds.size === photoIds.length) {
      setSelectedPhotoIds(new Set());
    } else {
      setSelectedPhotoIds(new Set(photoIds));
    }
  };

  const handleCancelDownload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsDownloading(false);
    setDownloadProgress(null);
  };

  // Perform bulk download (either all confirmed or selected)
  const executeDownload = async (targetIds: string[]) => {
    const validItems: PhotoDownloadItem[] = targetIds
      .map((pid) => ({ id: pid, photo: photos[pid] }))
      .filter((item): item is PhotoDownloadItem => Boolean(item.photo));

    if (validItems.length === 0) return;

    const controller = new AbortController();
    abortControllerRef.current = controller;
    setIsDownloading(true);
    setDownloadProgress({ current: 0, total: validItems.length });
    setDownloadError(null);

    try {
      if (hasDrivePhotos) {
        await downloadDriveSequential(
          validItems,
          (cur, tot) => setDownloadProgress({ current: cur, total: tot }),
          controller.signal
        );
      } else {
        await downloadLocalZip(
          displayName,
          validItems,
          (cur, tot) => setDownloadProgress({ current: cur, total: tot }),
          controller.signal
        );
      }
    } catch (err: any) {
      if (err?.name !== 'AbortError' && !controller.signal.aborted) {
        console.error('Download error:', err);
        setDownloadError(err?.message || 'Download failed');
      }
    } finally {
      setIsDownloading(false);
      setDownloadProgress(null);
      abortControllerRef.current = null;
    }
  };

  const handleDownloadClick = (targetIds: string[]) => {
    if (hasDrivePhotos) {
      const acknowledged = sessionStorage.getItem('catlog-drive-dl-note-shown');
      if (!acknowledged) {
        setShowDriveNoteModal(true);
        return;
      }
    }
    executeDownload(targetIds);
  };

  const handleConfirmDriveDownload = () => {
    sessionStorage.setItem('catlog-drive-dl-note-shown', '1');
    setShowDriveNoteModal(false);
    const targetIds = isSelectMode && selectedPhotoIds.size > 0
      ? Array.from(selectedPhotoIds)
      : photoIds;
    executeDownload(targetIds);
  };

  // Single photo download
  const handleDownloadSingle = async (photo: PhotoInfo, idx: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const cleanName = getCleanDownloadName(displayName, idx, photo.name);
    
    if (isDrivePhoto(photo)) {
      const url = photo.download_url || photo.download || (photo.drive_file_id ? `https://drive.google.com/uc?id=${photo.drive_file_id}&export=download` : null);
      if (url) {
        const a = document.createElement('a');
        a.href = url;
        a.download = cleanName;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } else {
      // Local single photo download
      const url = photo.download || photo.download_url || photo.thumb;
      try {
        const res = await fetch(url);
        const blob = await res.blob();
        const objUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objUrl;
        a.download = cleanName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(objUrl), 1000);
      } catch (err) {
        console.error('Single photo download failed:', err);
      }
    }
  };

  // Find representative Drive folder/link for fallback
  const firstDriveUrl = photoIds
    .map((pid) => photos[pid]?.drive_url)
    .find((url) => Boolean(url));

  return (
    <div className="space-y-6 pb-24 animate-fadeIn">
      {/* Top Profile Banner */}
      <div
        className="p-4 sm:p-6 rounded-xl glass-card flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
        style={{
          background: 'var(--panel)',
          border: '2px solid var(--line)',
          boxShadow: '4px 4px 0px var(--line)',
        }}
      >
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="btn-tactile btn-sm"
            title="Back to all people"
            aria-label="Back to all people"
            style={{ padding: '10px 14px' }}
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono font-bold hidden sm:inline">Back</span>
          </button>

          <img
            src={person.face}
            alt={displayName}
            loading="lazy"
            className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl object-cover border-2 border-[var(--line)] shadow-[2px_2px_0px_var(--line)] bg-[var(--bg)] flex-shrink-0"
          />

          <div>
            <h2 className="text-2xl sm:text-3xl font-black font-mono tracking-tight text-[var(--text)]">
              {displayName}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="badge-chip">
                {photoIds.length} {photoIds.length === 1 ? 'photo' : 'photos'}
              </span>
              {maybePhotos.length > 0 && includeMaybe && (
                <span className="badge-chip" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}>
                  +{maybePhotos.length} possible
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons: Download all N photos, Select Mode, Drive Fallback */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Primary: Download all N photos (shows person's photo count) */}
          {photoIds.length > 0 && (
            <button
              onClick={() => handleDownloadClick(photoIds)}
              disabled={isDownloading}
              className="btn-tactile btn-accent"
              style={{
                padding: '10px 20px',
                fontSize: '14px',
              }}
              title={`Download all ${photoIds.length} photos for ${displayName}`}
            >
              <Download className="w-4 h-4" />
              <span className="font-mono font-bold">
                {photoIds.length === 1
                  ? 'Download 1 photo'
                  : `Download all ${photoIds.length} photos`}
              </span>
            </button>
          )}

          {/* Toggle Select Mode */}
          {photoIds.length > 1 && (
            <button
              onClick={() => {
                setIsSelectMode(!isSelectMode);
                setSelectedPhotoIds(new Set());
              }}
              className="btn-tactile"
              style={{
                padding: '10px 16px',
                fontSize: '14px',
                backgroundColor: isSelectMode ? 'var(--text)' : 'var(--panel)',
                color: isSelectMode ? 'var(--bg)' : 'var(--text)',
              }}
            >
              {isSelectMode ? (
                <>
                  <X className="w-4 h-4" />
                  <span className="font-mono font-bold">Exit select</span>
                </>
              ) : (
                <>
                  <CheckSquare className="w-4 h-4" />
                  <span className="font-mono font-bold">Select</span>
                </>
              )}
            </button>
          )}

          {/* Drive Fallback Button (if Drive-sourced) */}
          {hasDrivePhotos && firstDriveUrl && (
            <a
              href={firstDriveUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-tactile"
              style={{ padding: '10px 16px', fontSize: '14px' }}
              title="Open folder in Google Drive"
            >
              <ExternalLink className="w-4 h-4 text-[var(--accent)]" />
              <span className="font-mono font-bold">Drive</span>
            </a>
          )}
        </div>
      </div>

      {/* Progress Dialog when Downloading */}
      {isDownloading && downloadProgress && (
        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-md flex items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
            <div>
              <p className="text-xs sm:text-sm font-semibold text-[var(--text-main)]">
                {hasDrivePhotos
                  ? `Downloading photo ${downloadProgress.current} of ${downloadProgress.total}...`
                  : `Creating zip: ${downloadProgress.current} of ${downloadProgress.total} photos...`}
              </p>
            </div>
          </div>

          <button
            onClick={handleCancelDownload}
            className="touch-target px-3 py-1.5 rounded-lg border border-[var(--border-color)] text-xs font-semibold text-[var(--text-muted)] hover:text-red-400 hover:border-red-400/40 transition-colors focus:outline-none focus-visible:ring-2"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Download Error Banner */}
      {downloadError && (
        <div className="p-3.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{downloadError}</span>
          </div>
          <button
            onClick={() => setDownloadError(null)}
            className="touch-target p-1 text-red-400 hover:text-red-300"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Confirmed Photos Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-[var(--text-muted)]">
            Confirmed Photos ({photoIds.length})
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
          {photoIds.map((pid, idx) => {
            const photo = photos[pid];
            if (!photo) return null;

            const isSelected = selectedPhotoIds.has(pid);
            const hasError = imageErrorMap[pid];

            return (
              <div
                key={pid}
                onClick={() => {
                  if (isSelectMode) {
                    toggleSelectPhoto(pid);
                  } else {
                    handleOpenModal(photoIds, idx);
                  }
                }}
                className={`group relative rounded-xl overflow-hidden glass-card aspect-[4/3] bg-[var(--bg-main)] cursor-pointer select-none transition-all duration-200 ${
                  isSelectMode && isSelected
                    ? 'ring-2 ring-[var(--color-accent)] border-transparent'
                    : 'border-[var(--border-color)]'
                }`}
              >
                {/* Thumbnail with lazy load and error fallback */}
                {hasError ? (
                  <div className="w-full h-full flex flex-col items-center justify-center p-2 text-center bg-[var(--bg-card)]">
                    {photo.drive_url || photo.drive_file_id ? (
                      <a
                        href={photo.drive_url || `https://drive.google.com/file/d/${photo.drive_file_id}/view`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="touch-target px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-sm inline-flex items-center gap-1"
                        title="Open photo in Google Drive"
                      >
                        <span>unavailable - open in Drive ↗</span>
                      </a>
                    ) : (
                      <div className="text-[var(--text-dim)] flex flex-col items-center">
                        <ImageOff className="w-6 h-6 mb-1 opacity-50" />
                        <span className="text-[11px]">Image unavailable</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <img
                    src={photo.thumb}
                    alt={photo.name}
                    loading="lazy"
                    onError={() =>
                      setImageErrorMap((prev) => ({ ...prev, [pid]: true }))
                    }
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                )}

                {/* Selection Tick Box Overlay in Select Mode */}
                {isSelectMode && (
                  <div className="absolute top-2 left-2 z-10">
                    <div
                      className={`w-6 h-6 rounded-lg flex items-center justify-center border shadow-sm transition-colors ${
                        isSelected
                          ? 'bg-[var(--color-accent)] border-[var(--color-accent)] text-[var(--color-accent-text)]'
                          : 'bg-[var(--bg-main)]/80 border-[var(--border-strong)] text-transparent'
                      }`}
                    >
                      <Check className="w-4 h-4 stroke-[3]" />
                    </div>
                  </div>
                )}

                {/* Hover / Action Overlay */}
                {!isSelectMode && (
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-2.5 flex flex-col justify-between pointer-events-none">
                    <div className="flex justify-end pointer-events-auto">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenModal(photoIds, idx);
                        }}
                        className="touch-target p-1.5 rounded-lg bg-black/60 text-white hover:bg-[var(--color-accent)] transition-colors focus:outline-none focus-visible:ring-2"
                        title="Zoom preview"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between gap-1 pointer-events-auto">
                      <span className="text-[11px] text-white font-mono truncate">
                        {photo.name}
                      </span>

                      {/* Per-Photo Download */}
                      {(photo.download || photo.download_url) && (
                        <a
                          href={photo.download || photo.download_url || undefined}
                          download={getCleanDownloadName(displayName, idx, photo.name)}
                          target={isDrivePhoto(photo) ? '_blank' : undefined}
                          rel={isDrivePhoto(photo) ? 'noopener noreferrer' : undefined}
                          onClick={(e) => e.stopPropagation()}
                          className="touch-target p-1.5 rounded-lg bg-black/60 text-white hover:bg-[var(--color-accent)] transition-colors flex-shrink-0 focus:outline-none focus-visible:ring-2 flex items-center justify-center"
                          title="Download photo"
                          aria-label={`Download ${photo.name}`}
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Sticky Bottom Bar in Select Mode */}
      {isSelectMode && (
        <div className="fixed bottom-0 inset-x-0 z-40 p-3 sm:p-4 glass-nav border-t border-[var(--border-color)] shadow-2xl animate-fadeIn">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs sm:text-sm font-semibold text-[var(--text-main)]">
                {selectedPhotoIds.size} of {photoIds.length} selected
              </span>
              <button
                onClick={handleSelectAll}
                className="touch-target px-2.5 py-1 text-xs font-semibold text-[var(--color-accent)] hover:underline focus:outline-none focus-visible:ring-2"
              >
                {selectedPhotoIds.size === photoIds.length ? 'Deselect all' : 'Select all'}
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setIsSelectMode(false);
                  setSelectedPhotoIds(new Set());
                }}
                className="touch-target px-3.5 py-2 rounded-xl border border-[var(--border-color)] text-xs sm:text-sm font-semibold text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors focus:outline-none focus-visible:ring-2"
              >
                Cancel
              </button>

              <button
                disabled={selectedPhotoIds.size === 0 || isDownloading}
                onClick={() => handleDownloadClick(Array.from(selectedPhotoIds))}
                className="touch-target inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)] font-semibold text-xs sm:text-sm shadow-sm hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-40 focus:outline-none focus-visible:ring-2"
              >
                <Download className="w-4 h-4" />
                <span>Download selected ({selectedPhotoIds.size})</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* "Possible matches" Section: NO download all button allowed! */}
      {includeMaybe && maybePhotos.length > 0 && (
        <div className="pt-6 border-t border-[var(--border-color)]">
          <div className="mb-3">
            <h3 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-amber-400" />
              Possible matches ({maybePhotos.length})
            </h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
            {maybePhotos.map((mItem, idx) => {
              const photo = photos[mItem.photo_id];
              if (!photo) return null;
              const maybeList = maybePhotos.map((m) => m.photo_id);

              return (
                <div
                  key={`${mItem.photo_id}-${idx}`}
                  onClick={() => handleOpenModal(maybeList, idx)}
                  className="group relative rounded-xl overflow-hidden glass-card border border-amber-500/30 hover:border-amber-400 aspect-[4/3] bg-[var(--bg-main)] cursor-pointer select-none transition-colors"
                >
                  <img
                    src={photo.thumb}
                    alt={photo.name}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />

                  {/* Badge top-left */}
                  <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-[var(--bg-main)]/90 border border-amber-500/30 text-[10px] font-semibold text-amber-300 pointer-events-none">
                    From {mItem.source_cluster}
                  </div>

                  {/* Hover Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-2.5 flex flex-col justify-between pointer-events-none">
                    <div className="flex justify-end pointer-events-auto">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenModal(maybeList, idx);
                        }}
                        className="touch-target p-1.5 rounded-lg bg-black/60 text-white hover:bg-amber-500 transition-colors focus:outline-none focus-visible:ring-2"
                        title="Zoom preview"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between gap-1 pointer-events-auto">
                      <span className="text-[11px] text-white font-mono truncate">
                        {photo.name}
                      </span>

                      {/* Per-Photo Download */}
                      {(photo.download || photo.download_url) && (
                        <a
                          href={photo.download || photo.download_url || undefined}
                          download={getCleanDownloadName(displayName, idx, photo.name)}
                          target={isDrivePhoto(photo) ? '_blank' : undefined}
                          rel={isDrivePhoto(photo) ? 'noopener noreferrer' : undefined}
                          onClick={(e) => e.stopPropagation()}
                          className="touch-target p-1.5 rounded-lg bg-black/60 text-white hover:bg-amber-500 transition-colors flex-shrink-0 focus:outline-none focus-visible:ring-2 flex items-center justify-center"
                          title="Download photo"
                          aria-label={`Download ${photo.name}`}
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* One-Time Google Drive Multi-Download Permission Notice Modal */}
      {showDriveNoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="max-w-md w-full p-5 sm:p-6 rounded-2xl glass-card border border-[var(--border-strong)] bg-[var(--bg-main)] shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--color-accent)]/20 text-[var(--color-accent)] flex items-center justify-center flex-shrink-0">
                <Download className="w-5 h-5" />
              </div>
              <h3 className="text-base sm:text-lg font-bold text-[var(--text-main)]">
                Downloading Drive Photos
              </h3>
            </div>

            <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
              Photos from Google Drive will download one by one. Your browser may display a prompt asking to <strong>allow multiple file downloads</strong>. Please click <strong>Allow</strong> to proceed.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-end gap-2.5 pt-2">
              {firstDriveUrl && (
                <a
                  href={firstDriveUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="touch-target w-full sm:w-auto px-3.5 py-2 rounded-xl border border-[var(--border-color)] text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors inline-flex items-center justify-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open in Drive instead</span>
                </a>
              )}

              <button
                onClick={handleConfirmDriveDownload}
                className="touch-target w-full sm:w-auto px-4 py-2 rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)] text-xs font-bold shadow-sm hover:brightness-105 transition-all"
              >
                Continue Download
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Preview */}
      {modalState !== null && activePhoto && activePhotoId && (
        <PhotoModal
          photo={activePhoto}
          photoId={activePhotoId}
          hasPrev={modalState.index > 0}
          hasNext={modalState.index < modalState.list.length - 1}
          onPrev={handlePrev}
          onNext={handleNext}
          onClose={handleCloseModal}
          personLabel={displayName}
        />
      )}
    </div>
  );
};
export default PhotoGallery;
