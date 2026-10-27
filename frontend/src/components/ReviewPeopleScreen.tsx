import React, { useState, useMemo, useEffect } from 'react';
import {
  PersonCluster,
  PhotoInfo,
  UnrecognizedData,
  SuggestionsData,
  WhatChangedResponse,
} from '../types';
import { api } from '../api/client';
import { PeopleGrid } from './PeopleGrid';
import { SuggestionReview } from './SuggestionReview';
import { UnrecognizedTriage } from './UnrecognizedTriage';
import { PersonModal } from './PersonModal';
import { ImageViewerModal } from './ImageViewerModal';
import { AddSourceModal } from './AddSourceModal';
import { WhatChangedModal } from './WhatChangedModal';
import { Users, Sparkles, HelpCircle, Undo2, CheckCircle, ShieldAlert, Plus, Check } from 'lucide-react';

interface ReviewPeopleScreenProps {
  people: PersonCluster[];
  photos: Record<string, PhotoInfo>;
  unrecognized: UnrecognizedData;
  suggestions: SuggestionsData;
  selectedIds: Set<string>;
  onToggleSelect: (personId: string) => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onMergeSelected: () => void;
  onAcceptSuggestion: (personAId: string, personBId: string) => void;
  onRejectSuggestion: (personAId: string, personBId: string) => void;
  rejectedPairs: Set<string>;
  onAssignFace: (faceId: string, targetPersonId?: string | null) => void;
  onAssignMultipleFaces?: (faceIds: string[], targetPersonId?: string | null) => Promise<void>;
  onAssignPhotos?: (photoIds: string[], targetPersonId?: string | null) => Promise<void>;
  onRenamePerson: (personId: string, newLabel: string) => void;
  onHidePerson: (personId: string) => void;
  onRemoveFace: (personId: string, faceId: string) => void;
  onRemovePhoto: (personId: string, photoId: string) => void;
  onUndo?: () => void;
  appliedEditsCount?: number;
  isMerging?: boolean;
  activeSubTab?: 'people' | 'suggestions' | 'unrecognized';
  onSubTabChange?: (tab: 'people' | 'suggestions' | 'unrecognized') => void;
  theme?: string;
  selectedSourceId?: string;
  onSourceFilterChange?: (sourceId: string) => void;
  onRefreshData?: () => void;
}

