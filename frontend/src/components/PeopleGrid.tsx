import React, { useState, useMemo } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { Search, Users, CheckSquare, Square, X, Download } from 'lucide-react';
import { MascotSticker } from './MascotSticker';

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
  theme?: string;
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
  theme = 't-dark',
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
    <div className="space-y-6 animate-fadeIn" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Search and Filters Bar */}
      <div
        className="p-4 sm:p-5 rounded flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4"
        style={{
          background: 'var(--card-bg, var(--panel))',
          border: '1.5px solid var(--line)',
          boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
        }}
      >
        {/* Search Input */}
        <div className="relative flex-1">
          <Search
            className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: 'var(--muted)' }}
          />
          <input
            id="people-search-input"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search across ${people.length} people...`}
            className="riso-input w-full pl-11 pr-10"
            style={{ height: '46px', fontSize: '15px' }}
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 cursor-pointer"
              style={{ background: 'transparent', border: 'none', color: 'var(--muted)' }}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 self-start md:self-auto overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setFilterMode('all')}
            className="px-4 py-2 rounded text-sm font-bold transition-all cursor-pointer"
            style={{
              background: filterMode === 'all' ? 'var(--accent)' : 'var(--input)',
              color: filterMode === 'all' ? 'var(--on-accent)' : 'var(--text)',
              border: filterMode === 'all' ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
            }}
          >
            All ({people.length})
          </button>
          <button
            onClick={() => setFilterMode('multiple')}
            className="px-4 py-2 rounded text-sm font-bold transition-all cursor-pointer"
            style={{
              background: filterMode === 'multiple' ? 'var(--accent)' : 'var(--input)',
              color: filterMode === 'multiple' ? 'var(--on-accent)' : 'var(--text)',
              border: filterMode === 'multiple' ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
            }}
          >
            Multi-photo ({multipleCount})
          </button>
          <button
            onClick={() => setFilterMode('single')}
            className="px-4 py-2 rounded text-sm font-bold transition-all cursor-pointer"
            style={{
              background: filterMode === 'single' ? 'var(--accent)' : 'var(--input)',
              color: filterMode === 'single' ? 'var(--on-accent)' : 'var(--text)',
              border: filterMode === 'single' ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
            }}
          >
            Singletons ({singleCount})
          </button>
        </div>
      </div>

      {/* Floating / Sticky Merge Action Banner */}
      {selectedIds.size > 0 && (
        <div
          id="merge-action-banner"
          className="sticky top-20 z-30 p-4 sm:p-5 rounded flex items-center justify-between gap-4 animate-scaleUp"
          style={{
            background: 'var(--panel)',
            border: '2px solid var(--accent)',
            boxShadow: '2px 4px 0px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div className="flex items-center gap-3.5">
            <div
              className="w-10 h-10 rounded flex items-center justify-center font-bold text-base flex-shrink-0"
              style={{
                background: 'var(--accent)',
                color: 'var(--on-accent)',
              }}
            >
              {selectedIds.size}
            </div>
            <div>
              <p className="text-base sm:text-lg font-bold" style={{ color: 'var(--text)' }}>
                {selectedIds.size} {selectedIds.size === 1 ? 'person' : 'people'} selected
              </p>
              <p className="text-sm mt-0.5" style={{ color: 'var(--muted)' }}>
                {selectedIds.size < 2
                  ? 'Select at least 2 people to merge into a single person'
                  : 'Ready to combine all faces and photos into one person'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              id="clear-selection-btn"
              onClick={onClearSelection}
              className="riso-btn-sec"
              style={{ height: '44px', padding: '0 18px', fontSize: '14px' }}
            >
              Clear
            </button>
            <button
              id="merge-selected-btn"
              disabled={selectedIds.size < 2 || isMerging}
              onClick={onMergeSelected}
              className="btn pri"
              style={{
                height: '44px',
                padding: '0 24px',
                borderRadius: '4px',
                fontSize: '15px',
                fontWeight: 800,
                opacity: selectedIds.size < 2 || isMerging ? 0.45 : 1,
                cursor: selectedIds.size < 2 || isMerging ? 'not-allowed' : 'pointer',
                boxShadow: '2px 3px 0px rgba(0,0,0,0.25)',
              }}
            >
              <Users className="w-4 h-4 mr-1.5" />
              <span>{isMerging ? 'Merging...' : `Merge Selected (${selectedIds.size})`}</span>
            </button>
          </div>
        </div>
      )}

      {/* Grid of People Cards */}
      {filteredPeople.length === 0 ? (
        <div
          id="people-empty-state"
          data-testid="people-empty-state"
          className="p-12 sm:p-16 rounded-lg text-center space-y-4"
          style={{
            background: 'var(--card-bg, var(--panel))',
            border: '2px dashed var(--line)',
            color: 'var(--muted)',
            boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
          }}
        >
          <div className="w-24 h-24 mx-auto rounded-2xl bg-[var(--input)] border-2 border-[var(--line)] flex items-center justify-center p-2 shadow-[2px_2px_0px_var(--line)]">
            <MascotSticker pose={8} theme={theme} className="w-full h-full object-contain" />
          </div>
          <h3 className="text-xl font-black font-mono uppercase" style={{ color: 'var(--text)' }}>
            {people.length === 0 ? 'No People Clusters Yet' : 'No People Match Filters'}
          </h3>
          <p className="text-sm max-w-md mx-auto leading-relaxed">
            {people.length === 0
              ? 'Our mascot is snoozing while waiting for photos to organize! Go to the Source tab to scan an event album or open a saved project.'
              : 'Try clearing the search query or switching the multiple/single photo filters above.'}
          </p>
        </div>
      ) : (
        <div
          id="people-cards-grid"
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4"
        >
          {filteredPeople.map((person) => {
            const isSelected = selectedIds.has(person.id);
            const photoCount = person.photo_count || person.photo_ids?.length || 0;
            const displayName = person.label || person.id;

            return (
              <div
                key={person.id}
                id={`person-card-${person.id}`}
                data-testid="person-card"
                onClick={() => onSelectPerson(person)}
                className="group relative rounded overflow-hidden transition-all duration-150 cursor-pointer flex flex-col"
                style={{
                  background: isSelected ? 'var(--panel)' : 'var(--card-bg, var(--panel))',
                  border: isSelected ? '2.5px solid var(--accent)' : '1.5px solid var(--line)',
                  boxShadow: isSelected ? '2px 4px 0px var(--accent)' : '2px 3px 0px rgba(0, 0, 0, 0.2)',
                }}
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
                  className="absolute top-2 left-2 z-10 w-7 h-7 rounded flex items-center justify-center transition-all"
                  style={{
                    background: isSelected ? 'var(--accent)' : 'rgba(0,0,0,0.65)',
                    color: isSelected ? 'var(--on-accent)' : 'var(--muted)',
                    border: isSelected ? 'none' : '1px solid var(--line)',
                    cursor: 'pointer',
                  }}
                >
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4" />
                  ) : (
                    <Square className="w-4 h-4" />
                  )}
                </button>

                {/* Photo Count Badge */}
                <div
                  className="absolute top-2 right-2 z-10 px-2 py-0.5 rounded text-xs font-mono font-bold"
                  style={{
                    background: 'var(--panel)',
                    border: '1px solid var(--line)',
                    color: 'var(--text)',
                  }}
                >
                  {photoCount} {photoCount === 1 ? 'photo' : 'photos'}
                </div>

                {/* Face Thumbnail */}
                <div className="relative aspect-square w-full overflow-hidden" style={{ background: 'var(--input)' }}>
                  <img
                    src={person.face}
                    alt={displayName}
                    loading="lazy"
                    className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                  />
                </div>

                {/* Footer details */}
                <div
                  className="p-3 flex flex-col justify-between flex-1"
                  style={{
                    background: 'var(--card-bg)',
                    borderTop: '1px solid var(--line)',
                  }}
                >
                  <div className="min-w-0">
                    <p
                      className="text-sm sm:text-base font-bold font-mono truncate"
                      style={{ color: 'var(--text)' }}
                      title={displayName}
                    >
                      {displayName}
                    </p>
                    {person.label && (
                      <p className="text-xs font-mono truncate mt-0.5" style={{ color: 'var(--muted)' }}>
                        {person.id}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-2 pt-1 border-t border-[var(--line)]">
                    <p className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                      {person.faces?.length || photoCount} detected face{person.faces?.length === 1 ? '' : 's'}
                    </p>
                    <a
                      href={`/api/people/${person.id}/download-zip`}
                      download={`${(person.label || person.id).replace(/[^a-zA-Z0-9_-]/g, '_')}_photos.zip`}
                      onClick={(e) => e.stopPropagation()}
                      className="p-1 rounded text-xs flex items-center gap-1 font-mono hover:text-[var(--accent)] transition-colors"
                      style={{ color: 'var(--muted)' }}
                      title={`Download all ${photoCount} photos for ${displayName}`}
                    >
                      <Download className="w-3.5 h-3.5 text-[var(--accent)]" />
                      <span className="text-[11px]">ZIP</span>
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
