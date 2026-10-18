import React, { useState } from 'react';
import { PersonCluster, UnrecognizedGroup, PhotoInfo } from '../types';
import { PersonCard } from './PersonCard';
import { HelpCircle, Filter } from 'lucide-react';
import { MascotSticker } from './MascotSticker';

interface PeopleGridProps {
  people: PersonCluster[];
  unrecognized: UnrecognizedGroup;
  photos?: Record<string, PhotoInfo>;
  searchQuery: string;
  showLabels?: boolean;
  hideSinglePhotoDefault?: boolean;
  theme?: string;
  onSelectPerson: (person: PersonCluster) => void;
  onSelectUnrecognized: () => void;
  onDownloadPersonPhotos?: (person: PersonCluster) => void;
}

export const PeopleGrid: React.FC<PeopleGridProps> = ({
  people,
  unrecognized,
  photos = {},
  searchQuery,
  showLabels = true,
  hideSinglePhotoDefault = false,
  theme = 't-dark',
  onSelectPerson,
  onSelectUnrecognized,
  onDownloadPersonPhotos,
}) => {
  const [hideSinglePhoto, setHideSinglePhoto] = useState(hideSinglePhotoDefault);

  const searchFiltered = people.filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const idMatch = p.id.toLowerCase().includes(q);
    const labelMatch = p.label ? p.label.toLowerCase().includes(q) : false;
    return idMatch || labelMatch;
  });

  const singlePhotoCount = searchFiltered.filter(
    (p) => (p.photos || p.photo_ids || []).length === 1
  ).length;

  const displayedPeople = hideSinglePhoto
    ? searchFiltered.filter((p) => (p.photos || p.photo_ids || []).length > 1)
    : searchFiltered;

  const unrecognizedFaceCount = (unrecognized.faces || []).length;

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header Controls Toolbar */}
      <div
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b-2 border-[var(--line)]"
      >
        <div className="flex items-center gap-3">
          <h2 className="text-xl sm:text-2xl font-black font-mono tracking-tight text-[var(--text)] uppercase">
            People ({displayedPeople.length})
          </h2>
          {searchQuery && (
            <span className="badge-chip badge-accent">
              Filtering: "{searchQuery}"
            </span>
          )}
        </div>

        {/* Toggle: Hide single-photo people */}
        <div className="flex items-center gap-3">
          <label className="touch-target flex items-center gap-3 cursor-pointer select-none group min-h-[44px]">
            <span className="text-xs sm:text-sm font-mono text-[var(--muted)] group-hover:text-[var(--text)] font-bold transition-colors flex items-center gap-1.5">
              <Filter className="w-4 h-4 text-[var(--accent)]" />
              Hide single-photo people {singlePhotoCount > 0 ? `(${singlePhotoCount})` : ''}
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={hideSinglePhoto}
              onClick={() => setHideSinglePhoto(!hideSinglePhoto)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-[var(--line)] transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 ${
                hideSinglePhoto ? 'bg-[var(--accent)]' : 'bg-[var(--panel)]'
              }`}
            >
              <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-[var(--text)] shadow-md ring-0 transition duration-200 ease-in-out mt-0.5 ml-0.5 ${
                  hideSinglePhoto ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </label>
        </div>
      </div>

      {/* People Grid */}
      {displayedPeople.length === 0 ? (
        <div className="py-16 flex flex-col items-center justify-center text-center space-y-4">
          <MascotSticker pose={searchQuery ? 2 : 1} theme={theme} width={110} height={110} />
          <h3 className="text-lg font-bold font-mono text-[var(--text)]">
            {searchQuery ? `No matches found for "${searchQuery}"` : 'No people found'}
          </h3>
          <p className="text-sm font-mono text-[var(--muted)] max-w-sm">
            {searchQuery
              ? 'Try searching with another name or ID, or clear the search filter above.'
              : 'This gallery does not contain any indexed person clusters.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4">
          {displayedPeople.map((person) => (
            <PersonCard
              key={person.id}
              person={person}
              photos={photos}
              showLabel={showLabels}
              onClick={() => onSelectPerson(person)}
              onDownloadAll={onDownloadPersonPhotos}
            />
          ))}

          {/* Unrecognized Category Card at end of grid */}
          {unrecognizedFaceCount > 0 && !searchQuery && (
            <button
              onClick={onSelectUnrecognized}
              className="group relative flex flex-col items-center text-center p-3 rounded-xl glass-card border-dashed border-amber-500/60 hover:border-amber-400 focus:outline-none focus-visible:ring-2 transition-all duration-150 min-h-[44px] cursor-pointer"
              aria-label={`View ${unrecognizedFaceCount} unrecognized faces`}
              style={{
                background: 'var(--card-bg)',
                borderWidth: '2px',
                borderStyle: 'dashed',
                borderColor: 'var(--accent)',
              }}
            >
              <div
                className="relative w-full aspect-square rounded-lg overflow-hidden flex flex-col items-center justify-center border-2 border-[var(--line)] group-hover:scale-105 transition-transform duration-200"
                style={{
                  background: 'var(--panel)',
                }}
              >
                <HelpCircle className="w-10 h-10 mb-1 text-[var(--accent)]" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text)]">
                  Unrecognized
                </span>
                <span className="text-[11px] font-mono text-[var(--muted)] mt-1 font-bold">
                  {unrecognizedFaceCount} faces
                </span>
              </div>
              <div className="mt-2.5 w-full px-1">
                <p className="text-xs sm:text-sm font-bold font-mono text-[var(--accent)] group-hover:underline truncate">
                  Review Unrecognized
                </p>
              </div>
            </button>
          )}
        </div>
      )}
    </div>
  );
};
export default PeopleGrid;