export const ReviewPeopleScreen: React.FC<ReviewPeopleScreenProps> = ({
  people,
  photos,
  unrecognized,
  suggestions,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onClearSelection,
  onMergeSelected,
  onAcceptSuggestion,
  onRejectSuggestion,
  rejectedPairs,
  onAssignFace,
  onAssignMultipleFaces,
  onAssignPhotos,
  onRenamePerson,
  onHidePerson,
  onRemoveFace,
  onRemovePhoto,
  onUndo,
  appliedEditsCount = 0,
  isMerging = false,
  activeSubTab: controlledSubTab,
  onSubTabChange,
  theme = 't-dark',
  selectedSourceId: controlledSourceId,
  onSourceFilterChange,
  onRefreshData,
}) => {
  const [internalSubTab, setInternalSubTab] = useState<'people' | 'suggestions' | 'unrecognized'>('people');
  const activeSubTab = controlledSubTab !== undefined ? controlledSubTab : internalSubTab;
  const setActiveSubTab = (tab: 'people' | 'suggestions' | 'unrecognized') => {
    setInternalSubTab(tab);
    onSubTabChange?.(tab);
  };
  const [inspectingPerson, setInspectingPerson] = useState<PersonCluster | null>(null);
  const [viewingPhotoId, setViewingPhotoId] = useState<string | null>(null);
  const [viewingContextPhotoIds, setViewingContextPhotoIds] = useState<string[] | undefined>(undefined);

  // Incremental Source Ingestion & What Changed states
  const [isAddSourceOpen, setIsAddSourceOpen] = useState<boolean>(false);
  const [isWhatChangedOpen, setIsWhatChangedOpen] = useState<boolean>(false);
  const [whatChangedReport, setWhatChangedReport] = useState<WhatChangedResponse | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getWhatChanged()
      .then((diff) => {
        if (diff && (diff.new_photos_count > 0 || (diff.new_photo_ids && diff.new_photo_ids.length > 0) || diff.generated_at)) {
          setWhatChangedReport(diff);
        }
      })
      .catch(() => {});
  }, []);

  const handleSourceAdded = (diff: WhatChangedResponse) => {
    setWhatChangedReport(diff);
    setIsWhatChangedOpen(true);
    onRefreshData?.();
    setToastMessage(`Added ${diff.new_photos_count} new photos successfully.`);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleUndoAddition = async () => {
    await api.undoLastSnapshot();
    setWhatChangedReport(null);
    setIsWhatChangedOpen(false);
    onRefreshData?.();
    setToastMessage('Project successfully rolled back to pre-addition state.');
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Derive available sources across all photos
  const availableSources = useMemo(() => {
    const map = new Map<string, { id: string; label: string; photoCount: number }>();
    for (const p of Object.values(photos)) {
      if (p.source_id || p.source_label) {
        const sId = p.source_id || p.source_label || 'unknown';
        const sLabel = p.source_label || p.source_id || 'Source';
        const existing = map.get(sId);
        if (existing) {
          existing.photoCount += 1;
        } else {
          map.set(sId, { id: sId, label: sLabel, photoCount: 1 });
        }
      }
    }
    return Array.from(map.values());
  }, [photos]);

  const [internalSourceFilter, setInternalSourceFilter] = useState<string>('all');
  const activeSourceFilter = controlledSourceId !== undefined ? controlledSourceId : internalSourceFilter;
  const handleSourceFilterChange = (val: string) => {
    setInternalSourceFilter(val);
    onSourceFilterChange?.(val);
  };

  const filteredPeopleBySource = useMemo(() => {
    if (activeSourceFilter === 'all') return people;
    return people.filter((p) => {
      const pPhotoIds = p.photo_ids || p.photos || [];
      return pPhotoIds.some((pid) => {
        const photo = photos[pid];
        return (
          photo &&
          (photo.source_id === activeSourceFilter || photo.source_label === activeSourceFilter)
        );
      });
    });
  }, [people, photos, activeSourceFilter]);

  // Map for quick person lookup
  const peopleMap = useMemo(() => {
    const map: Record<string, PersonCluster> = {};
    for (const p of people) {
      map[p.id] = p;
    }
    return map;
  }, [people]);

  // Keep inspected person up to date if people array changes
  const currentInspectingPerson = useMemo(() => {
    if (!inspectingPerson) return null;
    return peopleMap[inspectingPerson.id] || null;
  }, [inspectingPerson, peopleMap]);

  // Ambiguous faces map for triage
  const ambiguousMap = useMemo(() => {
    const map: Record<string, any> = {};
    if (suggestions.ambiguous_faces) {
      for (const item of suggestions.ambiguous_faces) {
        map[item.face_id] = item;
      }
    }
    return map;
  }, [suggestions]);

  // Active suggestions count (excluding session rejected pairs)
  const activeSuggestionsCount = useMemo(() => {
    if (!suggestions.possibly_the_same) return 0;
    return suggestions.possibly_the_same.filter((s) => {
      const key = [s.person_a_id, s.person_b_id].sort().join(':::');
      return !rejectedPairs.has(key);
    }).length;
  }, [suggestions, rejectedPairs]);

  // Open viewer with optional context photo list (e.g. from person modal or triage)
  const handleOpenPhotoViewer = (photoId: string, contextIds?: string[]) => {
    setViewingPhotoId(photoId);
    setViewingContextPhotoIds(contextIds);
  };

  return (
    <div className="space-y-6 pb-24 animate-fadeIn">
      {/* Top Header Bar & Sub-tab Navigation */}
      <div
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4"
        style={{ borderBottom: '1.5px solid var(--line)' }}
      >
        {/* Navigation Tabs */}
        <div id="review-subtabs-nav" className="flex items-center gap-3 flex-wrap">
          <button
            id="tab-people-grid"
            onClick={() => setActiveSubTab('people')}
            className={`riso-subtab-btn ${activeSubTab === 'people' ? 'active' : ''}`}
          >
            <Users className="w-5 h-5" style={{ color: activeSubTab === 'people' ? 'var(--accent)' : 'inherit' }} />
            <span>People Clusters</span>
            <span id="subtab-people-count" className="riso-tab-badge">
              {people.length}
            </span>
          </button>

          <button
            id="tab-suggestions"
            onClick={() => setActiveSubTab('suggestions')}
            className={`riso-subtab-btn ${activeSubTab === 'suggestions' ? 'active' : ''}`}
          >
            <Sparkles className="w-5 h-5" style={{ color: activeSubTab === 'suggestions' ? 'var(--accent)' : 'inherit' }} />
            <span>Suggestions</span>
            <span id="subtab-suggestions-count" className="riso-tab-badge">
              {activeSuggestionsCount}
            </span>
          </button>

          <button
            id="tab-unrecognized"
            onClick={() => setActiveSubTab('unrecognized')}
            className={`riso-subtab-btn ${activeSubTab === 'unrecognized' ? 'active' : ''}`}
          >
            <HelpCircle className="w-5 h-5" style={{ color: activeSubTab === 'unrecognized' ? 'var(--accent)' : 'inherit' }} />
            <span>Unrecognized</span>
            <span id="subtab-unrecognized-count" className="riso-tab-badge">
              {unrecognized.faces.length}
            </span>
          </button>
        </div>

        {/* Quick Undo, Source Filter & Review Stats */}
        <div className="flex items-center gap-3 flex-wrap">
          {availableSources.length > 1 && (
            <div className="flex items-center gap-2" id="source-filter-container">
              <span className="text-xs font-mono font-bold uppercase text-[var(--muted)]">Source:</span>
              <select
                id="source-filter-select"
                data-testid="source-filter-select"
                aria-label="Filter people by source"
                value={activeSourceFilter}
                onChange={(e) => handleSourceFilterChange(e.target.value)}
                className="riso-input text-xs font-mono font-bold px-2.5 py-1 rounded cursor-pointer"
                style={{
                  height: '34px',
                  background: 'var(--card-bg)',
                  border: '1.5px solid var(--line)',
                  color: 'var(--text)',
                }}
              >
                <option value="all">All Sources ({Object.keys(photos).length})</option>
                {availableSources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label} ({s.photoCount})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Add Source Button */}
          <button
            id="btn-add-source"
            data-testid="btn-add-source"
            type="button"
            onClick={() => setIsAddSourceOpen(true)}
            className="riso-btn-sec"
            title="Add an additional folder, ZIP, or Google Drive source to this project"
          >
            <Plus className="w-4 h-4 text-[var(--accent)]" />
            <span>+ Add Source</span>
          </button>

          {/* What Changed Button */}
          {whatChangedReport && (
            <button
              id="btn-view-what-changed"
              data-testid="btn-view-what-changed"
              type="button"
              onClick={() => setIsWhatChangedOpen(true)}
              className="riso-btn-sec"
              title="View What Changed in the latest addition"
            >
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>What Changed</span>
              <span className="riso-tab-badge ml-1 text-emerald-400">
                +{whatChangedReport.new_photos_count}
              </span>
            </button>
          )}

          {appliedEditsCount > 0 && onUndo && (
            <button
              onClick={onUndo}
              className="riso-btn-sec"
              title="Undo last edit operation"
            >
              <Undo2 className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <span>Undo Last Edit</span>
              <span className="riso-tab-badge ml-1">
                {appliedEditsCount}
              </span>
            </button>
          )}

          <div
            className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded"
            style={{
              background: 'var(--card-bg)',
              border: '1.5px solid var(--line)',
              fontSize: '14px',
              fontFamily: "'JetBrains Mono', monospace",
              color: 'var(--muted)',
            }}
          >
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ background: 'var(--accent)' }}
            />
            <span>{Object.keys(photos).length} Photos Indexed</span>
          </div>
        </div>
      </div>

      {/* Incremental Notification Toast Banner */}
      {toastMessage && (
        <div
          id="review-toast-banner"
          data-testid="review-toast-banner"
          className="p-3 rounded-lg flex items-center justify-between text-xs font-mono animate-fadeIn"
          style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1.5px solid #10b981',
            color: '#34d399',
          }}
        >
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            <span>{toastMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setToastMessage(null)}
            className="opacity-70 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Sub-tab Contents */}
      {activeSubTab === 'people' && (
        <PeopleGrid
          people={filteredPeopleBySource}
          photos={photos}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
          onSelectAll={onSelectAll}
          onClearSelection={onClearSelection}
          onMergeSelected={onMergeSelected}
          onSelectPerson={(p) => setInspectingPerson(p)}
          isMerging={isMerging}
          theme={theme}
          selectedSourceId={activeSourceFilter}
          availableSources={availableSources}
        />
      )}

      {activeSubTab === 'suggestions' && (
        <SuggestionReview
          suggestions={suggestions.possibly_the_same || []}
          peopleMap={peopleMap}
          onAccept={onAcceptSuggestion}
          onReject={onRejectSuggestion}
          rejectedPairs={rejectedPairs}
          theme={theme}
        />
      )}

      {activeSubTab === 'unrecognized' && (
        <UnrecognizedTriage
          unrecognized={unrecognized}
          ambiguousMap={ambiguousMap}
          people={people}
          photos={photos}
          onAssignFace={onAssignFace}
          onAssignMultipleFaces={onAssignMultipleFaces}
          onAssignPhotos={onAssignPhotos}
          onOpenPhotoViewer={(pid) => handleOpenPhotoViewer(pid)}
          theme={theme}
        />
      )}

      {/* Person Detail / Edit Modal */}
      {currentInspectingPerson && (
        <PersonModal
          person={currentInspectingPerson}
          photos={photos}
          onClose={() => setInspectingPerson(null)}
          onRename={onRenamePerson}
          onHide={onHidePerson}
          onRemoveFace={onRemoveFace}
          onRemovePhoto={onRemovePhoto}
          onOpenPhotoViewer={(pid) =>
            handleOpenPhotoViewer(pid, currentInspectingPerson.photo_ids || currentInspectingPerson.photos)
          }
        />
      )}

      {/* Revamped High-End Image Viewer Modal */}
      {viewingPhotoId && photos[viewingPhotoId] && (
        <ImageViewerModal
          photoId={viewingPhotoId}
          photos={photos}
          photoIds={viewingContextPhotoIds}
          people={people}
          unrecognized={unrecognized}
          onClose={() => {
            setViewingPhotoId(null);
            setViewingContextPhotoIds(undefined);
          }}
          onNavigatePhoto={(pid) => setViewingPhotoId(pid)}
          onAssignFace={onAssignFace}
          onRemoveFace={onRemoveFace}
          onInspectPerson={(p) => {
            setViewingPhotoId(null);
            setInspectingPerson(p);
          }}
        />
      )}

      {/* Incremental Add Source Modal */}
      {isAddSourceOpen && (
        <AddSourceModal
          theme={theme}
          onClose={() => setIsAddSourceOpen(false)}
          onSourceAdded={handleSourceAdded}
        />
      )}

      {/* Incremental What Changed Diff & Rollback Modal */}
      {isWhatChangedOpen && whatChangedReport && (
        <WhatChangedModal
          theme={theme}
          diff={whatChangedReport}
          onClose={() => setIsWhatChangedOpen(false)}
          onUndoAddition={handleUndoAddition}
          onViewPerson={(pid) => {
            const found = peopleMap[pid];
            if (found) {
              setInspectingPerson(found);
            }
          }}
        />
      )}
    </div>
  );
};
