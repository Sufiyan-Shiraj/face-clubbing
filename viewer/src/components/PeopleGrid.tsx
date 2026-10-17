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
    <div className="space-y-5 pb-12">
      {/* Header Controls Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[var(--border-color)]">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-[var(--text-main)] tracking-tight">
            People ({displayedPeople.length})
          </h2>
        </div>

        {/* Toggle: Hide single-photo people */}
        <div className="flex items-center gap-3">
          <label className="touch-target flex items-center gap-2.5 cursor-pointer select-none group min-h-[44px]">
            <span className="text-xs sm:text-sm text-[var(--text-muted)] group-hover:text-[var(--text-main)] font-medium transition-colors flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-[var(--text-dim)]" />
              Hide single-photo people {singlePhotoCount > 0 ? `(${singlePhotoCount})` : ''}
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={hideSinglePhoto}
              onClick={() => setHideSinglePhoto(!hideSinglePhoto)}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 ${
                hideSinglePhoto ? 'bg-[var(--color-accent)]' : 'bg-[var(--border-strong)]'
              }`}
            >
              <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                  hideSinglePhoto ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </label>
        </div>
      </div>

      {/* People Grid */}
      {displayedPeople.length === 0 && !searchQuery ? (
        <p className="text-[var(--text-dim)] text-sm py-8 text-center">No people discovered.</p>
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
          {unrecognizedFaceCount > 0 && !searchQuery && (
            <button
              onClick={onSelectUnrecognized}
              className="group relative flex flex-col items-center text-center p-3 rounded-2xl glass-card border-dashed border-amber-500/40 hover:border-amber-400 focus:outline-none focus-visible:ring-2 transition-all duration-200 min-h-[44px]"
              aria-label={`View ${unrecognizedFaceCount} unrecognized faces`}
            >
              <div className="relative w-full aspect-square rounded-xl overflow-hidden bg-amber-500/10 border border-amber-500/30 flex flex-col items-center justify-center text-amber-400 group-hover:scale-105 transition-transform duration-200">
                <HelpCircle className="w-9 h-9 mb-1" />
                <span className="text-xs font-semibold">Unrecognized</span>
                <span className="text-[10px] text-amber-300 font-mono mt-0.5">
                  {unrecognizedFaceCount} faces
                </span>
              </div>
              <div className="mt-2.5 w-full px-1">
                <p className="text-xs sm:text-sm font-semibold text-amber-300 group-hover:text-amber-200 truncate">
                  Unrecognized Faces
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
