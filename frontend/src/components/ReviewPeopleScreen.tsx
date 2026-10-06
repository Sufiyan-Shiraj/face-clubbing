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
import { PhotoModal } from '@viewer/components/PhotoModal';
import { Users, Sparkles, HelpCircle } from 'lucide-react';

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
  onRenamePerson: (personId: string, newLabel: string) => void;
  onHidePerson: (personId: string) => void;
  onRemoveFace: (personId: string, faceId: string) => void;
  onRemovePhoto: (personId: string, photoId: string) => void;
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
  onRenamePerson,
  onHidePerson,
  onRemoveFace,
  onRemovePhoto,
  isMerging = false,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'people' | 'suggestions' | 'unrecognized'>('people');
  const [inspectingPerson, setInspectingPerson] = useState<PersonCluster | null>(null);
  const [viewingPhotoId, setViewingPhotoId] = useState<string | null>(null);

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

  // Photo viewer navigation
  const allPhotoIds = useMemo(() => Object.keys(photos), [photos]);
  const activePhotoIndex = viewingPhotoId ? allPhotoIds.indexOf(viewingPhotoId) : -1;
  const activePhoto = viewingPhotoId ? photos[viewingPhotoId] : null;

  return (
    <div className="space-y-6 pb-20 animate-fadeIn">
      {/* Sub-tab Navigation */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            id="tab-people-grid"
            onClick={() => setActiveSubTab('people')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeSubTab === 'people'
                ? 'bg-neutral-800 text-white shadow-sm border border-neutral-700'
                : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>People</span>
            <span
              id="subtab-people-count"
              className="px-2 py-0.5 rounded-md bg-neutral-900 border border-neutral-700/80 text-xs font-mono text-neutral-300"
            >
              {people.length}
            </span>
          </button>

          <button
            id="tab-suggestions"
            onClick={() => setActiveSubTab('suggestions')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeSubTab === 'suggestions'
                ? 'bg-neutral-800 text-white shadow-sm border border-neutral-700'
                : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Suggestions</span>
            {activeSuggestionsCount > 0 && (
              <span
                id="subtab-suggestions-count"
                className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono font-bold"
              >
                {activeSuggestionsCount}
              </span>
            )}
          </button>

          <button
            id="tab-unrecognized"
            onClick={() => setActiveSubTab('unrecognized')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeSubTab === 'unrecognized'
                ? 'bg-neutral-800 text-white shadow-sm border border-neutral-700'
                : 'text-neutral-400 hover:text-white hover:bg-neutral-900/60'
            }`}
          >
            <HelpCircle className="w-4 h-4 text-blue-400" />
            <span>Unrecognized</span>
            <span
              id="subtab-unrecognized-count"
              className="px-2 py-0.5 rounded-md bg-neutral-900 border border-neutral-700/80 text-xs font-mono text-neutral-300"
            >
              {unrecognized.faces.length}
            </span>
          </button>
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
          onOpenPhotoViewer={(pid) => setViewingPhotoId(pid)}
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
          onOpenPhotoViewer={(pid) => setViewingPhotoId(pid)}
        />
      )}

      {/* Photo Viewer Modal */}
      {viewingPhotoId && activePhoto && (
        <PhotoModal
          photo={{
            name: activePhoto.file_name,
            thumb: activePhoto.thumb || `thumbs/${activePhoto.photo_id}.jpg`,
            width: activePhoto.width,
            height: activePhoto.height,
          }}
          photoId={viewingPhotoId}
          hasPrev={activePhotoIndex > 0}
          hasNext={activePhotoIndex >= 0 && activePhotoIndex < allPhotoIds.length - 1}
          onPrev={() => {
            if (activePhotoIndex > 0) setViewingPhotoId(allPhotoIds[activePhotoIndex - 1]);
          }}
          onNext={() => {
            if (activePhotoIndex >= 0 && activePhotoIndex < allPhotoIds.length - 1) {
              setViewingPhotoId(allPhotoIds[activePhotoIndex + 1]);
            }
          }}
          onClose={() => setViewingPhotoId(null)}
        />
      )}
    </div>
  );
};
