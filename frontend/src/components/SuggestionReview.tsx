import React, { useState } from 'react';
import { RankedPairSuggestion, PersonCluster } from '../types';
import { Check, X, Sparkles, Filter } from 'lucide-react';

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
    <div className="space-y-6 animate-fadeIn" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Top Filter and Info Bar */}
      <div
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded"
        style={{
          background: 'var(--card-bg, var(--panel))',
          border: '1.5px solid var(--line)',
          boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
        }}
      >
        <div className="flex items-center gap-3.5">
          <div
            className="w-10 h-10 rounded flex items-center justify-center flex-shrink-0"
            style={{
              background: 'var(--input)',
              border: '1.5px solid var(--accent)',
              color: 'var(--accent)',
            }}
          >
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold" style={{ color: 'var(--text)' }}>
              Smart Match Suggestions
            </h3>
            <p className="text-sm mt-0.5" style={{ color: 'var(--muted)' }}>
              Ranked pairs calculated by centroid cosine distance. Rejected pairs stay hidden for this session.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" style={{ color: 'var(--muted)' }}>
            <Filter className="w-4 h-4" /> Filter:
          </span>
          <button
            onClick={() => setFilterType('all')}
            className="px-3.5 py-1.5 rounded text-xs font-bold transition-all"
            style={{
              background: filterType === 'all' ? 'var(--accent)' : 'var(--input)',
              color: filterType === 'all' ? 'var(--on-accent)' : 'var(--text)',
              border: filterType === 'all' ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
              cursor: 'pointer',
            }}
          >
            All ({suggestions.filter((s) => !rejectedPairs.has(getPairKey(s.person_a_id, s.person_b_id))).length})
          </button>
          <button
            onClick={() => setFilterType('medium')}
            className="px-3.5 py-1.5 rounded text-xs font-bold transition-all"
            style={{
              background: filterType === 'medium' ? 'var(--accent)' : 'var(--input)',
              color: filterType === 'medium' ? 'var(--on-accent)' : 'var(--text)',
              border: filterType === 'medium' ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
              cursor: 'pointer',
            }}
          >
            Medium
          </button>
          <button
            onClick={() => setFilterType('low')}
            className="px-3.5 py-1.5 rounded text-xs font-bold transition-all"
            style={{
              background: filterType === 'low' ? 'var(--accent)' : 'var(--input)',
              color: filterType === 'low' ? 'var(--on-accent)' : 'var(--text)',
              border: filterType === 'low' ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
              cursor: 'pointer',
            }}
          >
            Low (Single-Photo)
          </button>
        </div>
      </div>

      {/* Suggestion Cards List */}
      {activeSuggestions.length === 0 ? (
        <div
          className="text-center py-14 rounded"
          style={{
            background: 'var(--card-bg, var(--panel))',
            border: '1.5px solid var(--line)',
            color: 'var(--muted)',
            boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
          }}
        >
          <Check className="w-9 h-9 mx-auto mb-2" style={{ color: 'var(--accent)' }} />
          <h4 className="text-lg font-bold" style={{ color: 'var(--text)' }}>No Pending Suggestions</h4>
          <p className="text-sm mt-1 max-w-sm mx-auto">
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
                className="p-5 sm:p-6 rounded flex flex-col md:flex-row md:items-center justify-between gap-5"
                style={{
                  background: 'var(--card-bg, var(--panel))',
                  border: '1.5px solid var(--line)',
                  boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
                }}
              >
                {/* Comparison Pair Grid */}
                <div className="flex items-center gap-4 sm:gap-8 flex-1 flex-wrap sm:flex-nowrap">
                  {/* Person A */}
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div
                      className="w-20 h-20 sm:w-24 sm:h-24 rounded overflow-hidden flex-shrink-0"
                      style={{
                        background: 'var(--input)',
                        border: '2px solid var(--line)',
                      }}
                    >
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
                      <span className="text-base sm:text-lg font-bold font-mono truncate block" style={{ color: 'var(--text)' }}>
                        {nameA}
                      </span>
                      <span className="text-xs font-mono" style={{ color: 'var(--muted)' }}>
                        {pA?.photo_count ?? s.person_a_photos} photos
                      </span>
                    </div>
                  </div>

                  {/* Middle Match Metrics */}
                  <div
                    className="flex flex-col items-center justify-center px-4 py-3 rounded text-center flex-shrink-0 mx-auto"
                    style={{
                      background: 'var(--input)',
                      border: '1.5px solid var(--line)',
                    }}
                  >
                    <span className="text-xs font-mono font-medium" style={{ color: 'var(--muted)' }}>Distance</span>
                    <span className="text-base sm:text-lg font-bold font-mono" style={{ color: 'var(--accent)' }}>
                      {s.distance.toFixed(4)}
                    </span>
                    <div className="mt-1 flex flex-col items-center gap-1">
                      <span className="riso-tab-badge">
                        {s.reason}
                      </span>
                      {isLowConfidence && (
                        <span className="riso-badge-accent text-xs">
                          Single-Photo
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Person B */}
                  <div className="flex items-center gap-4 flex-1 min-w-0 justify-end">
                    <div className="text-right min-w-0">
                      <span className="text-base sm:text-lg font-bold font-mono truncate block" style={{ color: 'var(--text)' }}>
                        {nameB}
                      </span>
                      <span className="text-xs font-mono" style={{ color: 'var(--muted)' }}>
                        {pB?.photo_count ?? s.person_b_photos} photos
                      </span>
                    </div>
                    <div
                      className="w-20 h-20 sm:w-24 sm:h-24 rounded overflow-hidden flex-shrink-0"
                      style={{
                        background: 'var(--input)',
                        border: '2px solid var(--line)',
                      }}
                    >
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
                <div
                  className="flex items-center justify-end gap-3 pt-3 md:pt-0"
                  style={{ borderTop: '1px solid var(--line)' }}
                >
                  <button
                    data-testid="reject-suggestion-btn"
                    onClick={() => onReject(s.person_a_id, s.person_b_id)}
                    className="riso-btn-sec"
                    style={{ height: '44px', padding: '0 18px', fontSize: '14px' }}
                  >
                    <X className="w-4 h-4" />
                    <span>Reject</span>
                  </button>

                  <button
                    data-testid="accept-suggestion-btn"
                    onClick={() => onAccept(s.person_a_id, s.person_b_id)}
                    className="btn pri"
                    style={{
                      height: '44px',
                      padding: '0 22px',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontWeight: 800,
                      boxShadow: '2px 3px 0px rgba(0,0,0,0.25)',
                    }}
                  >
                    <Check className="w-4 h-4 mr-1" />
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
