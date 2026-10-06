import React, { useState, useMemo } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { Search, Users, CheckSquare, Square, X, Filter } from 'lucide-react';

interface PeopleGridProps {
  people: PersonCluster[];
  photos: Record<string, PhotoInfo>;
  selectedIds: Set<string>;
  onToggleSelect: (personId: string) => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onMergeSelected: () => void;
  onSelectPerson: (person: PersonCluster) => void;
  isMerging?: boolean;
}

export const PeopleGrid: React.FC<PeopleGridProps> = ({
  people,
  photos,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onClearSelection,
  onMergeSelected,
  onSelectPerson,
  isMerging = false,
}) => {
  const [search, setSearch] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'multiple' | 'single'>('all');

  const filteredPeople = useMemo(() => {
    return people.filter((p) => {
      // Photo count check
      const photoCount = p.photo_count || p.photo_ids?.length || 0;
      if (filterMode === 'multiple' && photoCount <= 1) return false;
      if (filterMode === 'single' && photoCount !== 1) return false;

      // Search check
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      const label = (p.label || '').toLowerCase();
      const id = (p.id || '').toLowerCase();
      return label.includes(q) || id.includes(q);
    });
  }, [people, search, filterMode]);

  const multipleCount = useMemo(
    () => people.filter((p) => (p.photo_count || p.photo_ids?.length || 0) > 1).length,
    [people]
  );
  const singleCount = useMemo(
    () => people.filter((p) => (p.photo_count || p.photo_ids?.length || 0) === 1).length,
    [people]
  );

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Search and Filters Bar */}
      <div className="glass-card p-4 rounded-2xl flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            id="people-search-input"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search across ${people.length} people...`}
            className="w-full pl-10 pr-4 py-2 bg-neutral-900/90 border border-neutral-800 rounded-xl text-neutral-200 placeholder-neutral-500 text-sm focus:outline-none focus:border-accent"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 self-start md:self-auto overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterMode === 'all'
                ? 'bg-neutral-800 text-white border border-neutral-700'
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/60'
            }`}
          >
            All ({people.length})
          </button>
          <button
            onClick={() => setFilterMode('multiple')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterMode === 'multiple'
                ? 'bg-neutral-800 text-white border border-neutral-700'
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/60'
            }`}
          >
            Multi-photo ({multipleCount})
          </button>
          <button
            onClick={() => setFilterMode('single')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterMode === 'single'
                ? 'bg-neutral-800 text-white border border-neutral-700'
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/60'
            }`}
          >
            Singletons ({singleCount})
          </button>
        </div>
      </div>

      {/* Floating / Sticky Merge Action Banner */}
      {selectedIds.size > 0 && (
        <div
          id="merge-action-banner"
          className="sticky top-20 z-30 glass-card border border-accent/40 bg-neutral-900/95 p-3 sm:p-4 rounded-2xl shadow-2xl flex items-center justify-between gap-4 animate-scaleUp"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/40 flex items-center justify-center text-accent font-bold text-sm">
              {selectedIds.size}
            </div>
            <div>
              <p className="text-sm font-semibold text-white">
                {selectedIds.size} {selectedIds.size === 1 ? 'person' : 'people'} selected
              </p>
              <p className="text-xs text-neutral-400">
                {selectedIds.size < 2
                  ? 'Select at least 2 people to merge into a single person'
                  : 'Ready to combine all faces and photos into one person'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              id="clear-selection-btn"
              onClick={onClearSelection}
              className="px-3 py-1.5 rounded-xl border border-neutral-700 text-neutral-300 hover:text-white hover:bg-neutral-800 text-xs font-medium transition-all"
            >
              Clear
            </button>
            <button
              id="merge-selected-btn"
              disabled={selectedIds.size < 2 || isMerging}
              onClick={onMergeSelected}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-2 transition-all shadow-lg ${
                selectedIds.size >= 2 && !isMerging
                  ? 'bg-accent text-white hover:brightness-110 shadow-accent/20 cursor-pointer'
                  : 'bg-neutral-800 text-neutral-500 cursor-not-allowed border border-neutral-700/50'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>{isMerging ? 'Merging...' : `Merge Selected (${selectedIds.size})`}</span>
            </button>
          </div>
        </div>
      )}

      {/* Grid of People Cards */}
      {filteredPeople.length === 0 ? (
        <div className="glass-card p-12 rounded-2xl text-center space-y-3">
          <Users className="w-10 h-10 text-neutral-500 mx-auto" />
          <h3 className="text-base font-semibold text-neutral-300">No people found</h3>
          <p className="text-xs text-neutral-500 max-w-sm mx-auto">
            Try adjusting your search query or filter settings above.
          </p>
        </div>
      ) : (
        <div
          id="people-cards-grid"
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4"
        >
          {filteredPeople.map((person) => {
            const isSelected = selectedIds.has(person.id);
            const photoCount = person.photo_count || person.photo_ids?.length || 0;
            const displayName = person.label || person.id;

            return (
              <div
                key={person.id}
                id={`person-card-${person.id}`}
                onClick={() => onSelectPerson(person)}
                className={`group relative glass-card rounded-2xl overflow-hidden border transition-all duration-200 cursor-pointer flex flex-col ${
                  isSelected
                    ? 'border-accent bg-accent/5 ring-2 ring-accent/30 shadow-lg'
                    : 'border-neutral-800/80 hover:border-neutral-700 hover:bg-neutral-900/90'
                }`}
              >
                {/* Selection Checkbox Overlay */}
                <button
                  type="button"
                  id={`select-person-${person.id}`}
                  aria-label={`Select ${displayName}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleSelect(person.id);
                  }}
                  className={`absolute top-2 left-2 z-10 p-1.5 rounded-lg transition-all ${
                    isSelected
                      ? 'bg-accent text-white shadow-md'
                      : 'bg-black/60 text-neutral-400 hover:text-white backdrop-blur-sm opacity-60 group-hover:opacity-100'
                  }`}
                >
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-white" />
                  ) : (
                    <Square className="w-4 h-4" />
                  )}
                </button>

                {/* Photo Count Badge */}
                <div className="absolute top-2 right-2 z-10 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md border border-white/10 text-[10px] font-medium text-neutral-200">
                  {photoCount} {photoCount === 1 ? 'photo' : 'photos'}
                </div>

                {/* Face Thumbnail */}
                <div className="relative aspect-square w-full bg-neutral-950 overflow-hidden">
                  <img
                    src={person.face}
                    alt={displayName}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                {/* Footer details */}
                <div className="p-2.5 sm:p-3 flex flex-col justify-between flex-1">
                  <div className="min-w-0">
                    <p
                      className="text-xs sm:text-sm font-semibold text-neutral-200 group-hover:text-white truncate"
                      title={displayName}
                    >
                      {displayName}
                    </p>
                    {person.label && (
                      <p className="text-[10px] text-neutral-500 font-mono truncate">{person.id}</p>
                    )}
                  </div>
                  <p className="text-[10px] text-neutral-400 mt-1">
                    {person.faces?.length || photoCount} detected face{person.faces?.length === 1 ? '' : 's'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
