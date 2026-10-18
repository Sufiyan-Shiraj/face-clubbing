import React, { useState, useMemo } from 'react';
import {
  PersonCluster,
  PhotoInfo,
  UnrecognizedData,
  SuggestionsData,
} from '../types';
import { PeopleGrid } from './PeopleGrid';
import { SuggestionReview } from './SuggestionReview';
import { UnrecognizedTriage } from './UnrecognizedTriage';
import { PersonModal } from './PersonModal';
import { ImageViewerModal } from './ImageViewerModal';
import { Users, Sparkles, HelpCircle, Undo2, CheckCircle, ShieldAlert } from 'lucide-react';

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
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'people' | 'suggestions' | 'unrecognized'>('people');
  const [inspectingPerson, setInspectingPerson] = useState<PersonCluster | null>(null);
  const [viewingPhotoId, setViewingPhotoId] = useState<string | null>(null);
  const [viewingContextPhotoIds, setViewingContextPhotoIds] = useState<string[] | undefined>(undefined);

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
        <div className="flex items-center gap-3 flex-wrap">
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

        {/* Quick Undo & Review Stats */}
        <div className="flex items-center gap-3">
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

      {/* Sub-tab Contents */}
      {activeSubTab === 'people' && (
        <PeopleGrid
          people={people}
          photos={photos}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
          onSelectAll={onSelectAll}
          onClearSelection={onClearSelection}
          onMergeSelected={onMergeSelected}
          onSelectPerson={(p) => setInspectingPerson(p)}
          isMerging={isMerging}
        />
      )}

      {activeSubTab === 'suggestions' && (
        <SuggestionReview
          suggestions={suggestions.possibly_the_same || []}
          peopleMap={peopleMap}
          onAccept={onAcceptSuggestion}
          onReject={onRejectSuggestion}
          rejectedPairs={rejectedPairs}
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
    </div>
  );
};
