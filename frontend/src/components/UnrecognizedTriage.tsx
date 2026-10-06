import React, { useState } from 'react';
import { UnrecognizedData, AmbiguousFaceSuggestion, PersonCluster, PhotoInfo } from '../types';
import { UserPlus, Sparkles, AlertTriangle, ArrowRight, Image as ImageIcon, Check, Filter } from 'lucide-react';

interface UnrecognizedTriageProps {
  unrecognized: UnrecognizedData;
  ambiguousMap: Record<string, AmbiguousFaceSuggestion>;
  people: PersonCluster[];
  photos: Record<string, PhotoInfo>;
  onAssignFace: (faceId: string, targetPersonId?: string | null) => void;
  onOpenPhotoViewer: (photoId: string) => void;
}

export const UnrecognizedTriage: React.FC<UnrecognizedTriageProps> = ({
  unrecognized,
  ambiguousMap,
  people,
  photos,
  onAssignFace,
  onOpenPhotoViewer,
}) => {
  const [reasonFilter, setReasonFilter] = useState<string>('all');
  const [selectedPersonForAssign, setSelectedPersonForAssign] = useState<Record<string, string>>({});

  const filteredFaces = unrecognized.faces.filter((f) => {
    if (reasonFilter === 'all') return true;
    return f.rejection_reason === reasonFilter;
  });

  return (
    <div className="space-y-8">
      {/* Triage Overview Card */}
      <div className="p-5 rounded-2xl bg-neutral-900/60 border border-neutral-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Unrecognized Faces & Non-Detected Photos
          </h3>
          <p className="text-xs text-neutral-400 mt-0.5">
            Faces that could not be reliably attached to a cluster. Assign them to an existing person or create a new person.
          </p>
        </div>

        {/* Reason Filter */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-neutral-500 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Reason:
          </span>
          {['all', 'ambiguous', 'unattached_profile', 'unattached_small', 'unattached_lowscore'].map((r) => (
            <button
              key={r}
              onClick={() => setReasonFilter(r)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-colors ${
                reasonFilter === r
                  ? 'bg-blue-600 text-white'
                  : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {r.replace('unattached_', '')}
            </button>
          ))}
        </div>
      </div>

      {/* Faces Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-semibold text-neutral-300 uppercase tracking-wider">
            Unrecognized Face Crops ({filteredFaces.length})
          </h4>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="unrec-faces-grid">
          {filteredFaces.map((f, idx) => {
            const faceId = f.face_id || `face_${idx}`;
            const ambSuggestion = ambiguousMap[faceId];
            const pInfo = photos[f.photo_id];
            const fileName = pInfo?.file_name || f.file_name || `${f.photo_id}.jpg`;
            const selectedPid = selectedPersonForAssign[faceId] || '';

            return (
              <div
                key={faceId}
                data-testid={`unrec-face-card-${faceId}`}
                className="glass-card rounded-2xl p-4 bg-neutral-900/70 border border-neutral-800 flex flex-col justify-between"
              >
                <div>
                  {/* Face Image & Header */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-16 h-16 rounded-xl overflow-hidden bg-neutral-950 border border-neutral-800 flex-shrink-0">
                      <img
                        src={f.face}
                        alt={faceId}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src =
                            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2352525b"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                        }}
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="text-[11px] font-mono text-neutral-400 truncate block" title={faceId}>
                        {faceId}
                      </span>
                      <span
                        className="text-[10px] text-blue-400 hover:underline cursor-pointer truncate block mt-0.5"
                        onClick={() => onOpenPhotoViewer(f.photo_id)}
                        title={`View photo: ${fileName}`}
                      >
                        {fileName}
                      </span>
                      <span className="inline-block mt-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-neutral-950 text-amber-300 border border-neutral-800">
                        {f.rejection_reason || 'unattached'}
                      </span>
                    </div>
                  </div>

                  {/* Top Candidates for Ambiguous Faces */}
                  {ambSuggestion && ambSuggestion.top_candidates && ambSuggestion.top_candidates.length > 0 && (
                    <div className="mb-3 p-2.5 rounded-xl bg-neutral-950/80 border border-neutral-800/80">
                      <span className="text-[10px] text-neutral-400 font-semibold flex items-center gap-1 mb-1.5">
                        <Sparkles className="w-3 h-3 text-amber-400" />
                        Top Matching Candidates:
                      </span>
                      <div className="space-y-1">
                        {ambSuggestion.top_candidates.slice(0, 3).map((cand, cIdx) => {
                          const candPerson = people.find((p) => p.id === cand.candidate_id);
                          const candName = candPerson?.label || cand.candidate_id;
                          return (
                            <div
                              key={cIdx}
                              className="flex items-center justify-between text-[11px] p-1 rounded bg-neutral-900 border border-neutral-800/60"
                            >
                              <span className="font-mono text-neutral-300 truncate max-w-[90px]">
                                {candName}
                              </span>
                              <div className="flex items-center gap-1.5">
                                <span className="text-neutral-500 font-mono text-[10px]">
                                  d={cand.distance.toFixed(3)}
                                </span>
                                <button
                                  data-testid="quick-assign-btn"
                                  onClick={() => onAssignFace(faceId, cand.candidate_id)}
                                  className="px-1.5 py-0.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-medium"
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
                </div>

                {/* Assignment Controls */}
                <div className="pt-2 border-t border-neutral-800/80 space-y-2">
                  <div className="flex items-center gap-1.5">
                    <select
                      value={selectedPid}
                      onChange={(e) =>
                        setSelectedPersonForAssign({
                          ...selectedPersonForAssign,
                          [faceId]: e.target.value,
                        })
                      }
                      className="flex-1 px-2 py-1 text-xs rounded-lg bg-neutral-950 border border-neutral-800 text-neutral-300 focus:outline-none"
                    >
                      <option value="">Choose person...</option>
                      {people.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.label || p.id} ({p.photo_count}p)
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => {
                        if (selectedPid) onAssignFace(faceId, selectedPid);
                      }}
                      disabled={!selectedPid}
                      className="px-2.5 py-1 rounded-lg bg-neutral-800 hover:bg-neutral-700 disabled:opacity-40 text-neutral-200 text-xs font-medium"
                      title="Assign to selected person"
                    >
                      Assign
                    </button>
                  </div>

                  <button
                    data-testid="create-person-btn"
                    onClick={() => onAssignFace(faceId, null)}
                    className="w-full py-1.5 px-3 rounded-lg bg-neutral-800/80 hover:bg-neutral-700 text-neutral-300 hover:text-white border border-neutral-700/60 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <UserPlus className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Create New Person</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Photos With No Detected Face (Reachability guarantee) */}
      <div className="p-5 rounded-2xl bg-neutral-900/60 border border-neutral-800">
        <h4 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-blue-400" />
          Photos With No Detected Face ({unrecognized.no_face_photos.length} photos)
        </h4>
        <p className="text-xs text-neutral-400 mb-4">
          Every photo stays reachable. These photos contain no face above detection thresholds, but remain indexed and accessible.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3" data-testid="no-face-photos-list">
          {unrecognized.no_face_photos.map((photoId) => {
            const pInfo = photos[photoId];
            const thumbUrl = pInfo?.thumb || `thumbs/${photoId}.jpg`;
            const fileName = pInfo?.file_name || `${photoId}.jpg`;

            return (
              <div
                key={photoId}
                onClick={() => onOpenPhotoViewer(photoId)}
                className="group rounded-xl overflow-hidden bg-neutral-950 border border-neutral-800 aspect-square relative cursor-pointer hover:border-neutral-700 transition-all"
              >
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
                <div className="absolute inset-x-0 bottom-0 p-1.5 bg-gradient-to-t from-black/90 to-transparent">
                  <span className="text-[10px] text-neutral-300 font-mono truncate block" title={fileName}>
                    {fileName}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
