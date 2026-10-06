import React, { useState } from 'react';
import { PersonCluster, UnrecognizedGroup } from '../types';
import { PersonCard } from './PersonCard';
import { HelpCircle, Filter } from 'lucide-react';

interface PeopleGridProps {
  people: PersonCluster[];
  unrecognized: UnrecognizedGroup;
  searchQuery: string;
  showLabels?: boolean;
  hideSinglePhotoDefault?: boolean;
  onSelectPerson: (person: PersonCluster) => void;
  onSelectUnrecognized: () => void;
}

export const PeopleGrid: React.FC<PeopleGridProps> = ({
  people,
  unrecognized,
  searchQuery,
  showLabels = true,
  hideSinglePhotoDefault = false,
  onSelectPerson,
  onSelectUnrecognized,
}) => {
  // Toggle: Hide single-photo people (initial state from config)
  const [hideSinglePhoto, setHideSinglePhoto] = useState(hideSinglePhotoDefault);

  // 1. Filter by search query
  const searchFiltered = people.filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const idMatch = p.id.toLowerCase().includes(q);
    const labelMatch = p.label ? p.label.toLowerCase().includes(q) : false;
    return idMatch || labelMatch;
  });

  // Count how many single-photo people exist
  const singlePhotoCount = searchFiltered.filter((p) => p.photo_ids.length === 1).length;

  // 2. Filter by single-photo toggle (no cluster is ever removed from underlying data)
  const displayedPeople = hideSinglePhoto
    ? searchFiltered.filter((p) => p.photo_ids.length > 1)
    : searchFiltered;

  return (
    <div className="space-y-6 pb-12">
      {/* Header Controls Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-neutral-800/60">
        <div>
          <h2 className="text-lg sm:text-xl font-semibold text-white tracking-tight">
            People ({displayedPeople.length})
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Sorted by photo count
            {hideSinglePhoto && singlePhotoCount > 0 && ` • ${singlePhotoCount} single-photo people hidden`}
          </p>
        </div>

        {/* Toggle: Hide single-photo people */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2.5 cursor-pointer select-none group">
            <span className="text-xs sm:text-sm text-neutral-300 group-hover:text-white font-medium transition-colors flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-neutral-400 group-hover:text-neutral-300" />
              Hide single-photo people
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={hideSinglePhoto}
              onClick={() => setHideSinglePhoto(!hideSinglePhoto)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-neutral-900 ${
                hideSinglePhoto ? 'bg-accent' : 'bg-neutral-700 hover:bg-neutral-600'
              }`}
            >
              <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                  hideSinglePhoto ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </label>
        </div>
      </div>

      {/* Unified Single People Grid */}
      {displayedPeople.length === 0 && !searchQuery ? (
        <p className="text-neutral-500 text-sm">No people discovered.</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4">
          {displayedPeople.map((person) => (
            <PersonCard
              key={person.id}
              person={person}
              showLabel={showLabels}
              onClick={() => onSelectPerson(person)}
            />
          ))}

          {/* Unrecognized Category Card at end of grid */}
          <button
            onClick={onSelectUnrecognized}
            className="group relative flex flex-col items-center text-center p-3 rounded-2xl glass-card focus:outline-none focus:ring-2 focus:ring-accent border-dashed border-neutral-700/80 hover:border-amber-500/80 hover:shadow-[0_0_20px_rgba(245,158,11,0.2)] transition-all duration-300 w-full"
            aria-label={`View ${unrecognized.faces?.length || 0} unrecognized faces`}
          >
            <div className="relative w-full aspect-square rounded-xl bg-neutral-900/90 border border-neutral-800 flex flex-col items-center justify-center text-neutral-400 group-hover:text-amber-400 transition-colors p-4">
              <HelpCircle className="w-10 h-10 mb-2 stroke-[1.5]" />
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-300 group-hover:text-amber-300">
                Unrecognized
              </span>
              
              <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-neutral-950/80 backdrop-blur-md text-amber-300/90 border border-amber-500/20 shadow-sm">
                {unrecognized.faces?.length || 0} faces
              </div>
            </div>

            {showLabels && (
              <div className="mt-2.5 w-full px-1">
                <p className="text-xs sm:text-sm font-medium text-neutral-400 group-hover:text-amber-400 transition-colors truncate">
                  Review Unattached Faces
                </p>
              </div>
            )}
          </button>
        </div>
      )}

      {/* Empty State when search yields nothing */}
      {displayedPeople.length === 0 && searchQuery && (
        <div className="text-center py-16 text-neutral-400">
          <p className="text-base">No people found matching "{searchQuery}".</p>
        </div>
      )}
    </div>
  );
};
