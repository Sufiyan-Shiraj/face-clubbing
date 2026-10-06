import React, { useState } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { ArrowLeft, Download, ZoomIn, HelpCircle } from 'lucide-react';
import { PhotoModal } from './PhotoModal';

interface PhotoGalleryProps {
  person: PersonCluster;
  photos: Record<string, PhotoInfo>;
  onBack: () => void;
}

export const PhotoGallery: React.FC<PhotoGalleryProps> = ({
  person,
  photos,
  onBack,
}) => {
  const [modalState, setModalState] = useState<{
    list: string[];
    index: number;
  } | null>(null);

  const displayName = person.label || person.id.toUpperCase();
  const photoIds = person.photos || person.photo_ids;
  const maybePhotos = person.maybe_photos || [];

  const handleOpenModal = (list: string[], idx: number) => {
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

  return (
    <div className="space-y-8 pb-16 animate-fadeIn">
      {/* Top Profile Banner */}
      <div className="p-4 sm:p-6 rounded-2xl glass-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-300 hover:text-white hover:bg-neutral-800 transition-colors"
            title="Back to all people"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <img
            src={person.face}
            alt={displayName}
            className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl object-cover border border-neutral-700/80 shadow-md"
          />

          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              {displayName}
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400">
              Appears in {photoIds.length} {photoIds.length === 1 ? 'photo' : 'photos'}
              {maybePhotos.length > 0 && ` • ${maybePhotos.length} possible additional`}
            </p>
          </div>
        </div>

        <button
          onClick={onBack}
          className="text-xs sm:text-sm text-neutral-400 hover:text-accent font-medium transition-colors"
        >
          View all people
        </button>
      </div>

      {/* Confirmed Photos Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-300">
            Confirmed Photos ({photoIds.length})
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
          {photoIds.map((pid, idx) => {
            const photo = photos[pid];
            if (!photo) return null;

            return (
              <div
                key={pid}
                className="group relative rounded-xl overflow-hidden glass-card border border-neutral-800 aspect-[4/3] bg-neutral-900"
              >
                {/* Thumbnail with lazy load */}
                <img
                  src={photo.thumb}
                  alt={photo.name}
                  loading="lazy"
                  onClick={() => handleOpenModal(photoIds, idx)}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 cursor-pointer"
                />

                {/* Hover Overlay with filename & actions */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-2.5 flex flex-col justify-between pointer-events-none">
                  <div className="flex justify-end pointer-events-auto">
                    <button
                      onClick={() => handleOpenModal(photoIds, idx)}
                      className="p-1.5 rounded-lg bg-black/60 text-white hover:bg-accent transition-colors"
                      title="Zoom preview"
                    >
                      <ZoomIn className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex items-center justify-between gap-1 pointer-events-auto">
                    <span className="text-[11px] text-white/90 truncate font-mono">
                      {photo.name}
                    </span>

                    {photo.download && (
                      <a
                        href={photo.download}
                        target="_blank"
                        rel="noopener noreferrer"
                        download={photo.name}
                        onClick={(e) => e.stopPropagation()}
                        className="p-1.5 rounded-lg bg-black/60 text-white hover:bg-accent transition-colors flex-shrink-0"
                        title="Download photo"
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

      {/* "May also include" Row/Section (Shown only when maybe_photos exist) */}
      {maybePhotos.length > 0 && (
        <div className="pt-6 border-t border-neutral-800/80">
          <div className="mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-amber-400" />
                May also include ({maybePhotos.length})
              </h3>
            </div>
            <p className="text-xs text-neutral-400 mt-0.5">
              Potential photo matches from connected visual similarity groups (cosine distance 0.50 – 0.60).
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
            {maybePhotos.map((mItem, idx) => {
              const photo = photos[mItem.photo_id];
              if (!photo) return null;
              const maybeList = maybePhotos.map((m) => m.photo_id);

              return (
                <div
                  key={`${mItem.photo_id}-${idx}`}
                  className="group relative rounded-xl overflow-hidden glass-card border border-amber-500/30 hover:border-amber-400/60 aspect-[4/3] bg-neutral-900 transition-colors"
                >
                  <img
                    src={photo.thumb}
                    alt={photo.name}
                    loading="lazy"
                    onClick={() => handleOpenModal(maybeList, idx)}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 cursor-pointer"
                  />

                  {/* Badge top-left: Source cluster & distance */}
                  <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-neutral-950/80 backdrop-blur-md border border-amber-500/30 text-[10px] font-medium text-amber-300 pointer-events-none">
                    From {mItem.source_cluster} • d: {mItem.distance.toFixed(2)}
                  </div>

                  {/* Hover Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-2.5 flex flex-col justify-between pointer-events-none">
                    <div className="flex justify-end pointer-events-auto">
                      <button
                        onClick={() => handleOpenModal(maybeList, idx)}
                        className="p-1.5 rounded-lg bg-black/60 text-white hover:bg-amber-500 transition-colors"
                        title="Zoom preview"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between gap-1 pointer-events-auto">
                      <span className="text-[11px] text-white/90 truncate font-mono">
                        {photo.name}
                      </span>

                      {photo.download && (
                        <a
                          href={photo.download}
                          target="_blank"
                          rel="noopener noreferrer"
                          download={photo.name}
                          onClick={(e) => e.stopPropagation()}
                          className="p-1.5 rounded-lg bg-black/60 text-white hover:bg-amber-500 transition-colors flex-shrink-0"
                          title="Download photo"
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
        />
      )}
    </div>
  );
};
