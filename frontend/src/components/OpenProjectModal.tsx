import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { ProjectItem, OpenProjectResponse } from '../types';
import { apiClient } from '../api/client';
import {
  X,
  Folder,
  FolderOpen,
  Trash2,
  Clock,
  Users,
  Image as ImageIcon,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  FolderPlus,
  ExternalLink,
} from 'lucide-react';

interface OpenProjectModalProps {
  onClose: () => void;
  onProjectOpened: (response: OpenProjectResponse) => void;
  theme?: string;
}

export const OpenProjectModal: React.FC<OpenProjectModalProps> = ({
  onClose,
  onProjectOpened,
  theme = 't-dark',
}) => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [noticeMsg, setNoticeMsg] = useState<string | null>(null);
  const [missingProjectId, setMissingProjectId] = useState<string | null>(null);
  const [customPath, setCustomPath] = useState<string>('');
  const [isOpeningCustom, setIsOpeningCustom] = useState<boolean>(false);
  const [isCleaningMissing, setIsCleaningMissing] = useState<boolean>(false);

  const loadProjects = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const list = await apiClient.getRecentProjects();
      setProjects(list);
    } catch (err: any) {
      console.error('Failed to load recent projects:', err);
      setErrorMsg(err.message || 'Failed to load recent projects.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleOpen = async (project: ProjectItem) => {
    setOpeningId(project.id);
    setErrorMsg(null);
    setNoticeMsg(null);
    setMissingProjectId(null);

    try {
      const res = await apiClient.openProject({ project_id: project.id });
      if (res.success) {
        onProjectOpened(res);
        onClose();
      } else {
        setErrorMsg(res.message || 'Failed to open project.');
      }
    } catch (err: any) {
      console.error('Open project failed:', err);
      const detail = err.message || '';
      if (detail.includes('not found') || detail.includes('moved') || detail.includes('404')) {
        setMissingProjectId(project.id);
        setErrorMsg(`Work folder '${project.work_dir}' was moved or deleted on disk.`);
      } else if (detail.includes('scan') || detail.includes('running') || detail.includes('409')) {
        setErrorMsg('A scan is currently running. Please wait or cancel the running scan before opening another project.');
      } else {
        setErrorMsg(detail || 'Could not open project.');
      }
    } finally {
      setOpeningId(null);
    }
  };

  const handleRemove = async (projectId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setRemovingId(projectId);
    setErrorMsg(null);
    try {
      await apiClient.removeProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
      if (missingProjectId === projectId) {
        setMissingProjectId(null);
      }
      setNoticeMsg('Project removed from recent list. No files were deleted.');
      setTimeout(() => setNoticeMsg(null), 4000);
    } catch (err: any) {
      console.error('Failed to remove project:', err);
      setErrorMsg(err.message || 'Failed to remove project.');
    } finally {
      setRemovingId(null);
    }
  };

  const handleClearAllMissing = async () => {
    const missing = projects.filter((p) => !p.exists);
    if (missing.length === 0) return;
    setIsCleaningMissing(true);
    let removedCount = 0;
    for (const p of missing) {
      try {
        await apiClient.removeProject(p.id);
        removedCount++;
      } catch (err) {
        console.error('Failed to remove missing project:', p.id, err);
      }
    }
    setIsCleaningMissing(false);
    setNoticeMsg(`Cleaned up ${removedCount} missing project ${removedCount === 1 ? 'entry' : 'entries'}.`);
    loadProjects();
  };

  const handleOpenCustomPath = async () => {
    if (!customPath.trim()) return;
    setIsOpeningCustom(true);
    setErrorMsg(null);
    try {
      const res = await apiClient.openProject({ work_dir: customPath.trim() });
      if (res.success) {
        onProjectOpened(res);
        onClose();
      } else {
        setErrorMsg(res.message || 'Failed to open folder.');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to open folder.');
    } finally {
      setIsOpeningCustom(false);
    }
  };

  const handleBrowseFolder = async () => {
    if (window.pywebview?.api?.select_folder) {
      try {
        const selected = await window.pywebview.api.select_folder('Select Saved Project or Work Folder');
        if (selected) {
          setCustomPath(selected);
        }
      } catch (err) {
        console.error('Dialog error:', err);
      }
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const missingCount = projects.filter((p) => !p.exists).length;

  const modalContent = (
    <div
      className={`fixed inset-0 flex items-center justify-center p-4 animate-fadeIn ${theme || 't-dark'}`}
      style={{
        zIndex: 100000,
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
      }}
      data-testid="open-project-modal"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
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
              <FolderOpen className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono tracking-tight" style={{ color: 'var(--text)' }}>
                Open Saved Project
              </h2>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                Reopen a past work or export folder without re-scanning
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {missingCount > 0 && (
              <button
                type="button"
                data-testid="clean-all-missing-btn"
                onClick={handleClearAllMissing}
                disabled={isCleaningMissing}
                className="riso-btn-sec text-xs flex items-center gap-1.5"
                style={{
                  height: '32px',
                  padding: '0 10px',
                  borderColor: '#ef4444',
                  color: '#f87171',
                }}
                title="Remove missing test or deleted folders from list (never touches files on disk)"
              >
                {isCleaningMissing ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
                <span>Clean Missing ({missingCount})</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="riso-btn-sec"
              style={{ width: '36px', height: '36px', padding: 0 }}
              title="Close (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Status / Alerts */}
        {errorMsg && (
          <div
            data-testid="project-error-alert"
            className="mx-5 mt-4 p-3 rounded flex items-start gap-2.5 text-xs"
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1.5px solid #ef4444',
              color: '#f87171',
            }}
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-400" />
            <div className="flex-1">
              <p className="font-bold">{errorMsg}</p>
              {missingProjectId && (
                <div className="mt-2">
                  <button
                    data-testid="remove-missing-entry-btn"
                    onClick={() => handleRemove(missingProjectId)}
                    className="riso-btn-sec text-xs"
                    style={{
                      height: '28px',
                      padding: '0 10px',
                      borderColor: '#ef4444',
                      color: '#f87171',
                    }}
                  >
                    <Trash2 className="w-3.5 h-3.5 mr-1" />
                    Remove this entry from recent list
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {noticeMsg && (
          <div
            data-testid="project-notice-alert"
            className="mx-5 mt-4 p-3 rounded flex items-center gap-2.5 text-xs"
            style={{
              background: 'rgba(34, 197, 94, 0.15)',
              border: '1.5px solid #22c55e',
              color: '#4ade80',
            }}
          >
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-green-400" />
            <p className="font-bold">{noticeMsg}</p>
          </div>
        )}

        {/* Projects List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <RefreshCw className="w-6 h-6 animate-spin text-accent mb-2" />
              <p className="text-xs" style={{ color: 'var(--muted)' }}>Loading recent projects...</p>
            </div>
          ) : projects.length === 0 ? (
            <div
              data-testid="no-projects-state"
              className="py-12 flex flex-col items-center justify-center text-center rounded border-2 border-dashed p-6"
              style={{ borderColor: 'var(--line)', background: 'var(--input)' }}
            >
              <Folder className="w-10 h-10 mb-3 opacity-40 text-accent" />
              <p className="font-bold text-sm" style={{ color: 'var(--text)' }}>No recent projects found</p>
              <p className="text-xs mt-1 max-w-sm" style={{ color: 'var(--muted)' }}>
                Completed scans and exports are automatically remembered here. You can also open any existing folder below.
              </p>
            </div>
          ) : (
            projects.map((proj) => {
              const isOpening = openingId === proj.id;
              const isRemoving = removingId === proj.id;
              return (
                <div
                  key={proj.id}
                  data-testid={`project-item-${proj.id}`}
                  className="rounded p-3.5 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 border"
                  style={{
                    background: 'var(--card-bg, var(--panel))',
                    borderColor: 'var(--line)',
                  }}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm truncate" style={{ color: 'var(--text)' }}>
                        {proj.name}
                      </span>
                      {!proj.exists && (
                        <span
                          data-testid="badge-missing"
                          className="px-1.5 py-0.5 rounded text-[10px] font-bold"
                          style={{
                            background: 'rgba(239, 68, 68, 0.2)',
                            color: '#f87171',
                            border: '1px solid #ef4444',
                          }}
                        >
                          Folder Missing
                        </span>
                      )}
                    </div>

                    {proj.source_description && (
                      <p className="text-xs truncate mt-0.5" style={{ color: 'var(--muted)' }} title={proj.source_description}>
                        {proj.source_description}
                      </p>
                    )}

                    <div className="flex items-center gap-3 text-[11px] mt-2 flex-wrap" style={{ color: 'var(--muted)' }}>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(proj.last_opened)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {proj.counts.people} people
                      </span>
                      <span className="flex items-center gap-1">
                        <ImageIcon className="w-3 h-3" />
                        {proj.counts.photos} photos
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                    <button
                      type="button"
                      data-testid={`open-project-btn-${proj.id}`}
                      onClick={() => handleOpen(proj)}
                      disabled={isOpening || isRemoving}
                      className="riso-btn-accent text-xs"
                      style={{ height: '34px', padding: '0 14px' }}
                    >
                      {isOpening ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" />
                          Opening...
                        </>
                      ) : (
                        <>
                          <FolderOpen className="w-3.5 h-3.5 mr-1.5" />
                          Open
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      data-testid={`remove-project-btn-${proj.id}`}
                      onClick={(e) => handleRemove(proj.id, e)}
                      disabled={isOpening || isRemoving}
                      className="riso-btn-sec text-xs"
                      style={{ height: '34px', width: '34px', padding: 0 }}
                      title="Remove from list (never deletes files)"
                    >
                      <Trash2 className="w-3.5 h-3.5 opacity-70" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer: Open folder directly */}
        <div
          className="flex-shrink-0 px-5 py-3 border-t flex flex-col sm:flex-row items-center gap-2"
          style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}
        >
          <div className="flex items-center gap-2 w-full sm:flex-1">
            <input
              type="text"
              data-testid="custom-project-path-input"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              placeholder="Or enter path to work/export folder..."
              className="w-full text-xs px-3 py-2 rounded font-mono"
              style={{
                background: 'var(--input)',
                border: '1.5px solid var(--line)',
                color: 'var(--text)',
              }}
            />
            {typeof window !== 'undefined' && window.pywebview?.api?.select_folder && (
              <button
                type="button"
                onClick={handleBrowseFolder}
                className="riso-btn-sec text-xs flex-shrink-0"
                style={{ height: '34px', padding: '0 10px' }}
                title="Browse folder on disk"
              >
                <FolderPlus className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <button
            type="button"
            data-testid="open-custom-path-btn"
            onClick={handleOpenCustomPath}
            disabled={!customPath.trim() || isOpeningCustom}
            className="riso-btn-sec text-xs w-full sm:w-auto"
            style={{ height: '34px', padding: '0 14px' }}
          >
            {isOpeningCustom ? 'Opening...' : 'Open Folder'}
          </button>
        </div>
      </div>
    </div>
  );

  if (typeof document !== 'undefined' && document.body) {
    return ReactDOM.createPortal(modalContent, document.body);
  }
  return modalContent;
};
