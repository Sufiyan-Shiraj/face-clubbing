import React, { useState, useMemo } from 'react';
import { UnrecognizedGroup, PhotoInfo } from '../types';
import { ArrowLeft, ZoomIn, HelpCircle, ImageOff } from 'lucide-react';
import { PhotoModal } from './PhotoModal';

interface UnrecognizedGalleryProps {
  unrecognized: UnrecognizedGroup;
  photos: Record<string, PhotoInfo>;
  onBack: () => void;
}

export const UnrecognizedGallery: React.FC<UnrecognizedGalleryProps> = ({
  unrecognized,
  photos,
  onBack,
}) => {
  const [selectedPhotoId, setSelectedPhotoId] = useState<string | null>(null);

  // Separate face crops and photos
  const faceCrops = unrecognized.faces || [];
  const facePhotoIdSet = useMemo(() => new Set(faceCrops.map((f) => f.photo_id)), [faceCrops]);
  const noFacePhotoIds = useMemo(
    () => (unrecognized.photo_ids || []).filter((pid) => !facePhotoIdSet.has(pid)),
    [unrecognized.photo_ids, facePhotoIdSet]
  );

  const allModalPhotoIds = useMemo(() => {
    const ids: string[] = [];
    for (const f of faceCrops) {
      if (!ids.includes(f.photo_id)) ids.push(f.photo_id);
    }
    for (const pid of noFacePhotoIds) {
      if (!ids.includes(pid)) ids.push(pid);
    }
    return ids;
  }, [faceCrops, noFacePhotoIds]);

  const currentIndex = selectedPhotoId ? allModalPhotoIds.indexOf(selectedPhotoId) : -1;
  const activePhoto = selectedPhotoId ? photos[selectedPhotoId] : null;

  const handlePrev = () => {
    if (currentIndex > 0) {
      setSelectedPhotoId(allModalPhotoIds[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    if (currentIndex >= 0 && currentIndex < allModalPhotoIds.length - 1) {
      setSelectedPhotoId(allModalPhotoIds[currentIndex + 1]);
    }
  };

  return (
    <div className="space-y-6 pb-20 animate-fadeIn">
      {/* Top Banner: Notice NO "Download all" button here! */}
      <div
        className="p-4 sm:p-5 rounded-xl glass-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        style={{
          background: 'var(--panel)',
          border: '2px solid var(--line)',
          boxShadow: '4px 4px 0px var(--line)',
        }}
      >
        <div className="flex items-center gap-3.5">
          <button
            onClick={onBack}
            className="btn-tactile btn-sm"
            title="Back to all people"
            aria-label="Back to all people"
            style={{ padding: '8px 12px' }}
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono font-bold hidden sm:inline">Back</span>
          </button>

          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 border-2 border-[var(--line)] shadow-[2px_2px_0px_var(--line)]"
            style={{ background: 'var(--bg)', color: 'var(--accent)' }}
          >
            <HelpCircle className="w-6 h-6" />
          </div>

          <div>
            <h2 className="text-xl sm:text-2xl font-black font-mono text-[var(--text)] tracking-tight">
              Unrecognized Faces ({faceCrops.length})
            </h2>
          </div>
        </div>

        <button
          onClick={onBack}
          className="btn-tactile btn-sm"
          style={{ padding: '8px 14px', fontSize: '13px' }}
        >
          View all people
        </button>
      </div>

      {/* Grid of Unrecognized Face Crops */}
      {faceCrops.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs sm:text-sm font-bold font-mono uppercase tracking-wider text-[var(--muted)]">
            Detected Face Crops ({faceCrops.length})
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2.5 sm:gap-3">
            {faceCrops.map((fItem, idx) => {
              return (
                <div
                  key={`${fItem.face_id || fItem.photo_id}-${idx}`}
                  onClick={() => setSelectedPhotoId(fItem.photo_id)}
                  className="group relative rounded-xl overflow-hidden glass-card aspect-square cursor-pointer select-none transition-all duration-200"
                  style={{
                    background: 'var(--panel)',
                    border: '2px solid var(--line)',
                    boxShadow: '2px 2px 0px var(--line)',
                  }}
                >
                  <img
                    src={fItem.face}
                    alt={fItem.file_name || fItem.face_id || 'Face'}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />

                  {fItem.rejection_reason && (
                    <div className="absolute bottom-1 inset-x-1 px-1.5 py-0.5 rounded bg-black/80 text-[9px] text-amber-300 truncate text-center font-mono">
                      {fItem.rejection_reason}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Photos without any detected faces */}
      {noFacePhotoIds.length > 0 && (
        <div className="space-y-3 pt-6 border-t-2 border-[var(--line)]">
          <h3 className="text-xs sm:text-sm font-bold font-mono uppercase tracking-wider text-[var(--muted)]">
            Photos Without Faces ({noFacePhotoIds.length})
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
            {noFacePhotoIds.map((pid) => {
              const photo = photos[pid];
              if (!photo) return null;

              return (
                <div
                  key={pid}
                  onClick={() => setSelectedPhotoId(pid)}
                  className="group relative rounded-xl overflow-hidden glass-card aspect-[4/3] cursor-pointer select-none transition-all duration-200"
                  style={{
                    background: 'var(--panel)',
                    border: '2px solid var(--line)',
                    boxShadow: '2px 2px 0px var(--line)',
                  }}
                >
                  <img
                    src={photo.thumb}
                    alt={photo.name}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-2 flex items-end">
                    <span className="text-[11px] text-white font-mono truncate">
                      {photo.name}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Modal Preview */}
      {selectedPhotoId !== null && activePhoto && (
        <PhotoModal
          photo={activePhoto}
          photoId={selectedPhotoId}
          hasPrev={currentIndex > 0}
          hasNext={currentIndex < allModalPhotoIds.length - 1}
          onPrev={handlePrev}
          onNext={handleNext}
          onClose={() => setSelectedPhotoId(null)}
          personLabel="unrecognized"
        />
      )}
    </div>
  );
};
export default UnrecognizedGallery;
