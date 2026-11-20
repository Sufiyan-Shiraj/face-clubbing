import React, { useState, useEffect } from 'react';
import { ProjectItem, MergeConflictItem, MergeProjectsResponse } from '../types';
import { apiClient } from '../api/client';
import {
  X,
  GitMerge,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Folder,
  Layers,
  ArrowRight,
  ShieldCheck,
  Info,
} from 'lucide-react';

interface MergeProjectsModalProps {
  onClose: () => void;
  onMergedSuccess: (response: MergeProjectsResponse) => void;
  theme?: string;
}

export const MergeProjectsModal: React.FC<MergeProjectsModalProps> = ({
  onClose,
  onMergedSuccess,
  theme = 't-dark',
}) => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [projAId, setProjAId] = useState<string>('');
  const [projBId, setProjBId] = useState<string>('');
  const [customName, setCustomName] = useState<string>('');
  const [isMerging, setIsMerging] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [mergeResult, setMergeResult] = useState<MergeProjectsResponse | null>(null);
  const [conflictResolutions, setConflictResolutions] = useState<
    Record<number, { choice: 'a' | 'b' | 'both' | 'custom'; customText: string }>
  >({});
  const [isApplyingResolutions, setIsApplyingResolutions] = useState<boolean>(false);

  useEffect(() => {
    loadRecentProjects();
  }, []);

  const loadRecentProjects = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await apiClient.getRecentProjects();
      const list = Array.isArray(data) ? data : ((data as any)?.projects || []);
      setProjects(list);
      if (list.length >= 2) {
        setProjAId(list[0].id);
        setProjBId(list[1].id);
      } else if (list.length === 1) {
        setProjAId(list[0].id);
        setProjBId(list[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load recent projects');
    } finally {
      setIsLoading(false);
    }
  };

  const selectedProjA = projects.find((p) => p.id === projAId);
  const selectedProjB = projects.find((p) => p.id === projBId);

  const handleExecuteMerge = async () => {
    if (!selectedProjA || !selectedProjB) {
      setErrorMsg('Please select two valid projects to merge.');
      return;
    }
    setIsMerging(true);
    setErrorMsg(null);
    try {
      const name = customName.trim() || `Merged: ${selectedProjA.name} + ${selectedProjB.name}`;
      const res: MergeProjectsResponse = await apiClient.mergeProjects({
        project_a_work_dir: selectedProjA.work_dir,
        project_b_work_dir: selectedProjB.work_dir,
        new_project_name: name,
      });
      setMergeResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to merge projects. Please ensure both projects use identical settings.');
    } finally {
      setIsMerging(false);
    }
  };

  const handleApplyResolutionsAndOpen = async () => {
    if (!mergeResult) return;
    setIsApplyingResolutions(true);
    try {
      for (let i = 0; i < mergeResult.conflicts.length; i++) {
        const c = mergeResult.conflicts[i];
        if (c.conflict_type === 'name_conflict') {
          const res = conflictResolutions[i] || { choice: 'a', customText: '' };
          let finalLabel = String(c.val_a || '');
          if (res.choice === 'b') {
            finalLabel = String(c.val_b || '');
          } else if (res.choice === 'both') {
            finalLabel = `${c.val_a} / ${c.val_b}`;
          } else if (res.choice === 'custom' && res.customText.trim()) {
            finalLabel = res.customText.trim();
          }

          try {
            await apiClient.applyEdit({
              op: 'name',
              person: [c.entity_id],
              label: finalLabel,
            });
          } catch (e) {
            console.warn(`Failed to apply resolved name to ${c.entity_id}:`, e);
          }
        }
      }
      onMergedSuccess(mergeResult);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to apply conflict resolutions.');
    } finally {
      setIsApplyingResolutions(false);
    }
  };

  return (
    <div
      data-testid="merge-projects-modal"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh] rounded"
        style={{
          background: 'var(--bg)',
          border: '2px solid var(--line)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.75), 0 0 0 1px var(--line)',
          color: 'var(--text)',
          fontFamily: "'JetBrains Mono', monospace",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex-shrink-0 flex items-center justify-between px-5 py-4 border-b"
          style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded flex items-center justify-center"
              style={{
                background: 'var(--bg)',
                border: '1.5px solid var(--accent)',
                color: 'var(--accent)',
              }}
            >
              <GitMerge className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono tracking-tight" style={{ color: 'var(--text)' }}>
                Merge Two Projects
              </h2>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                Union photos into a new project while leaving original projects untouched
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="riso-btn-sec"
            style={{ width: '36px', height: '36px', padding: 0 }}
            title="Close (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {errorMsg && (
            <div
              data-testid="merge-error-alert"
              className="p-3 rounded flex items-start gap-2.5 text-xs"
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1.5px solid #ef4444',
                color: '#f87171',
              }}
            >
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-400" />
              <div>
                <p className="font-bold">Cannot Merge Projects</p>
                <p className="mt-1 opacity-90">{errorMsg}</p>
              </div>
            </div>
          )}

          {mergeResult ? (
            /* Post-Merge Summary View */
            <div className="space-y-4">
              <div
                className="p-4 rounded border text-xs space-y-3"
                style={{
                  background: 'rgba(16, 185, 129, 0.08)',
                  borderColor: '#10b981',
                }}
              >
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Projects Merged Successfully!</span>
                </div>
                <p className="text-[var(--text)]">
                  Created new project <strong>{mergeResult.project_name}</strong>.
                </p>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
                  <div className="p-2 rounded bg-[var(--panel)] border border-[var(--line)]">
                    <span className="block text-[10px] text-[var(--muted)]">Total Photos</span>
                    <span className="text-base font-bold text-[var(--text)]">{mergeResult.total_photos}</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--panel)] border border-[var(--line)]">
                    <span className="block text-[10px] text-[var(--muted)]">Shared (Union)</span>
                    <span className="text-base font-bold text-[var(--accent)]">{mergeResult.shared_photos}</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--panel)] border border-[var(--line)]">
                    <span className="block text-[10px] text-[var(--muted)]">People Formed</span>
                    <span className="text-base font-bold text-[var(--text)]">{mergeResult.people_count}</span>
                  </div>
                  <div className="p-2 rounded bg-[var(--panel)] border border-[var(--line)]">
                    <span className="block text-[10px] text-[var(--muted)]">Edits Combined</span>
                    <span className="text-base font-bold text-[var(--text)]">{mergeResult.edits_applied}</span>
                  </div>
                </div>
              </div>

              {/* Conflict Review & Side-by-Side Resolution Section */}
              {mergeResult.conflicts_count > 0 ? (
                <div
                  data-testid="merge-conflicts-section"
                  className="p-3.5 rounded border text-xs space-y-3"
                  style={{
                    background: 'rgba(245, 158, 11, 0.08)',
                    borderColor: '#f59e0b',
                  }}
                >
                  <div className="flex items-center gap-2 text-amber-500 font-bold">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>Review Needed: {mergeResult.conflicts_count} Conflicts Flagged</span>
                  </div>
                  <p className="text-[var(--muted)] text-[11px] leading-relaxed">
                    Choose how each conflict should be resolved in the merged project. Naming choices can be selected side-by-side or given a custom name:
                  </p>

                  <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                    {mergeResult.conflicts.map((c, idx) => {
                      const isNameConflict = c.conflict_type === 'name_conflict';
                      const currentRes = conflictResolutions[idx] || { choice: 'a', customText: '' };

                      return (
                        <div
                          key={idx}
                          data-testid={`conflict-item-${idx}`}
                          className="p-3 rounded space-y-2"
                          style={{
                            background: 'var(--panel)',
                            border: '1.5px solid var(--line)',
                          }}
                        >
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-bold text-amber-500 uppercase tracking-wider">
                              [{c.conflict_type.replace('_', ' ')}]
                            </span>
                            <span className="font-mono text-[var(--muted)]">{c.entity_id}</span>
                          </div>
                          <p className="text-[11px] text-[var(--text)]">{c.description}</p>

                          {isNameConflict && (
                            <div className="pt-2 border-t border-[var(--line)] space-y-2">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)] block">
                                Choose Resolved Name:
                              </span>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                                {/* Option A */}
                                <label
                                  className="flex items-center gap-2 p-2 rounded cursor-pointer border"
                                  style={{
                                    borderColor: currentRes.choice === 'a' ? 'var(--accent)' : 'var(--line)',
                                    background: currentRes.choice === 'a' ? 'rgba(250, 113, 117, 0.08)' : 'var(--bg)',
                                  }}
                                >
                                  <input
                                    type="radio"
                                    name={`conflict-${idx}`}
                                    data-testid={`radio-keep-a-${idx}`}
                                    checked={currentRes.choice === 'a'}
                                    onChange={() =>
                                      setConflictResolutions((prev) => ({
                                        ...prev,
                                        [idx]: { ...currentRes, choice: 'a' },
                                      }))
                                    }
                                    className="accent-[var(--accent)]"
                                  />
                                  <span className="truncate">Keep A: <strong>&quot;{c.val_a}&quot;</strong></span>
                                </label>

                                {/* Option B */}
                                <label
                                  className="flex items-center gap-2 p-2 rounded cursor-pointer border"
                                  style={{
                                    borderColor: currentRes.choice === 'b' ? 'var(--accent)' : 'var(--line)',
                                    background: currentRes.choice === 'b' ? 'rgba(250, 113, 117, 0.08)' : 'var(--bg)',
                                  }}
                                >
                                  <input
                                    type="radio"
                                    name={`conflict-${idx}`}
                                    data-testid={`radio-keep-b-${idx}`}
                                    checked={currentRes.choice === 'b'}
                                    onChange={() =>
                                      setConflictResolutions((prev) => ({
                                        ...prev,
                                        [idx]: { ...currentRes, choice: 'b' },
                                      }))
                                    }
                                    className="accent-[var(--accent)]"
                                  />
                                  <span className="truncate">Keep B: <strong>&quot;{c.val_b}&quot;</strong></span>
                                </label>

                                {/* Option Both */}
                                <label
                                  className="flex items-center gap-2 p-2 rounded cursor-pointer border"
                                  style={{
                                    borderColor: currentRes.choice === 'both' ? 'var(--accent)' : 'var(--line)',
                                    background: currentRes.choice === 'both' ? 'rgba(250, 113, 117, 0.08)' : 'var(--bg)',
                                  }}
                                >
                                  <input
                                    type="radio"
                                    name={`conflict-${idx}`}
                                    data-testid={`radio-keep-both-${idx}`}
                                    checked={currentRes.choice === 'both'}
                                    onChange={() =>
                                      setConflictResolutions((prev) => ({
                                        ...prev,
                                        [idx]: { ...currentRes, choice: 'both' },
                                      }))
                                    }
                                    className="accent-[var(--accent)]"
                                  />
                                  <span className="truncate">Combine: <strong>&quot;{c.val_a} / {c.val_b}&quot;</strong></span>
                                </label>

                                {/* Option Custom */}
                                <label
                                  className="flex items-center gap-2 p-2 rounded cursor-pointer border"
                                  style={{
                                    borderColor: currentRes.choice === 'custom' ? 'var(--accent)' : 'var(--line)',
                                    background: currentRes.choice === 'custom' ? 'rgba(250, 113, 117, 0.08)' : 'var(--bg)',
                                  }}
                                >
                                  <input
                                    type="radio"
                                    name={`conflict-${idx}`}
                                    data-testid={`radio-custom-${idx}`}
                                    checked={currentRes.choice === 'custom'}
                                    onChange={() =>
                                      setConflictResolutions((prev) => ({
                                        ...prev,
                                        [idx]: { ...currentRes, choice: 'custom' },
                                      }))
                                    }
                                    className="accent-[var(--accent)]"
                                  />
                                  <span>Custom name:</span>
                                </label>
                              </div>

                              {currentRes.choice === 'custom' && (
                                <input
                                  type="text"
                                  data-testid={`input-custom-name-${idx}`}
                                  value={currentRes.customText}
                                  onChange={(e) =>
                                    setConflictResolutions((prev) => ({
                                      ...prev,
                                      [idx]: { ...currentRes, customText: e.target.value },
                                    }))
                                  }
                                  placeholder={`Enter name (default: ${c.val_a})`}
                                  className="w-full text-xs p-2 rounded border riso-input mt-1"
                                  style={{
                                    background: 'var(--bg)',
                                    borderColor: 'var(--line)',
                                    color: 'var(--text)',
                                  }}
                                />
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded border border-[var(--line)] bg-[var(--panel)] text-xs flex items-center gap-2 text-[var(--muted)]">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Zero conflicting names or conflicting face assignments detected.</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  data-testid="open-merged-project-btn"
                  onClick={handleApplyResolutionsAndOpen}
                  disabled={isApplyingResolutions}
                  className="riso-btn-accent text-xs"
                  style={{ height: '36px', padding: '0 18px' }}
                >
                  {isApplyingResolutions ? (
                    <span>Applying Resolutions...</span>
                  ) : (
                    <>
                      <span>{mergeResult.conflicts_count > 0 ? 'Apply Resolutions & Open Project' : 'Open Merged Project'}</span>
                      <ArrowRight className="w-4 h-4 ml-1.5 inline" />
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Setup & Selection Form */
            <div className="space-y-4">
              <div
                className="p-3 rounded border text-xs flex items-start gap-2.5"
                style={{
                  background: 'var(--panel)',
                  borderColor: 'var(--line)',
                  color: 'var(--muted)',
                }}
              >
                <Info className="w-4 h-4 flex-shrink-0 text-[var(--accent)] mt-0.5" />
                <div>
                  <p className="text-[var(--text)] font-semibold">Immutable Parent Projects Guarantee</p>
                  <p className="mt-0.5">
                    Merging creates a <strong>brand new project</strong>. Caches and embeddings are unified by content hash.
                    Parent projects remain 100% untouched.
                  </p>
                </div>
              </div>

              {/* Project A Selection */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[var(--text)]">
                  1. Parent Project A
                </label>
                {isLoading ? (
                  <div className="text-xs text-[var(--muted)] flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Loading saved projects...</span>
                  </div>
                ) : (
                  <select
                    id="select-project-a"
                    data-testid="select-project-a"
                    value={projAId}
                    onChange={(e) => setProjAId(e.target.value)}
                    className="w-full text-xs p-2.5 rounded border riso-input"
                    style={{
                      background: 'var(--panel)',
                      borderColor: 'var(--line)',
                      color: 'var(--text)',
                    }}
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.counts?.photos || 0} photos, {p.counts?.people || 0} people)
                      </option>
                    ))}
                  </select>
                )}
                {selectedProjA && (
                  <p className="text-[10px] text-[var(--muted)] truncate font-mono">
                    {selectedProjA.work_dir}
                  </p>
                )}
              </div>

              {/* Project B Selection */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[var(--text)]">
                  2. Parent Project B
                </label>
                {isLoading ? null : (
                  <select
                    id="select-project-b"
                    data-testid="select-project-b"
                    value={projBId}
                    onChange={(e) => setProjBId(e.target.value)}
                    className="w-full text-xs p-2.5 rounded border riso-input"
                    style={{
                      background: 'var(--panel)',
                      borderColor: 'var(--line)',
                      color: 'var(--text)',
                    }}
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.counts?.photos || 0} photos, {p.counts?.people || 0} people)
                      </option>
                    ))}
                  </select>
                )}
                {selectedProjB && (
                  <p className="text-[10px] text-[var(--muted)] truncate font-mono">
                    {selectedProjB.work_dir}
                  </p>
                )}
              </div>

              {/* Custom Target Name */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[var(--text)]">
                  3. New Project Name (Optional)
                </label>
                <input
                  type="text"
                  id="merged-project-name-input"
                  data-testid="merged-project-name-input"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  placeholder={
                    selectedProjA && selectedProjB
                      ? `Merged: ${selectedProjA.name} + ${selectedProjB.name}`
                      : 'Combined Event Gallery'
                  }
                  className="w-full text-xs p-2.5 rounded border riso-input"
                  style={{
                    background: 'var(--panel)',
                    borderColor: 'var(--line)',
                    color: 'var(--text)',
                  }}
                />
              </div>

              {/* Action Bar */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[var(--line)]">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isMerging}
                  className="riso-btn-sec text-xs"
                  style={{ height: '36px', padding: '0 16px' }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  id="btn-confirm-merge"
                  data-testid="btn-confirm-merge"
                  onClick={handleExecuteMerge}
                  disabled={isMerging || !projAId || !projBId}
                  className="riso-btn-accent text-xs"
                  style={{ height: '36px', padding: '0 20px' }}
                >
                  {isMerging ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" />
                      <span>Merging Projects...</span>
                    </>
                  ) : (
                    <>
                      <GitMerge className="w-3.5 h-3.5 mr-1.5" />
                      <span>Merge Into New Project</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
