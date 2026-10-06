import React, { useState, useMemo } from 'react';
import { UnrecognizedGroup, PhotoInfo } from '../types';
import { ArrowLeft, ZoomIn, HelpCircle, ImageOff, UserX } from 'lucide-react';
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

  // 1. Separate face crops and photos with no detected faces
  const faceCrops = unrecognized.faces || [];
  const facePhotoIdSet = useMemo(() => new Set(faceCrops.map((f) => f.photo_id)), [faceCrops]);
  const noFacePhotoIds = useMemo(
    () => (unrecognized.photo_ids || []).filter((pid) => !facePhotoIdSet.has(pid)),
    [unrecognized.photo_ids, facePhotoIdSet]
  );

  // Ordered list of photo IDs for modal prev/next navigation
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
    <div className="space-y-8 pb-16 animate-fadeIn">
      {/* Top Banner */}
      <div className="p-4 sm:p-6 rounded-2xl glass-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-amber-500/20">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-300 hover:text-white hover:bg-neutral-800 transition-colors"
            title="Back to all people"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <HelpCircle className="w-7 h-7" />
          </div>

          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <span>Unrecognized Faces</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-medium">
                {faceCrops.length} faces
              </span>
            </h2>
            <p className="text-xs sm:text-sm text-neutral-400 mt-0.5">
              Faces that could not attach to any cluster (profile angles, small faces, low confidence).
            </p>
          </div>
        </div>

        <button
          onClick={onBack}
          className="text-xs sm:text-sm text-neutral-400 hover:text-white font-medium transition-colors"
        >
          View all people
        </button>
      </div>

      {/* 1. Unrecognized Face Crops Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-white tracking-tight flex items-center gap-2">
            <UserX className="w-5 h-5 text-amber-400" />
            <span>Unattached Face Crops</span>
            <span className="text-xs font-normal text-neutral-400">
              ({faceCrops.length} crops — click to open photo)
            </span>
          </h3>
        </div>

        {faceCrops.length === 0 ? (
          <p className="text-neutral-500 text-sm">No unrecognized face crops found.</p>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2.5 sm:gap-3">
            {faceCrops.map((item, idx) => {
              const photo = photos[item.photo_id];
              return (
                <div
                  key={`${item.face}-${idx}`}
                  onClick={() => setSelectedPhotoId(item.photo_id)}
                  className="group relative rounded-xl overflow-hidden glass-card border border-neutral-800 bg-neutral-900 aspect-square cursor-pointer hover:border-amber-500/60 hover:shadow-[0_0_15px_rgba(245,158,11,0.2)] transition-all duration-300"
                  title={`Click to open ${photo ? photo.name : item.photo_id}`}
                >
                  <img
                    src={item.face}
                    alt={photo?.name || 'Unrecognized face'}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />

                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-1.5 flex flex-col justify-end pointer-events-none">
                    <span className="text-[10px] text-white/90 truncate font-mono">
                      {photo?.name || item.photo_id}
                    </span>
                  </div>

                  <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                    <span className="p-1 rounded-md bg-black/60 text-amber-300 inline-block">
                      <ZoomIn className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 2. Photos with No Detected Face (Separate Small List) */}
      {noFacePhotoIds.length > 0 && (
        <div className="pt-6 border-t border-neutral-800/80">
          <div className="p-4 sm:p-5 rounded-2xl glass-card border-neutral-800 bg-neutral-900/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <ImageOff className="w-5 h-5 text-neutral-400" />
                <h3 className="text-base sm:text-lg font-semibold text-white tracking-tight">
                  Photos With No Detected Face
                </h3>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-800 text-neutral-300 border border-neutral-700/50">
                {noFacePhotoIds.length} {noFacePhotoIds.length === 1 ? 'photo' : 'photos'}
              </span>
            </div>

            <p className="text-xs text-neutral-400">
              Captures without human faces (scenic or room shots). Click to view full photo.
            </p>

            {/* Small compact list */}
            <div className="divide-y divide-neutral-800/80 border border-neutral-800/90 rounded-xl overflow-hidden bg-neutral-950/70 mt-2">
              {noFacePhotoIds.map((pid) => {
                const photo = photos[pid];
                if (!photo) return null;

                return (
                  <div
                    key={pid}
                    onClick={() => setSelectedPhotoId(pid)}
                    className="group flex items-center justify-between p-2.5 sm:p-3 hover:bg-neutral-800/50 cursor-pointer transition-colors"
                    title={`View ${photo.name}`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <img
                        src={photo.thumb}
                        alt={photo.name}
                        loading="lazy"
                        className="w-10 h-10 sm:w-11 sm:h-11 rounded-lg object-cover border border-neutral-800 flex-shrink-0 group-hover:border-accent transition-colors"
                      />
                      <div className="min-w-0">
                        <p className="text-xs sm:text-sm font-medium text-neutral-200 group-hover:text-white truncate font-mono">
                          {photo.name}
                        </p>
                        <p className="text-[11px] text-neutral-400">
                          {photo.width && photo.height ? `${photo.width} × ${photo.height} px • ` : ''}No face detected
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-neutral-400 group-hover:text-accent flex-shrink-0 pl-2">
                      <span className="hidden sm:inline text-[11px]">View photo</span>
                      <ZoomIn className="w-4 h-4" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Photo Modal */}
      {selectedPhotoId && activePhoto && (
        <PhotoModal
          photo={activePhoto}
          photoId={selectedPhotoId}
          hasPrev={currentIndex > 0}
          hasNext={currentIndex < allModalPhotoIds.length - 1}
          onPrev={handlePrev}
          onNext={handleNext}
          onClose={() => setSelectedPhotoId(null)}
        />
      )}
    </div>
  );
};
