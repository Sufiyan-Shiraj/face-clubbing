import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  Users,
  Image as ImageIcon,
  UserPlus,
  Link2,
  HelpCircle,
  Undo2,
  Check,
  AlertTriangle,
  Loader2,
  CopyCheck,
} from 'lucide-react';
import { WhatChangedResponse } from '../types';

export interface WhatChangedModalProps {
  diff: WhatChangedResponse;
  onClose: () => void;
  onUndoAddition?: () => Promise<void>;
  onViewPerson?: (personId: string) => void;
  theme?: string;
}

export const WhatChangedModal: React.FC<WhatChangedModalProps> = ({
  diff,
  onClose,
  onUndoAddition,
  onViewPerson,
  theme = 't-dark',
}) => {
  const [isUndoing, setIsUndoing] = useState(false);
  const [confirmUndo, setConfirmUndo] = useState(false);
  const [undoError, setUndoError] = useState<string | null>(null);

  const handleExecuteUndo = async () => {
    if (!onUndoAddition) return;
    setIsUndoing(true);
    setUndoError(null);
    try {
      await onUndoAddition();
      onClose();
    } catch (err: any) {
      setUndoError(err.message || 'Rollback failed.');
      setIsUndoing(false);
    }
  };

  const joinedPeopleEntries = Object.entries(diff.joined_existing || {});

  return (
    <div
      id="what-changed-modal-overlay"
      data-testid="what-changed-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="what-changed-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isUndoing) onClose();
      }}
    >
      <div
        id="what-changed-modal-card"
        data-testid="what-changed-modal-card"
        className={`w-full max-w-2xl max-h-[90vh] flex flex-col rounded-xl overflow-hidden shadow-2xl ${theme}`}
        style={{
          background: 'var(--card-bg)',
          border: '2px solid var(--line)',
          color: 'var(--text)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          className="flex items-center justify-between px-6 py-4 flex-shrink-0"
          style={{ borderBottom: '1.5px solid var(--line)', background: 'var(--bg)' }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'var(--accent)', color: 'var(--bg)' }}
            >
              <CopyCheck className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h2 id="what-changed-modal-title" className="text-base font-bold font-mono tracking-tight">
                What Changed in This Addition
              </h2>
              <p className="text-xs text-[var(--muted)]">
                Structured diff report for incremental source ingestion
              </p>
            </div>
          </div>
          <button
            id="btn-close-what-changed"
            data-testid="btn-close-what-changed"
            type="button"
            disabled={isUndoing}
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--line)] transition-colors"
            aria-label="Close what changed modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {undoError && (
            <div
              id="what-changed-undo-error"
              data-testid="what-changed-undo-error"
              className="p-3 rounded-lg flex items-center gap-2.5 text-xs font-mono"
              style={{
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1.5px solid #ef4444',
                color: '#f87171',
              }}
            >
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{undoError}</span>
            </div>
          )}

          {/* Frozen Mode Invariant Shield */}
          <div
            id="frozen-invariant-badge"
            data-testid="frozen-invariant-badge"
            className="p-3 rounded-lg flex items-center justify-between text-xs font-mono"
            style={{
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1.5px solid #10b981',
              color: '#34d399',
            }}
          >
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 flex-shrink-0" />
              <span className="font-bold">Frozen Invariant Verified</span>
            </div>
            <span className="text-[11px] opacity-90">
              0 existing people membership changes
            </span>
          </div>

          {/* Metric Stat Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div
              id="stat-new-photos"
              data-testid="stat-new-photos"
              className="p-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex flex-col"
            >
              <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
                <ImageIcon className="w-3.5 h-3.5" />
                <span>New Photos</span>
              </div>
              <span className="text-xl font-mono font-bold text-[var(--accent)]">
                +{diff.new_photos_count}
              </span>
              {(diff.skipped_duplicate_photos ?? 0) > 0 && (
                <span className="text-[11px] text-[var(--muted)] mt-0.5">
                  {diff.skipped_duplicate_photos} duplicates skipped
                </span>
              )}
            </div>

            <div
              id="stat-new-people"
              data-testid="stat-new-people"
              className="p-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex flex-col"
            >
              <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
                <UserPlus className="w-3.5 h-3.5" />
                <span>New People</span>
              </div>
              <span className="text-xl font-mono font-bold text-amber-400">
                +{diff.new_people_count}
              </span>
              <span className="text-[11px] text-[var(--muted)] mt-0.5">
                New unique clusters
              </span>
            </div>

            <div
              id="stat-joined-existing"
              data-testid="stat-joined-existing"
              className="p-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex flex-col"
            >
              <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
                <Link2 className="w-3.5 h-3.5" />
                <span>Attached Faces</span>
              </div>
              <span className="text-xl font-mono font-bold text-emerald-400">
                +{diff.joined_existing_count}
              </span>
              <span className="text-[11px] text-[var(--muted)] mt-0.5">
                To {joinedPeopleEntries.length} existing people
              </span>
            </div>

            <div
              id="stat-unrec-faces"
              data-testid="stat-unrec-faces"
              className="p-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex flex-col"
            >
              <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Unrecognized Faces</span>
              </div>
              <span className="text-xl font-mono font-bold text-[var(--text)]">
                +{diff.new_unrecognized_faces_count}
              </span>
              <span className="text-[11px] text-[var(--muted)] mt-0.5">
                In unrecognized triage
              </span>
            </div>

            <div
              id="stat-unrec-photos"
              data-testid="stat-unrec-photos"
              className="p-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex flex-col"
            >
              <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
                <ImageIcon className="w-3.5 h-3.5" />
                <span>No-Face Photos</span>
              </div>
              <span className="text-xl font-mono font-bold text-[var(--text)]">
                +{diff.new_unrecognized_photos_count}
              </span>
              <span className="text-[11px] text-[var(--muted)] mt-0.5">
                Zero faces detected
              </span>
            </div>

            <div
              id="stat-membership-delta"
              data-testid="stat-membership-delta"
              className="p-3 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex flex-col"
            >
              <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
                <Users className="w-3.5 h-3.5" />
                <span>Membership Delta</span>
              </div>
              <span className="text-xl font-mono font-bold text-emerald-400">
                0
              </span>
              <span className="text-[11px] text-[var(--muted)] mt-0.5">
                Existing strictly preserved
              </span>
            </div>
          </div>

          {/* New People Section */}
          {diff.new_people_ids && diff.new_people_ids.length > 0 && (
            <div id="section-new-people" data-testid="section-new-people" className="space-y-2">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)] flex items-center justify-between">
                <span>Newly Formed People ({diff.new_people_ids.length})</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {diff.new_people_ids.map((pid) => (
                  <button
                    key={pid}
                    type="button"
                    onClick={() => {
                      onViewPerson?.(pid);
                      onClose();
                    }}
                    className="px-2.5 py-1.5 rounded-lg border border-[var(--line)] bg-[var(--bg)] text-xs font-mono hover:border-[var(--accent)] hover:text-[var(--accent)] transition-all flex items-center gap-1.5"
                    title={`View person ${pid}`}
                  >
                    <UserPlus className="w-3 h-3 text-amber-400" />
                    <span>{pid}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Attached Faces into Existing People Section */}
          {joinedPeopleEntries.length > 0 && (
            <div id="section-joined-existing" data-testid="section-joined-existing" className="space-y-2">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)]">
                Existing People Gained Photos ({joinedPeopleEntries.length})
              </h3>
              <div className="divide-y divide-[var(--line)] rounded-lg border border-[var(--line)] bg-[var(--bg)] overflow-hidden">
                {joinedPeopleEntries.map(([pid, info]: [string, any]) => (
                  <div
                    key={pid}
                    className="p-3 flex items-center justify-between text-xs font-mono"
                  >
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          onViewPerson?.(pid);
                          onClose();
                        }}
                        className="font-bold text-[var(--text)] hover:text-[var(--accent)] transition-colors underline decoration-dotted"
                      >
                        {info.person_name || pid}
                      </button>
                      <span className="text-[10px] text-[var(--muted)]">({pid})</span>
                    </div>
                    <div className="flex items-center gap-3 text-[var(--muted)]">
                      <span className="text-emerald-400 font-bold">
                        +{info.new_faces_count} {info.new_faces_count === 1 ? 'face' : 'faces'}
                      </span>
                      {info.new_photo_ids && info.new_photo_ids.length > 0 && (
                        <span>
                          +{info.new_photo_ids.length} {info.new_photo_ids.length === 1 ? 'photo' : 'photos'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rollback Confirmation Warning if Clicked */}
          {confirmUndo && (
            <div
              id="confirm-undo-container"
              data-testid="confirm-undo-container"
              className="p-4 rounded-lg border border-amber-500/50 bg-amber-500/10 space-y-3"
            >
              <div className="flex items-start gap-2.5 text-xs text-amber-300">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">Confirm Rollback to Pre-Addition Snapshot</p>
                  <p className="mt-1 opacity-90 leading-relaxed">
                    This will discard all photos, face embeddings, and clusters introduced in this incremental addition. Any state prior to this addition will be fully restored.
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  id="btn-cancel-confirm-undo"
                  data-testid="btn-cancel-confirm-undo"
                  disabled={isUndoing}
                  onClick={() => setConfirmUndo(false)}
                  className="px-3 py-1.5 rounded text-xs font-mono border border-[var(--line)] bg-[var(--bg)] hover:bg-[var(--line)] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  id="btn-execute-undo"
                  data-testid="btn-execute-undo"
                  disabled={isUndoing}
                  onClick={handleExecuteUndo}
                  className="px-4 py-1.5 rounded text-xs font-mono font-bold bg-amber-500 text-black hover:bg-amber-400 transition-colors flex items-center gap-1.5"
                >
                  {isUndoing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Rolling Back...</span>
                    </>
                  ) : (
                    <>
                      <Undo2 className="w-3.5 h-3.5" />
                      <span>Yes, Rollback Addition</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div
          className="flex items-center justify-between px-6 py-4 flex-shrink-0"
          style={{ borderTop: '1.5px solid var(--line)', background: 'var(--bg)' }}
        >
          {onUndoAddition && !confirmUndo ? (
            <button
              id="btn-trigger-undo-addition"
              data-testid="btn-trigger-undo-addition"
              type="button"
              disabled={isUndoing}
              onClick={() => setConfirmUndo(true)}
              className="px-4 py-2 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 border border-amber-500/50 text-amber-400 hover:bg-amber-500/10 transition-colors"
            >
              <Undo2 className="w-4 h-4" />
              <span>Undo This Addition</span>
            </button>
          ) : (
            <div />
          )}

          <button
            id="btn-accept-what-changed"
            data-testid="btn-accept-what-changed"
            type="button"
            disabled={isUndoing}
            onClick={onClose}
            className="px-5 py-2 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all"
            style={{
              background: 'var(--accent)',
              color: 'var(--bg)',
            }}
          >
            <Check className="w-4 h-4 stroke-[2.5]" />
            <span>Accept & Continue Review</span>
          </button>
        </div>
      </div>
    </div>
  );
};
