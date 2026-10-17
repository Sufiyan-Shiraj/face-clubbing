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
  const photoCount = (person.photos || person.photo_ids || []).length;

  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col items-center text-center p-3 rounded-2xl glass-card focus:outline-none focus-visible:ring-2 transition-all duration-200 w-full min-h-[44px]"
      aria-label={`View photos for ${displayName} (${photoCount} photos)`}
    >
      {/* Square Face Thumbnail Container */}
      <div className="relative w-full aspect-square rounded-xl overflow-hidden bg-[var(--bg-main)] border border-[var(--border-color)] group-hover:border-[var(--color-accent)] transition-all duration-200">
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 shimmer-placeholder" />
        )}

        {imageError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-[var(--text-dim)] bg-[var(--bg-main)]">
            <ImageIcon className="w-8 h-8 mb-1 opacity-50" />
            <span className="text-[10px] font-mono">No Preview</span>
          </div>
        ) : (
          <img
            src={person.face}
            alt={displayName}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            className={`w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Photo Count Badge (Overlay) */}
        <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-[var(--bg-main)]/90 text-[var(--text-main)] border border-[var(--border-color)] shadow-sm">
          {photoCount} {photoCount === 1 ? 'photo' : 'photos'}
        </div>
      </div>

      {/* Label / ID */}
      {showLabel && (
        <div className="mt-2.5 w-full px-1">
          <p className="text-xs sm:text-sm font-semibold text-[var(--text-main)] group-hover:text-[var(--color-accent)] transition-colors truncate">
            {displayName}
          </p>
        </div>
      )}
    </button>
  );
};
export default PersonCard;
