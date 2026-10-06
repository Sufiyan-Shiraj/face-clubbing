import React, { useState } from 'react';
import { RankedPairSuggestion, PersonCluster } from '../types';
import { Check, X, Sparkles, Filter, AlertCircle, Users } from 'lucide-react';

interface SuggestionReviewProps {
  suggestions: RankedPairSuggestion[];
  peopleMap: Record<string, PersonCluster>;
  onAccept: (personAId: string, personBId: string) => void;
  onReject: (personAId: string, personBId: string) => void;
  rejectedPairs: Set<string>;
}

export const SuggestionReview: React.FC<SuggestionReviewProps> = ({
  suggestions,
  peopleMap,
  onAccept,
  onReject,
  rejectedPairs,
}) => {
  const [filterType, setFilterType] = useState<'all' | 'medium' | 'low'>('all');

  // Pair key helper
  const getPairKey = (idA: string, idB: string) => {
    return [idA, idB].sort().join(':::');
  };

  // Filter out session-rejected suggestions
  const activeSuggestions = suggestions.filter((s) => {
    const key = getPairKey(s.person_a_id, s.person_b_id);
    if (rejectedPairs.has(key)) return false;
    if (filterType === 'medium') return s.confidence === 'medium';
    if (filterType === 'low') return s.confidence === 'low';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Filter and Info Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <div>
            <h3 className="text-sm font-semibold text-white">Smart Match Suggestions</h3>
            <p className="text-xs text-neutral-400">
              Ranked pairs calculated by centroid cosine distance. Rejected pairs stay hidden for this session.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-neutral-500 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          <button
            onClick={() => setFilterType('all')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
              filterType === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
            }`}
          >
            All ({suggestions.filter((s) => !rejectedPairs.has(getPairKey(s.person_a_id, s.person_b_id))).length})
          </button>
          <button
            onClick={() => setFilterType('medium')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
              filterType === 'medium'
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Medium
          </button>
          <button
            onClick={() => setFilterType('low')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
              filterType === 'low'
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-800 text-neutral-400 hover:text-neutral-200'
            }`}
          >
            Low (Single-Photo)
          </button>
        </div>
      </div>

      {/* Suggestion Cards List */}
      {activeSuggestions.length === 0 ? (
        <div className="text-center py-12 border border-neutral-800/80 rounded-2xl bg-neutral-900/30">
          <Check className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
          <h4 className="text-base font-semibold text-neutral-200">No Pending Suggestions</h4>
          <p className="text-xs text-neutral-500 mt-1 max-w-sm mx-auto">
            All suggestions in this category have been reviewed, accepted, or rejected for this session.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4" data-testid="suggestions-list">
          {activeSuggestions.map((s, idx) => {
            const pA = peopleMap[s.person_a_id];
            const pB = peopleMap[s.person_b_id];
            const nameA = pA?.label || s.person_a_id;
            const nameB = pB?.label || s.person_b_id;
            const faceA = pA?.face || `faces/${s.person_a_id}.jpg`;
            const faceB = pB?.face || `faces/${s.person_b_id}.jpg`;
            const isLowConfidence = s.confidence === 'low' || s.person_a_photos === 1 || s.person_b_photos === 1;

            return (
              <div
                key={idx}
                data-testid={`suggestion-card-${s.person_a_id}-${s.person_b_id}`}
                className="glass-card rounded-2xl p-4 sm:p-5 bg-neutral-900/70 border border-neutral-800 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Comparison Pair Grid */}
                <div className="flex items-center gap-3 sm:gap-6 flex-1">
                  {/* Person A */}
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl overflow-hidden bg-neutral-950 border border-neutral-800 flex-shrink-0">
                      <img
                        src={faceA}
                        alt={nameA}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src =
                            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2352525b"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                        }}
                      />
                    </div>
                    <div className="min-w-0">
                      <span className="text-xs sm:text-sm font-bold text-white truncate block">{nameA}</span>
                      <span className="text-[11px] text-neutral-400 font-mono">
                        {pA?.photo_count ?? s.person_a_photos} photos
                      </span>
                    </div>
                  </div>

                  {/* Middle Match Metrics */}
                  <div className="flex flex-col items-center justify-center px-2 sm:px-4 py-2 rounded-xl bg-neutral-950/80 border border-neutral-800/80 text-center flex-shrink-0">
                    <span className="text-[10px] text-neutral-500 font-mono">Distance</span>
                    <span className="text-xs sm:text-sm font-bold font-mono text-blue-400">
                      {s.distance.toFixed(4)}
                    </span>
                    <div className="mt-1 flex flex-col items-center gap-1">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${
                          s.reason === 'same_photo_conflict'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-blue-500/10 text-blue-300'
                        }`}
                      >
                        {s.reason}
                      </span>
                      {isLowConfidence && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] bg-neutral-800 text-amber-400 border border-neutral-700">
                          Low Confidence (Single-Photo)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Person B */}
                  <div className="flex items-center gap-3 flex-1 min-w-0 justify-end">
                    <div className="text-right min-w-0">
                      <span className="text-xs sm:text-sm font-bold text-white truncate block">{nameB}</span>
                      <span className="text-[11px] text-neutral-400 font-mono">
                        {pB?.photo_count ?? s.person_b_photos} photos
                      </span>
                    </div>
                    <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl overflow-hidden bg-neutral-950 border border-neutral-800 flex-shrink-0">
                      <img
                        src={faceB}
                        alt={nameB}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src =
                            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2352525b"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Actions: Accept & Reject */}
                <div className="flex items-center justify-end gap-2 pt-2 md:pt-0 border-t md:border-t-0 border-neutral-800">
                  <button
                    data-testid="reject-suggestion-btn"
                    onClick={() => onReject(s.person_a_id, s.person_b_id)}
                    className="px-3.5 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 hover:text-white text-xs font-semibold border border-neutral-700 flex items-center gap-1.5 transition-colors"
                  >
                    <X className="w-4 h-4 text-neutral-400" />
                    <span>Reject</span>
                  </button>

                  <button
                    data-testid="accept-suggestion-btn"
                    onClick={() => onAccept(s.person_a_id, s.person_b_id)}
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/20 flex items-center gap-1.5 transition-all"
                  >
                    <Check className="w-4 h-4" />
                    <span>Accept & Merge</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
