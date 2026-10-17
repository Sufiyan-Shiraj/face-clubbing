import React, { useState, useMemo } from 'react';
import { UnrecognizedData, AmbiguousFaceSuggestion, PersonCluster, PhotoInfo } from '../types';
import {
  UserPlus,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  Image as ImageIcon,
  Check,
  Filter,
  CheckSquare,
  Users,
  Search,
  CheckCircle2,
  ExternalLink,
  ChevronDown,
  Layers,
  ArrowLeftRight,
} from 'lucide-react';
import { FaceCompareModal } from './FaceCompareModal';
import { MascotSticker } from './MascotSticker';

interface UnrecognizedTriageProps {
  unrecognized: UnrecognizedData;
  ambiguousMap: Record<string, AmbiguousFaceSuggestion>;
  people: PersonCluster[];
  photos: Record<string, PhotoInfo>;
  onAssignFace: (faceId: string, targetPersonId?: string | null) => void;
  onAssignMultipleFaces?: (faceIds: string[], targetPersonId?: string | null) => Promise<void>;
  onAssignPhotos?: (photoIds: string[], targetPersonId?: string | null) => Promise<void>;
  onOpenPhotoViewer: (photoId: string) => void;
  theme?: string;
}

export const UnrecognizedTriage: React.FC<UnrecognizedTriageProps> = ({
  unrecognized,
  ambiguousMap,
  people,
  photos,
  onAssignFace,
  onAssignMultipleFaces,
  onAssignPhotos,
  onOpenPhotoViewer,
  theme = 't-dark',
}) => {
  const [reasonFilter, setReasonFilter] = useState<string>('all');
  const [faceSearch, setFaceSearch] = useState<string>('');

  // Selected person per individual card
  const [selectedPersonForAssign, setSelectedPersonForAssign] = useState<Record<string, string>>({});

  // Global batch selection states
  const [batchTargetPersonId, setBatchTargetPersonId] = useState<string>('');
  const [selectedFaceIds, setSelectedFaceIds] = useState<Set<string>>(new Set());
  const [selectedPhotoIds, setSelectedPhotoIds] = useState<Set<string>>(new Set());
  const [isBatchAssigning, setIsBatchAssigning] = useState<boolean>(false);
  const [batchSuccessMsg, setBatchSuccessMsg] = useState<string | null>(null);

  // Active comparison modal state
  const [compareModalData, setCompareModalData] = useState<{
    unrecognizedFace: {
      faceId: string;
      faceUrl: string;
      photoId: string;
      fileName?: string;
      rejectionReason?: string | null;
    };
    targetPerson: PersonCluster;
  } | null>(null);

  // Filtered unrecognized faces
  const filteredFaces = useMemo(() => {
    return unrecognized.faces.filter((f, idx) => {
      const faceId = f.face_id || `face_${idx}`;
      const pInfo = photos[f.photo_id];
      const fileName = pInfo?.file_name || f.file_name || '';

      // Reason filter
      if (reasonFilter !== 'all' && f.rejection_reason !== reasonFilter) {
        return false;
      }

      // Search filter
      if (faceSearch.trim()) {
        const q = faceSearch.toLowerCase();
        return faceId.toLowerCase().includes(q) || fileName.toLowerCase().includes(q);
      }

      return true;
    });
  }, [unrecognized.faces, reasonFilter, faceSearch, photos]);

  // Target Person lookup
  const batchTargetPerson = useMemo(() => {
    if (!batchTargetPersonId) return null;
    return people.find((p) => p.id === batchTargetPersonId) || null;
  }, [batchTargetPersonId, people]);

  // Multi-select face toggles
  const handleToggleFace = (faceId: string) => {
    setSelectedFaceIds((prev) => {
      const next = new Set(prev);
      if (next.has(faceId)) {
        next.delete(faceId);
      } else {
        next.add(faceId);
      }
      return next;
    });
  };

  const handleSelectAllFiltered = () => {
    const allFiltered = new Set(
      filteredFaces.map((f, idx) => f.face_id || `face_${idx}`)
    );
    setSelectedFaceIds(allFiltered);
  };

  const handleClearFaceSelection = () => {
    setSelectedFaceIds(new Set());
    setSelectedPhotoIds(new Set());
  };

  const handleInvertFaceSelection = () => {
    setSelectedFaceIds((prev) => {
      const next = new Set<string>();
      filteredFaces.forEach((f, idx) => {
        const id = f.face_id || `face_${idx}`;
        if (!prev.has(id)) next.add(id);
      });
      return next;
    });
  };

  // Toggle no-face photo selection
  const handleTogglePhoto = (photoId: string) => {
    setSelectedPhotoIds((prev) => {
      const next = new Set(prev);
      if (next.has(photoId)) next.delete(photoId);
      else next.add(photoId);
      return next;
    });
  };

  // One-click Batch Assignment Handler
  const handleExecuteBatchAssign = async () => {
    const totalFaces = selectedFaceIds.size;
    const totalPhotos = selectedPhotoIds.size;
    if (totalFaces === 0 && totalPhotos === 0) return;

    setIsBatchAssigning(true);
    setBatchSuccessMsg(null);

    try {
      const targetId = batchTargetPersonId || null;
      const faceIdsArray = Array.from(selectedFaceIds);
      const photoIdsArray = Array.from(selectedPhotoIds);

      // Assign faces
      if (faceIdsArray.length > 0) {
        if (onAssignMultipleFaces) {
          await onAssignMultipleFaces(faceIdsArray, targetId);
        } else {
          // Fallback sequential
          for (const fid of faceIdsArray) {
            await onAssignFace(fid, targetId);
          }
        }
      }

      // Assign photos
      if (photoIdsArray.length > 0) {
        if (onAssignPhotos) {
          await onAssignPhotos(photoIdsArray, targetId);
        }
      }

      const targetLabel = batchTargetPerson?.label || batchTargetPerson?.id || 'New Person';
      setBatchSuccessMsg(
        `Successfully added ${totalFaces} ${totalFaces === 1 ? 'face' : 'faces'}${
          totalPhotos > 0 ? ` and ${totalPhotos} photos` : ''
        } to ${targetLabel}!`
      );
      setSelectedFaceIds(new Set());
      setSelectedPhotoIds(new Set());

      setTimeout(() => {
        setBatchSuccessMsg(null);
      }, 5000);
    } catch (err: any) {
      alert(`Batch assignment failed: ${err.message || err}`);
    } finally {
      setIsBatchAssigning(false);
    }
  };

  const totalSelectedCount = selectedFaceIds.size + selectedPhotoIds.size;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Compare Modal */}
      {compareModalData && (
        <FaceCompareModal
          unrecognizedFace={compareModalData.unrecognizedFace}
          targetPerson={compareModalData.targetPerson}
          photos={photos}
          onClose={() => setCompareModalData(null)}
          onConfirm={(fid, pid) => {
            onAssignFace(fid, pid);
            setCompareModalData(null);
          }}
          onOpenPhotoViewer={onOpenPhotoViewer}
        />
      )}

      {/* Triage Overview & Filter Header */}
      <div
        id="unrecognized-triage-container"
        className="p-6 rounded"
        style={{
          background: 'var(--card-bg, var(--panel))',
          border: '1.5px solid var(--line)',
          boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h3
              className="text-xl font-bold flex items-center gap-3"
              style={{ color: 'var(--text)' }}
            >
              <div
                className="w-9 h-9 rounded flex items-center justify-center flex-shrink-0"
                style={{
                  background: 'var(--input)',
                  border: '1.5px solid var(--accent)',
                  color: 'var(--accent)',
                }}
              >
                <AlertTriangle className="w-5 h-5" />
              </div>
              <span>Unrecognized Faces & Photos Triage</span>
            </h3>
            <p className="text-sm mt-1.5 max-w-2xl leading-relaxed" style={{ color: 'var(--muted)' }}>
              Assign ambiguous and unattached faces into existing clusters or create new people. You can select a target person to visually verify them and batch-add all matching images with one click.
            </p>
          </div>

          {/* Reason Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5"
              style={{ color: 'var(--muted)' }}
            >
              <Filter className="w-4 h-4" /> Filter:
            </span>
            {['all', 'ambiguous', 'unattached_profile', 'unattached_small', 'unattached_lowscore'].map((r) => {
              const isActive = reasonFilter === r;
              return (
                <button
                  key={r}
                  onClick={() => setReasonFilter(r)}
                  className="px-3.5 py-1.5 rounded text-xs font-bold capitalize transition-all"
                  style={{
                    background: isActive ? 'var(--accent)' : 'var(--input)',
                    color: isActive ? 'var(--on-accent)' : 'var(--text)',
                    border: isActive ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
                    cursor: 'pointer',
                  }}
                >
                  {r.replace('unattached_', '')}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* BATCH ASSIGNMENT COMMAND CENTER (User Request Feature) */}
      <div
        className="p-6 sm:p-7 rounded"
        style={{
          background: 'var(--card-bg, var(--panel))',
          border: totalSelectedCount > 0 ? '2px solid var(--accent)' : '2px solid var(--line)',
          boxShadow: '2px 4px 0px rgba(0, 0, 0, 0.25)',
          position: 'relative',
          transition: 'border-color 0.2s ease',
        }}
      >
        <div className="flex items-center justify-between mb-5 flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div
              className="w-11 h-11 rounded flex items-center justify-center flex-shrink-0"
              style={{
                background: 'var(--input)',
                border: '1.5px solid var(--accent)',
                color: 'var(--accent)',
              }}
            >
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-lg font-bold flex items-center gap-2.5" style={{ color: 'var(--text)' }}>
                <span>Batch Assign to Person</span>
                <span className="riso-badge-accent">
                  1-Click Merge
                </span>
              </h4>
              <p className="text-sm mt-0.5" style={{ color: 'var(--muted)' }}>
                Select target person and faces below to batch merge.
              </p>
            </div>
          </div>

          {/* Selection Stats */}
          <div className="flex items-center gap-2.5">
            <span
              id="batch-selected-count"
              className="px-4 py-2 rounded text-sm font-mono font-bold transition-all"
              style={{
                background: totalSelectedCount > 0 ? 'var(--accent)' : 'var(--input)',
                color: totalSelectedCount > 0 ? 'var(--on-accent)' : 'var(--muted)',
                border: totalSelectedCount > 0 ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
              }}
            >
              {totalSelectedCount} items selected
            </span>

            {totalSelectedCount > 0 && (
              <button
                onClick={handleClearFaceSelection}
                className="riso-btn-sec"
                style={{ height: '38px', padding: '0 14px', fontSize: '13px' }}
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Step 1: Target Person Selection & Live Verification Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
          {/* Target Person Picker */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-2">
            <label
              className="text-sm font-bold uppercase tracking-wider flex items-center gap-2"
              style={{ color: 'var(--muted)' }}
            >
              <Users className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              1. Select Target Person:
            </label>
            <div className="relative">
              <select
                id="batch-target-person-select"
                value={batchTargetPersonId}
                onChange={(e) => setBatchTargetPersonId(e.target.value)}
                className="riso-select w-full"
                style={{ height: '52px', fontSize: '15px' }}
              >
                <option value="">-- Choose person to merge into (or create new) --</option>
                {people.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label ? `${p.label} (${p.id})` : p.id} — {p.photo_count || p.photos?.length || 0} photos
                  </option>
                ))}
              </select>
              <ChevronDown
                className="w-5 h-5 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none"
                style={{ color: 'var(--muted)' }}
              />
            </div>
          </div>

          {/* Live Person Visual Preview Card (Answers: "when i select a person i want to see that person so i know if its correct to merge") */}
          <div className="lg:col-span-7">
            {batchTargetPerson ? (
              <div
                id="batch-target-person-preview"
                className="p-4 rounded flex items-center justify-between gap-4 animate-fadeIn"
                style={{
                  background: 'var(--input)',
                  border: '1.5px solid var(--accent)',
                  boxShadow: '2px 2px 0px rgba(0, 0, 0, 0.2)',
                  minHeight: '100px',
                }}
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div
                    className="w-18 h-18 sm:w-20 sm:h-20 rounded overflow-hidden flex-shrink-0"
                    style={{
                      border: '2.5px solid var(--accent)',
                      background: 'var(--bg)',
                      boxShadow: '2px 2px 0px rgba(0, 0, 0, 0.25)',
                    }}
                  >
                    <img
                      src={batchTargetPerson.face}
                      alt={batchTargetPerson.label || batchTargetPerson.id}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2371717a"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                      }}
                    />
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="text-base sm:text-lg font-bold font-mono truncate" style={{ color: 'var(--text)' }}>
                        {batchTargetPerson.label || batchTargetPerson.id}
                      </span>
                      <span className="riso-tab-badge">
                        {batchTargetPerson.photo_count || batchTargetPerson.photos?.length || 0} photos
                      </span>
                    </div>
                    <div className="text-xs font-mono mt-1 truncate" style={{ color: 'var(--muted)' }}>
                      ID: {batchTargetPerson.id}
                    </div>

                    {/* Sample face thumbnails for visual confirmation */}
                    {batchTargetPerson.faces && batchTargetPerson.faces.length > 1 && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Other angles:</span>
                        {batchTargetPerson.faces.slice(0, 4).map((f) => (
                          <img
                            key={f.face_id}
                            src={`/faces/${f.face_id}.jpg`}
                            alt=""
                            className="w-8 h-8 rounded object-cover"
                            style={{ border: '1px solid var(--line)' }}
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = batchTargetPerson.face;
                            }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => setBatchTargetPersonId('')}
                  className="riso-btn-sec"
                  style={{ height: '38px', padding: '0 14px', fontSize: '13px' }}
                >
                  Change
                </button>
              </div>
            ) : (
              <div
                className="p-4 rounded flex items-center justify-center text-center text-sm"
                style={{
                  background: 'var(--input)',
                  border: '1.5px solid var(--line)',
                  color: 'var(--muted)',
                  minHeight: '100px',
                }}
              >
                <span>No person selected yet. Pick a target person on the left to see their photo preview here.</span>
              </div>
            )}
          </div>
        </div>

        {/* Action Controls & One-Click Button */}
        <div
          className="mt-6 pt-5 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4"
          style={{ borderTop: '1.5px solid var(--line)' }}
        >
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={handleSelectAllFiltered}
              className="riso-btn-sec"
              style={{ height: '44px', fontSize: '14px', fontWeight: 700 }}
            >
              <CheckSquare className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              <span>Select All Filtered ({filteredFaces.length})</span>
            </button>
            <button
              onClick={handleInvertFaceSelection}
              className="riso-btn-sec"
              style={{ height: '44px', fontSize: '14px', fontWeight: 700 }}
            >
              Invert Selection
            </button>
          </div>

          {/* ONE BUTTON TO ADD THEM ALL (User Request Feature) */}
          <button
            id="batch-execute-assign-btn"
            data-testid="batch-assign-btn"
            onClick={handleExecuteBatchAssign}
            disabled={totalSelectedCount === 0 || isBatchAssigning}
            className="btn pri"
            style={{
              height: '50px',
              padding: '0 32px',
              fontSize: '15px',
              fontWeight: 800,
              borderRadius: '4px',
              boxShadow: totalSelectedCount > 0 ? '2px 3px 0px rgba(0,0,0,0.25)' : 'none',
              opacity: totalSelectedCount === 0 || isBatchAssigning ? 0.45 : 1,
              cursor: totalSelectedCount === 0 || isBatchAssigning ? 'not-allowed' : 'pointer',
            }}
          >
            {isBatchAssigning ? (
              <>
                <div
                  className="w-4 h-4 rounded-full animate-spin mr-2"
                  style={{
                    border: '2px solid rgba(0,0,0,0.3)',
                    borderTopColor: 'var(--on-accent)',
                  }}
                />
                <span>Assigning {totalSelectedCount} items...</span>
              </>
            ) : batchTargetPerson ? (
              <>
                <Check className="w-5 h-5 mr-1" />
                <span>
                  Add {totalSelectedCount} Selected to {batchTargetPerson.label || batchTargetPerson.id}
                </span>
              </>
            ) : (
              <>
                <UserPlus className="w-5 h-5 mr-1" />
                <span>Create New Person from {totalSelectedCount} Selected</span>
              </>
            )}
          </button>
        </div>

        {/* Success Toast */}
        {batchSuccessMsg && (
          <div
            className="mt-4 p-4 rounded text-sm font-bold flex items-center gap-2.5 animate-fadeIn"
            style={{
              background: 'var(--input)',
              border: '1.5px solid var(--accent)',
              color: 'var(--accent)',
            }}
          >
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span>{batchSuccessMsg}</span>
          </div>
        )}
      </div>

      {/* Faces Grid Section */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div className="flex items-center gap-2.5">
            <h4 className="text-lg font-bold uppercase tracking-wider" style={{ color: 'var(--text)' }}>
              Unrecognized Face Crops ({filteredFaces.length})
            </h4>
            <span className="text-sm font-mono" style={{ color: 'var(--muted)' }}>
              (Click card to toggle selection)
            </span>
          </div>

          {/* Quick Search */}
          <div className="relative w-full sm:w-72">
            <Search
              className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: 'var(--muted)' }}
            />
            <input
              type="text"
              value={faceSearch}
              onChange={(e) => setFaceSearch(e.target.value)}
              placeholder="Search faces or photos..."
              className="riso-input w-full pl-10"
              style={{ height: '42px', fontSize: '14px' }}
            />
          </div>
        </div>

        {filteredFaces.length === 0 ? (
          <div
            id="unrec-faces-empty-state"
            data-testid="unrec-faces-empty-state"
            className="p-12 sm:p-14 rounded-lg text-center space-y-4"
            style={{
              background: 'var(--card-bg, var(--panel))',
              border: '2px dashed var(--line)',
              color: 'var(--muted)',
              boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
            }}
          >
            <div className="w-20 h-20 mx-auto rounded-xl bg-[var(--input)] border-2 border-[var(--line)] flex items-center justify-center p-1.5 shadow-[2px_2px_0px_var(--line)]">
              <MascotSticker pose={8} theme={theme} className="w-full h-full object-contain" />
            </div>
            <h4 className="text-xl font-black font-mono uppercase" style={{ color: 'var(--text)' }}>
              {unrecognized.faces.length === 0 ? 'Zero Unrecognized Faces!' : 'No Faces Match Query'}
            </h4>
            <p className="text-sm max-w-md mx-auto leading-relaxed">
              {unrecognized.faces.length === 0
                ? 'Every detected face in this album is recognized and assigned to an attendee cluster!'
                : 'Try adjusting or clearing the rejection reason filter or search term above.'}
            </p>
          </div>
        ) : (
          <div
            id="unrec-faces-grid"
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3.5"
            data-testid="unrec-faces-grid"
          >
            {filteredFaces.map((f, idx) => {
            const faceId = f.face_id || `face_${idx}`;
            const ambSuggestion = ambiguousMap[faceId];
            const pInfo = photos[f.photo_id];
            const fileName = pInfo?.file_name || f.file_name || `${f.photo_id}.jpg`;
            const isSelected = selectedFaceIds.has(faceId);
            const cardSelectedPid = selectedPersonForAssign[faceId] || '';
            const cardSelectedPerson = cardSelectedPid
              ? people.find((p) => p.id === cardSelectedPid)
              : null;

            return (
              <div
                key={faceId}
                data-testid={`unrec-face-card-${faceId}`}
                onClick={(e) => {
                  // Don't toggle selection if clicking select, button, or link
                  if (
                    (e.target as HTMLElement).closest('select') ||
                    (e.target as HTMLElement).closest('button') ||
                    (e.target as HTMLElement).closest('a')
                  ) {
                    return;
                  }
                  handleToggleFace(faceId);
                }}
                className="p-3 rounded transition-all flex flex-col justify-between cursor-pointer"
                style={{
                  background: isSelected ? 'var(--panel)' : 'var(--card-bg, var(--panel))',
                  border: isSelected ? '2.5px solid var(--accent)' : '1.5px solid var(--line)',
                  boxShadow: isSelected ? '2px 4px 0px var(--accent)' : '2px 3px 0px rgba(0, 0, 0, 0.2)',
                }}
              >
                <div>
                  {/* Top Header: Selection Checkbox & Photo ID */}
                  <div className="flex items-center justify-between gap-1.5 mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleFace(faceId);
                        }}
                        className="w-5 h-5 rounded flex items-center justify-center transition-colors flex-shrink-0"
                        style={{
                          background: isSelected ? 'var(--accent)' : 'var(--input)',
                          color: isSelected ? 'var(--on-accent)' : 'transparent',
                          border: isSelected ? 'none' : '1.5px solid var(--line)',
                        }}
                        title="Toggle selection for batch assignment"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <span className="text-xs font-mono font-bold truncate max-w-[110px]" style={{ color: 'var(--text)' }} title={faceId}>
                        {faceId}
                      </span>
                    </div>

                    <span className="riso-tab-badge text-xs" style={{ color: 'var(--accent)' }}>
                      {f.rejection_reason || 'unattached'}
                    </span>
                  </div>

                  {/* Compact Face Image - Sized appropriately */}
                  <div
                    className="w-full aspect-square max-h-40 sm:max-h-44 rounded overflow-hidden relative group cursor-pointer my-1.5 flex items-center justify-center"
                    style={{
                      background: 'var(--input)',
                      border: '1.5px solid var(--line)',
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenPhotoViewer(f.photo_id);
                    }}
                    title="Click to view full photo"
                  >
                    <img
                      src={f.face}
                      alt={faceId}
                      loading="lazy"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2352525b"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                      }}
                    />
                    <div
                      className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      style={{ background: 'rgba(0,0,0,0.45)', color: '#fff' }}
                    >
                      <div
                        className="flex items-center gap-1 px-2 py-1 rounded"
                        style={{ background: 'var(--panel)', border: '1px solid var(--line)', fontSize: '12px', fontWeight: 700 }}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>View</span>
                      </div>
                    </div>
                  </div>

                  {/* Metadata below face */}
                  <div className="mt-1 flex items-center justify-between gap-1.5 text-xs">
                    <span
                      className="text-xs font-mono hover:underline cursor-pointer truncate font-bold"
                      style={{ color: 'var(--text)' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenPhotoViewer(f.photo_id);
                      }}
                      title={`View photo: ${fileName}`}
                    >
                      {fileName}
                    </span>

                    {f.det_score !== undefined && f.det_score !== null && (
                      <span className="text-xs font-mono font-medium flex-shrink-0" style={{ color: 'var(--muted)' }}>
                        {f.det_score.toFixed(2)}
                      </span>
                    )}
                  </div>

                  {/* Top Candidates for Ambiguous Faces */}
                  {ambSuggestion && ambSuggestion.top_candidates && ambSuggestion.top_candidates.length > 0 && (
                    <div
                      className="my-2 p-2 rounded"
                      style={{
                        background: 'var(--input)',
                        border: '1.5px solid var(--line)',
                      }}
                    >
                      <span
                        className="text-xs font-bold uppercase tracking-wider flex items-center gap-1 mb-1.5"
                        style={{ color: 'var(--muted)' }}
                      >
                        <Sparkles className="w-3 h-3" style={{ color: 'var(--accent)' }} />
                        Top Candidates:
                      </span>
                      <div className="space-y-1.5">
                        {ambSuggestion.top_candidates.slice(0, 2).map((cand, cIdx) => {
                          const candPerson = people.find((p) => p.id === cand.candidate_id);
                          const candName = candPerson?.label || cand.candidate_id;

                          return (
                            <div
                              key={cIdx}
                              className="flex items-center justify-between p-1.5 rounded"
                              style={{
                                background: 'var(--card-bg)',
                                border: '1px solid var(--line)',
                              }}
                            >
                              <div className="flex items-center gap-1.5 min-w-0 pr-1 flex-1">
                                {candPerson?.face && (
                                  <img
                                    src={candPerson.face}
                                    alt=""
                                    loading="lazy"
                                    className="w-6 h-6 rounded object-cover flex-shrink-0"
                                    style={{ border: '1px solid var(--line)' }}
                                  />
                                )}
                                <span className="font-mono text-xs font-bold truncate" style={{ color: 'var(--text)' }} title={candName}>
                                  {candName}
                                </span>
                              </div>

                              <div className="flex items-center gap-1 flex-shrink-0">
                                {candPerson && (
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setCompareModalData({
                                        unrecognizedFace: {
                                          faceId,
                                          faceUrl: f.face,
                                          photoId: f.photo_id,
                                          fileName,
                                          rejectionReason: f.rejection_reason,
                                        },
                                        targetPerson: candPerson,
                                      });
                                    }}
                                    className="riso-btn-sec"
                                    style={{ height: '26px', padding: '0 6px', fontSize: '12px' }}
                                    title="Compare side-by-side"
                                  >
                                    Verify
                                  </button>
                                )}
                                <button
                                  type="button"
                                  data-testid="quick-assign-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onAssignFace(faceId, cand.candidate_id);
                                  }}
                                  className="btn pri"
                                  style={{ height: '26px', padding: '0 8px', fontSize: '12px', fontWeight: 700, borderRadius: '4px' }}
                                  title={`Assign to ${candName}`}
                                >
                                  Assign
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* VISUAL PERSON PREVIEW ON SELECTION */}
                  {cardSelectedPerson && (
                    <div
                      id={`selected-person-preview-${faceId}`}
                      className="my-2 p-2 rounded"
                      style={{
                        background: 'var(--input)',
                        border: '1.5px solid var(--accent)',
                        boxShadow: '2px 2px 0px rgba(0,0,0,0.2)',
                      }}
                    >
                      <div className="flex items-center justify-between text-xs font-bold mb-1.5" style={{ color: 'var(--accent)' }}>
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Match:
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setCompareModalData({
                              unrecognizedFace: {
                                faceId,
                                faceUrl: f.face,
                                photoId: f.photo_id,
                                fileName,
                                rejectionReason: f.rejection_reason,
                              },
                              targetPerson: cardSelectedPerson,
                            });
                          }}
                          className="riso-btn-sec"
                          style={{ height: '24px', padding: '0 6px', fontSize: '12px' }}
                          title="Open Side-by-side Comparison"
                        >
                          <ArrowLeftRight className="w-3 h-3" /> Compare
                        </button>
                      </div>

                      {/* Side-by-Side Face & Target Person Avatar - Compact */}
                      <div className="flex items-center justify-around py-1">
                        <div className="text-center">
                          <img
                            src={f.face}
                            alt="Unrecognized"
                            loading="lazy"
                            className="w-12 h-12 sm:w-14 sm:h-14 rounded object-cover mx-auto"
                            style={{ border: '1.5px solid var(--line)' }}
                          />
                          <span className="text-xs font-mono block mt-0.5" style={{ color: 'var(--muted)' }}>This Face</span>
                        </div>

                        <ArrowRight className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--accent)' }} />

                        <div className="text-center">
                          <img
                            src={cardSelectedPerson.face}
                            alt="Target"
                            loading="lazy"
                            className="w-12 h-12 sm:w-14 sm:h-14 rounded object-cover mx-auto shadow-md"
                            style={{ border: '2px solid var(--accent)' }}
                          />
                          <span className="text-xs font-bold font-mono block mt-0.5 truncate max-w-[80px]" style={{ color: 'var(--text)' }}>
                            {cardSelectedPerson.label || cardSelectedPerson.id}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Assignment Controls - Contained completely within card bounds */}
                <div
                  className="pt-2.5 mt-2 space-y-1.5"
                  style={{ borderTop: '1.5px solid var(--line)' }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="w-full">
                    <select
                      data-testid="assign-target-select"
                      value={cardSelectedPid}
                      onChange={(e) =>
                        setSelectedPersonForAssign({
                          ...selectedPersonForAssign,
                          [faceId]: e.target.value,
                        })
                      }
                      className="riso-select w-full block min-w-0"
                      style={{ height: '34px', fontSize: '12px' }}
                    >
                      <option value="">Assign to person...</option>
                      {people.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.label || p.id} ({p.photo_count || p.photos?.length || 0})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-1.5 w-full">
                    <button
                      type="button"
                      data-testid="assign-to-person-btn"
                      onClick={() => {
                        if (cardSelectedPid) onAssignFace(faceId, cardSelectedPid);
                      }}
                      disabled={!cardSelectedPid}
                      className="btn pri flex-1 min-w-0"
                      style={{
                        height: '34px',
                        padding: '0 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 700,
                        opacity: !cardSelectedPid ? 0.45 : 1,
                        cursor: !cardSelectedPid ? 'not-allowed' : 'pointer',
                      }}
                      title="Assign this face to selected person"
                    >
                      Assign
                    </button>

                    <button
                      type="button"
                      data-testid="create-person-btn"
                      onClick={() => onAssignFace(faceId, null)}
                      className="riso-btn-sec flex-1 min-w-0 truncate"
                      style={{ height: '34px', padding: '0 6px', fontSize: '12px', fontWeight: 700 }}
                      title="Create new person from this face"
                    >
                      + New
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      </div>

      {/* Photos With No Detected Face (Reachability guarantee) */}
      <div
        className="p-6 rounded"
        style={{
          background: 'var(--card-bg, var(--panel))',
          border: '1.5px solid var(--line)',
          boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
        }}
      >
        <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
          <h4 className="text-lg font-bold flex items-center gap-2.5" style={{ color: 'var(--text)' }}>
            <ImageIcon className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            <span>Photos With No Detected Face ({unrecognized.no_face_photos.length} photos)</span>
          </h4>

          {batchTargetPerson && selectedPhotoIds.size > 0 && (
            <button
              onClick={handleExecuteBatchAssign}
              className="btn pri"
              style={{ height: '42px', padding: '0 20px', borderRadius: '4px', fontSize: '14px', fontWeight: 700 }}
            >
              <Check className="w-4 h-4 mr-1" />
              <span>Add {selectedPhotoIds.size} Photos to {batchTargetPerson.label || batchTargetPerson.id}</span>
            </button>
          )}
        </div>

        <p className="text-sm mb-5 leading-relaxed" style={{ color: 'var(--muted)' }}>
          Every photo stays reachable. These photos contain no face above detection thresholds, but remain indexed and accessible. You can select and batch-assign them to any person cluster.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3.5" data-testid="no-face-photos-list">
          {unrecognized.no_face_photos.map((photoId) => {
            const pInfo = photos[photoId];
            const thumbUrl = pInfo?.thumb || `/thumbs/${photoId}.jpg`;
            const fileName = pInfo?.file_name || `${photoId}.jpg`;
            const isSelected = selectedPhotoIds.has(photoId);

            return (
              <div
                key={photoId}
                onClick={() => handleTogglePhoto(photoId)}
                className="group rounded overflow-hidden relative cursor-pointer transition-all flex flex-col"
                style={{
                  background: 'var(--input)',
                  border: isSelected ? '2.5px solid var(--accent)' : '1.5px solid var(--line)',
                  boxShadow: isSelected ? '2px 3px 0px var(--accent)' : '2px 2px 0px rgba(0,0,0,0.15)',
                }}
              >
                <div className="aspect-[4/3] w-full relative overflow-hidden bg-black/40">
                  <img
                    src={thumbUrl}
                    alt={fileName}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2327272a"><rect width="24" height="24"/></svg>';
                    }}
                  />

                  {/* Selection Checkbox */}
                  <div className="absolute top-2 left-2 z-10">
                    <div
                      className="w-6 h-6 rounded flex items-center justify-center transition-colors"
                      style={{
                        background: isSelected ? 'var(--accent)' : 'rgba(0,0,0,0.6)',
                        color: isSelected ? 'var(--on-accent)' : '#fff',
                        border: isSelected ? 'none' : '1.5px solid var(--line)',
                      }}
                    >
                      {isSelected && <Check className="w-4 h-4" />}
                    </div>
                  </div>

                  {/* Open in Viewer Button */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenPhotoViewer(photoId);
                    }}
                    className="absolute top-2 right-2 p-1.5 rounded transition-opacity opacity-0 group-hover:opacity-100"
                    style={{ background: 'var(--panel)', border: '1px solid var(--line)', color: 'var(--text)' }}
                    title="View full photo"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>

                <div
                  className="p-2.5 truncate"
                  style={{
                    background: 'var(--card-bg)',
                    borderTop: '1px solid var(--line)',
                    fontSize: '13px',
                    fontFamily: "'JetBrains Mono', monospace",
                    color: 'var(--text)',
                  }}
                  title={fileName}
                >
                  {fileName}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
