import React, { useState } from 'react';
import { PersonCluster } from '../types';
import { Image as ImageIcon } from 'lucide-react';

interface PersonCardProps {
  person: PersonCluster;
  showLabel?: boolean;
  onClick: () => void;
}

export const PersonCard: React.FC<PersonCardProps> = ({
  person,
  showLabel = true,
  onClick,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const displayName = person.label || person.id.toUpperCase();
  const photoCount = person.photo_ids.length;

  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col items-center text-center p-3 rounded-2xl glass-card focus:outline-none focus:ring-2 focus:ring-accent transition-all duration-300 w-full"
      aria-label={`View photos for ${displayName} (${photoCount} photos)`}
    >
      {/* Square Face Thumbnail Container */}
      <div className="relative w-full aspect-square rounded-xl overflow-hidden bg-neutral-900 border border-neutral-800/80 group-hover:border-accent/60 group-hover:shadow-[0_0_20px_rgba(59,130,246,0.2)] transition-all duration-300">
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 shimmer-placeholder" />
        )}

        {imageError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-neutral-600 bg-neutral-900">
            <ImageIcon className="w-8 h-8 mb-1" />
            <span className="text-[10px] font-mono">No Preview</span>
          </div>
        ) : (
          <img
            src={person.face}
            alt={displayName}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Photo Count Badge (Overlay) */}
        <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-neutral-950/80 backdrop-blur-md text-white border border-white/10 shadow-sm">
          {photoCount} {photoCount === 1 ? 'photo' : 'photos'}
        </div>
      </div>

      {/* Label / ID */}
      {showLabel && (
        <div className="mt-2.5 w-full px-1">
          <p className="text-xs sm:text-sm font-medium text-neutral-200 group-hover:text-accent transition-colors truncate">
            {displayName}
          </p>
        </div>
      )}
    </button>
  );
};
