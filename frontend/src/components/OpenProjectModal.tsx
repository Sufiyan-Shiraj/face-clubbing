import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactDOM from 'react-dom';
import { ProjectItem, OpenProjectResponse, BrowseFolderResult } from '../types';
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
  Monitor,
  ArrowUp,
  ChevronRight,
  Search,
  Check,
  ExternalLink,
} from 'lucide-react';

interface OpenProjectModalProps {
  onClose: () => void;
  onProjectOpened: (response: OpenProjectResponse) => void;
  theme?: string;
  hasUnexportedWork?: boolean;
  onNavigateToExport?: () => void;
}

export const OpenProjectModal: React.FC<OpenProjectModalProps> = ({
  onClose,
  onProjectOpened,
  theme = 't-dark',
  hasUnexportedWork = false,
  onNavigateToExport,
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

  // Unexported work confirmation guard state
  const [pendingAction, setPendingAction] = useState<
    | { type: 'project'; project: ProjectItem }
    | { type: 'custom'; path: string }
    | null
  >(null);

  // In-modal Filesystem Explorer state
  const [isExplorerOpen, setIsExplorerOpen] = useState<boolean>(false);
  const [browseData, setBrowseData] = useState<BrowseFolderResult | null>(null);
  const [isBrowsingLoading, setIsBrowsingLoading] = useState<boolean>(false);
  const [explorerFilter, setExplorerFilter] = useState<string>('');
  const [browseError, setBrowseError] = useState<string | null>(null);
  const [isBrowsingSystem, setIsBrowsingSystem] = useState<boolean>(false);

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

  const executeOpenCustomPath = async (targetPath: string) => {
    if (!targetPath.trim()) return;
    setIsOpeningCustom(true);
    setErrorMsg(null);
    try {
      const res = await apiClient.openProject({ work_dir: targetPath.trim() });
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

  const handleOpenCustomPath = async () => {
    handleRequestOpenCustomPath();
  };

  const handleRequestOpenProject = (project: ProjectItem) => {
    if (hasUnexportedWork) {
      setPendingAction({ type: 'project', project });
    } else {
      handleOpen(project);
    }
  };

  const handleRequestOpenCustomPath = (pathToOpen?: string) => {
    const target = (pathToOpen || customPath).trim();
    if (!target) return;
    if (hasUnexportedWork) {
      setPendingAction({ type: 'custom', path: target });
    } else {
      executeOpenCustomPath(target);
    }
  };

  const handleConfirmDiscardAndOpen = () => {
    if (!pendingAction) return;
    const action = pendingAction;
    setPendingAction(null);
    if (action.type === 'project') {
      handleOpen(action.project);
    } else {
      executeOpenCustomPath(action.path);
    }
  };

  const loadBrowseFolder = async (path?: string) => {
    setIsBrowsingLoading(true);
    setBrowseError(null);
    try {
      const data = await apiClient.browseFolder(path);
      setBrowseData(data);
    } catch (err: any) {
      setBrowseError(err.message || 'Failed to inspect filesystem');
    } finally {
      setIsBrowsingLoading(false);
    }
  };

  const handleToggleExplorer = () => {
    if (!isExplorerOpen) {
      setIsExplorerOpen(true);
      loadBrowseFolder(customPath.trim() || undefined);
    } else {
      setIsExplorerOpen(false);
    }
  };

  const handleSelectFolder = (path: string) => {
    setCustomPath(path);
    loadBrowseFolder(path);
  };

  const handleOpenSystemDialog = async () => {
    setIsBrowsingSystem(true);
    setErrorMsg(null);
    try {
      // 1. Pywebview native container dialog
      if ((window as any).pywebview?.api?.select_folder) {
        const selected = await (window as any).pywebview.api.select_folder('Select Saved Project or Work Folder');
        if (selected && selected.trim()) {
          setCustomPath(selected.trim());
          if (isExplorerOpen) {
            loadBrowseFolder(selected.trim());
          }
        }
        return;
      }

      // 2. Web browser native OS dialog via backend endpoint
      const targetDir = customPath.trim() || browseData?.current_path || undefined;
      const res = await apiClient.openFolderDialog(targetDir);
      if (res && res.selected && !res.cancelled) {
        setCustomPath(res.selected);
        if (isExplorerOpen) {
          loadBrowseFolder(res.selected);
        }
      }
    } catch (err: any) {
      console.error('System dialog error:', err);
      setErrorMsg(err.message || 'System folder dialog cancelled or failed');
    } finally {
      setIsBrowsingSystem(false);
    }
  };

  // Filter subdirectories in explorer
  const filteredSubdirs = useMemo(() => {
    if (!browseData?.directories) return [];
    if (!explorerFilter.trim()) return browseData.directories;
    const term = explorerFilter.toLowerCase();
    return browseData.directories.filter((d) => d.name.toLowerCase().includes(term));
  }, [browseData?.directories, explorerFilter]);

  // Compute breadcrumbs from current path
  const breadcrumbSegments = useMemo(() => {
    if (!browseData?.current_path) return [];
    const normalized = browseData.current_path.replace(/\\/g, '/');
    const parts = normalized.split('/').filter(Boolean);
    const segs: { label: string; fullPath: string }[] = [];
    let acc = '';

    parts.forEach((p, idx) => {
      if (idx === 0 && browseData.current_path.includes(':')) {
        acc = p + '/';
      } else {
        acc = acc ? (acc.endsWith('/') ? acc + p : acc + '/' + p) : p;
      }
      segs.push({
        label: p,
        fullPath: acc,
      });
    });
    return segs;
  }, [browseData?.current_path]);

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
                      onClick={() => handleRequestOpenProject(proj)}
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

        {/* Expandable Filesystem Explorer (like the Export page) */}
        {isExplorerOpen && (
          <div
            data-testid="in-modal-explorer"
            className="flex-shrink-0 border-t p-4 max-h-56 overflow-y-auto space-y-3"
            style={{
              background: 'var(--input)',
              borderColor: 'var(--line)',
            }}
          >
            {/* Explorer Header / Breadcrumbs & Shortcuts */}
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-1.5 flex-1 min-w-[200px] overflow-x-auto">
                <button
                  type="button"
                  data-testid="explorer-up-btn"
                  onClick={() => browseData?.parent_path && handleSelectFolder(browseData.parent_path)}
                  disabled={!browseData?.parent_path}
                  className="p-1.5 rounded border riso-btn-sec"
                  style={{ height: '28px', width: '28px', padding: 0 }}
                  title="Go up one folder"
                >
                  <ArrowUp className="w-3.5 h-3.5 mx-auto" />
                </button>

                <div className="flex items-center gap-1 text-[11px] font-mono flex-wrap">
                  {breadcrumbSegments.map((seg, idx) => (
                    <React.Fragment key={seg.fullPath}>
                      <button
                        type="button"
                        onClick={() => handleSelectFolder(seg.fullPath)}
                        className={`px-1.5 py-0.5 rounded transition-colors ${
                          idx === breadcrumbSegments.length - 1
                            ? 'font-bold text-[var(--accent)] border border-[var(--line)] bg-[var(--panel)]'
                            : 'hover:bg-[var(--panel)]'
                        }`}
                      >
                        {seg.label}
                      </button>
                      {idx < breadcrumbSegments.length - 1 && (
                        <ChevronRight className="w-3 h-3 opacity-40 flex-shrink-0" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Quick Access Shortcuts */}
              {browseData?.shortcuts && browseData.shortcuts.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  {browseData.shortcuts.map((sc) => (
                    <button
                      key={sc.path}
                      type="button"
                      onClick={() => handleSelectFolder(sc.path)}
                      className="px-2 py-0.5 rounded text-[10px] riso-btn-sec"
                      style={{ height: '24px' }}
                      title={sc.path}
                    >
                      {sc.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Filter Input */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 opacity-50" />
                <input
                  type="text"
                  value={explorerFilter}
                  onChange={(e) => setExplorerFilter(e.target.value)}
                  placeholder="Filter subfolders..."
                  className="w-full text-xs pl-8 pr-3 py-1 rounded font-mono"
                  style={{
                    background: 'var(--panel)',
                    border: '1px solid var(--line)',
                    color: 'var(--text)',
                  }}
                />
              </div>
              {browseData?.current_path && (
                <button
                  type="button"
                  data-testid="use-current-folder-btn"
                  onClick={() => setCustomPath(browseData.current_path)}
                  className="riso-btn-accent text-[11px] flex-shrink-0"
                  style={{ height: '28px', padding: '0 10px' }}
                >
                  <Check className="w-3 h-3 mr-1" />
                  Use Current Folder
                </button>
              )}
            </div>

            {/* Subdirectories List */}
            {isBrowsingLoading ? (
              <div className="py-6 flex items-center justify-center text-xs text-[var(--muted)]">
                <RefreshCw className="w-4 h-4 animate-spin mr-2 text-accent" />
                Scanning folder...
              </div>
            ) : filteredSubdirs.length === 0 ? (
              <p className="text-[11px] text-center py-4 text-[var(--muted)]">No subfolders found</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-36 overflow-y-auto">
                {filteredSubdirs.map((d) => (
                  <div
                    key={d.path}
                    className="flex items-center justify-between p-2 rounded border text-xs cursor-pointer hover:border-[var(--accent)] transition-all"
                    style={{
                      background: 'var(--panel)',
                      borderColor: customPath === d.path ? 'var(--accent)' : 'var(--line)',
                    }}
                    onClick={() => handleSelectFolder(d.path)}
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <Folder className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                      <span className="truncate font-mono text-[11px]" title={d.name}>
                        {d.name}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setCustomPath(d.path);
                      }}
                      className="text-[10px] px-1.5 py-0.5 rounded riso-btn-sec flex-shrink-0 ml-1"
                      style={{ height: '20px' }}
                      title="Select this path"
                    >
                      Select
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Footer: Open folder directly */}
        <div
          className="flex-shrink-0 px-5 py-3 border-t flex flex-col sm:flex-row items-center gap-2"
          style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}
        >
          <div className="flex items-center gap-1.5 w-full sm:flex-1">
            <input
              type="text"
              data-testid="custom-project-path-input"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              placeholder="Or select/enter path to work or export folder..."
              className="w-full text-xs px-3 py-2 rounded font-mono"
              style={{
                background: 'var(--input)',
                border: '1.5px solid var(--line)',
                color: 'var(--text)',
              }}
            />

            {/* System Dialog button (Works in Desktop pywebview AND Web browser!) */}
            <button
              type="button"
              id="btn-system-dialog"
              data-testid="btn-system-dialog"
              onClick={handleOpenSystemDialog}
              disabled={isBrowsingSystem}
              className="riso-btn-sec text-xs flex-shrink-0 flex items-center gap-1"
              style={{ height: '34px', padding: '0 10px' }}
              title="Open native Windows folder dialog"
            >
              {isBrowsingSystem ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Monitor className="w-3.5 h-3.5 text-accent" />
              )}
              <span className="hidden sm:inline">Browse...</span>
            </button>

            {/* In-Modal Filesystem Explorer toggle */}
            <button
              type="button"
              data-testid="toggle-explorer-btn"
              onClick={handleToggleExplorer}
              className={`riso-btn-sec text-xs flex-shrink-0 flex items-center gap-1 ${
                isExplorerOpen ? 'border-[var(--accent)] text-[var(--accent)]' : ''
              }`}
              style={{ height: '34px', padding: '0 10px' }}
              title="Toggle in-modal folder explorer"
            >
              <FolderPlus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Explorer</span>
            </button>
          </div>

          <button
            type="button"
            data-testid="open-custom-path-btn"
            onClick={() => handleRequestOpenCustomPath()}
            disabled={!customPath.trim() || isOpeningCustom}
            className="riso-btn-sec text-xs w-full sm:w-auto"
            style={{ height: '34px', padding: '0 14px' }}
          >
            {isOpeningCustom ? 'Opening...' : 'Open Folder'}
          </button>
        </div>

        {/* Unexported Work Guard Confirmation Prompt Modal */}
        {pendingAction && (
          <div
            data-testid="unexported-guard-modal"
            className="absolute inset-0 z-50 flex items-center justify-center p-6 animate-fadeIn"
            style={{
              background: 'rgba(0, 0, 0, 0.75)',
              backdropFilter: 'blur(4px)',
            }}
          >
            <div
              className="p-6 rounded max-w-md w-full border-2 space-y-4 shadow-2xl"
              style={{
                background: 'var(--bg)',
                borderColor: 'var(--accent)',
                color: 'var(--text)',
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded flex items-center justify-center flex-shrink-0"
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1.5px solid var(--accent)',
                    color: 'var(--accent)',
                  }}
                >
                  <AlertTriangle className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h3 className="font-bold text-sm tracking-tight" style={{ color: 'var(--text)' }}>
                    Unexported Work in Current Project
                  </h3>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    Active project has unsaved or unexported albums
                  </p>
                </div>
              </div>

              <p className="text-xs leading-relaxed" style={{ color: 'var(--text)' }}>
                You have active sorted people and edits in this session that haven't been exported yet. Loading another project will replace your current workspace.
              </p>

              <div className="flex flex-col gap-2 pt-2">
                <button
                  type="button"
                  data-testid="export-first-btn"
                  onClick={() => {
                    setPendingAction(null);
                    if (onNavigateToExport) {
                      onNavigateToExport();
                    } else {
                      onClose();
                    }
                  }}
                  className="riso-btn-accent text-xs flex items-center justify-center gap-2"
                  style={{ height: '36px' }}
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Export First (Recommended)</span>
                </button>

                <button
                  type="button"
                  data-testid="discard-and-open-btn"
                  onClick={handleConfirmDiscardAndOpen}
                  className="riso-btn-sec text-xs flex items-center justify-center gap-2"
                  style={{
                    height: '36px',
                    borderColor: '#ef4444',
                    color: '#f87171',
                  }}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Discard & Open Project</span>
                </button>

                <button
                  type="button"
                  data-testid="cancel-guard-btn"
                  onClick={() => setPendingAction(null)}
                  className="riso-btn-sec text-xs"
                  style={{ height: '34px' }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  if (typeof document !== 'undefined' && document.body) {
    return ReactDOM.createPortal(modalContent, document.body);
  }
  return modalContent;
};
