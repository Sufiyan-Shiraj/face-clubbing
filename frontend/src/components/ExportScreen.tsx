import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../api/client';
import { BrowseFolderResult } from '../types';
import {
  Download,
  Folder,
  FolderPlus,
  ArrowUp,
  RefreshCw,
  Monitor,
  Copy,
  Check,
  Search,
  ChevronRight,
  FileCode,
  HardDrive,
  Moon,
  Sun,
  Compass,
  Palette,
} from 'lucide-react';
import { MascotSticker } from './MascotSticker';

interface ExportScreenProps {
  initialTitle?: string;
  initialSubtitle?: string;
  peopleCount?: number;
  photosCount?: number;
  onRefreshStats?: () => void;
  onExportSuccess?: () => void;
  theme?: string;
}

export const ExportScreen: React.FC<ExportScreenProps> = ({
  initialTitle,
  initialSubtitle = 'Auto-sorted face albums and photo gallery',
  peopleCount = 0,
  photosCount = 0,
  onRefreshStats,
  onExportSuccess,
  theme = 't-dark',
}) => {
  // Determine automatic drive folder name
  const autoDriveName = useMemo(() => {
    if (initialTitle && initialTitle !== 'CatLog Gallery' && initialTitle !== 'Face Clubbing Gallery' && initialTitle !== 'Event Gallery') {
      return initialTitle;
    }
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('photosorter-verified-folder-name');
      if (stored && stored.trim()) return stored.trim();
    }
    return null;
  }, [initialTitle]);

  const [outputDir, setOutputDir] = useState('export');
  const [title, setTitle] = useState(autoDriveName || initialTitle || 'CatLog Gallery');
  const [subtitle, setSubtitle] = useState(initialSubtitle);
  const [includeMaybe, setIncludeMaybe] = useState(false);
  const [viewerTheme, setViewerTheme] = useState<'t-dark' | 't-paper' | 't-navy'>(
    theme === 't-paper' || theme === 't-navy' ? theme : 't-dark'
  );
  const [isExporting, setIsExporting] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // File Explorer State
  const [browseData, setBrowseData] = useState<BrowseFolderResult | null>(null);
  const [isBrowsingLoading, setIsBrowsingLoading] = useState(false);
  const [explorerFilter, setExplorerFilter] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [browseError, setBrowseError] = useState<string | null>(null);
  const [isNativeDialogOpen, setIsNativeDialogOpen] = useState(false);

  const getNestedPath = (basePath: string) => {
    const folderTitle =
      autoDriveName ||
      (title && title !== 'CatLog Gallery' && title !== 'Face Clubbing Gallery' && title !== 'Event Gallery' ? title : null);
    if (!folderTitle) return basePath;
    const safeName = folderTitle.replace(/[\\/*?:"<>|]/g, '').trim();
    if (!safeName) return basePath;

    const normalized = basePath.replace(/[\\/]+$/, '');
    const lastPart = normalized.split(/[\\/]/).pop();
    if (lastPart && lastPart.toLowerCase() === safeName.toLowerCase()) {
      return normalized;
    }
    return `${normalized}/${safeName}`;
  };

  // Fetch initial settings & folder list
  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        const baseOut = s.output_dir || 'export';
        const nestedOut = getNestedPath(baseOut);
        setOutputDir(nestedOut);
        loadFolder(baseOut);
        if (s.event_title && !autoDriveName && s.event_title !== 'Event Gallery') {
          setTitle(s.event_title);
        }
        if (s.event_subtitle) {
          setSubtitle(s.event_subtitle);
        }
        if (typeof s.include_maybe === 'boolean') {
          setIncludeMaybe(s.include_maybe);
        }
      })
      .catch(() => {
        const nestedOut = getNestedPath('export');
        setOutputDir(nestedOut);
        loadFolder('export');
      });
  }, [autoDriveName]);

  const loadFolder = async (path?: string) => {
    setIsBrowsingLoading(true);
    setBrowseError(null);
    try {
      const data = await api.browseFolder(path);
      setBrowseData(data);
    } catch (err: any) {
      setBrowseError(err.message || 'Failed to inspect filesystem');
    } finally {
      setIsBrowsingLoading(false);
    }
  };

  const [exportResult, setExportResult] = useState<{
    success: boolean;
    output_dir: string;
    files_exported: string[];
    people_count: number;
    photos_count: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    try {
      const targetDir = getNestedPath(outputDir.trim() || 'export');
      const res = await api.exportBundle({
        output_dir: targetDir,
        title: title.trim(),
        subtitle: subtitle.trim(),
        include_maybe: includeMaybe,
        theme: viewerTheme,
      });
      setExportResult(res);
      if (onRefreshStats) onRefreshStats();
      if (onExportSuccess) onExportSuccess();
    } catch (err: any) {
      setError(err.message || 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleSelectFolder = (path: string) => {
    const target = getNestedPath(path);
    setOutputDir(target);
    loadFolder(path);
  };

  const handleOpenSystemDialog = async () => {
    setIsNativeDialogOpen(true);
    setBrowseError(null);
    try {
      // 1. Check if running inside desktop pywebview container
      if ((window as any).pywebview?.api?.select_folder) {
        const selected = await (window as any).pywebview.api.select_folder('Select Public Export Directory');
        if (selected && selected.trim()) {
          const target = getNestedPath(selected.trim());
          setOutputDir(target);
          loadFolder(selected.trim());
        }
        return;
      }

      // 2. Otherwise trigger backend foreground dialog
      const targetDir = outputDir.trim() || browseData?.current_path || undefined;
      const res = await api.openFolderDialog(targetDir);
      if (res && res.selected && !res.cancelled) {
        const target = getNestedPath(res.selected);
        setOutputDir(target);
        loadFolder(res.selected);
      }
    } catch (err: any) {
      console.error('System dialog error:', err);
      setBrowseError(err.message || 'System folder dialog cancelled or failed');
    } finally {
      setIsNativeDialogOpen(false);
    }
  };

  const handleCreateNewFolder = async () => {
    if (!newFolderName.trim() || !browseData?.current_path) return;
    try {
      const res = await api.createFolder(browseData.current_path, newFolderName.trim());
      setBrowseData(res);
      setOutputDir(res.current_path);
      setNewFolderName('');
      setIsCreatingFolder(false);
    } catch (err: any) {
      setBrowseError(err.message || 'Failed to create folder');
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Filter subdirectories
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
        segs.push({ label: p, fullPath: p + '\\' });
      } else {
        acc = acc ? (acc.endsWith('/') ? acc + p : acc + '/' + p) : '/' + p;
        const osPath = acc.replace(/\//g, '\\');
        segs.push({ label: p, fullPath: osPath });
      }
    });
    return segs;
  }, [browseData?.current_path]);

  return (
    <div className="export-dashboard animate-fadeIn select-none w-full px-2 sm:px-4 py-2 space-y-8">
      {/* Top Header Row with Actions */}
      <div className="flex flex-wrap items-center justify-between gap-6 pb-6 border-b-2 border-[var(--line)]">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-xl bg-[var(--input)] border-2 border-[var(--panel-border)] shadow-[4px_4px_0px_var(--line)] flex items-center justify-center text-[var(--accent)] flex-shrink-0">
            <Download className="w-9 h-9" />
          </div>
          <div>
            <div className="flex items-center gap-4 flex-wrap">
              <h2 className="text-3xl md:text-4xl font-black tracking-tight text-[var(--text)] uppercase font-mono">
                Export Static Web Bundle
              </h2>
              <span className="settings-badge accent text-sm md:text-base px-3.5 py-1 font-bold">
                STANDALONE VIEWER
              </span>
            </div>
            <p className="text-base md:text-lg text-[var(--muted)] font-mono mt-2">
              Generate a completely self-contained photo gallery with zero backend or server dependencies.
            </p>
          </div>
        </div>

        {/* Top Header Controls: Single clean refresh button */}
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => loadFolder(outputDir)}
            className="btn sm flex items-center gap-2.5"
            style={{ height: '48px', padding: '0 24px', fontSize: '16px', fontWeight: 700 }}
            title="Refresh directory view"
          >
            <RefreshCw className={`w-4 h-4 text-[var(--muted)] ${isBrowsingLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-5 rounded-lg bg-red-950/90 border-2 border-red-700 text-red-100 text-lg flex items-center gap-4 animate-fadeIn">
          <span className="font-mono font-bold text-sm bg-red-800 text-white px-3 py-1 rounded">ERROR</span>
          <span className="font-semibold">{error}</span>
        </div>
      )}

      {/* Clean, Neat 2-Column Main Workspace using full available width */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Output Directory Explorer Window (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="explorer-window">
            {/* Titlebar Chrome */}
            <div className="explorer-titlebar px-6 py-4">
              <div className="flex items-center gap-3.5">
                <div className="explorer-window-dots">
                  <span className="explorer-dot red"></span>
                  <span className="explorer-dot amber"></span>
                  <span className="explorer-dot green"></span>
                </div>
                <div className="flex items-center gap-3 font-mono text-lg md:text-xl font-bold text-[var(--text)] ml-2">
                  <HardDrive className="w-5 h-5 text-[var(--accent)]" />
                  <span>OUTPUT DESTINATION EXPLORER</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  id="btn-system-dialog"
                  data-testid="btn-system-dialog"
                  onClick={handleOpenSystemDialog}
                  disabled={isNativeDialogOpen}
                  className={`btn sm transition-all flex items-center gap-2.5 ${
                    isNativeDialogOpen ? 'border-[var(--accent)] text-[var(--accent)] bg-[var(--input)]' : ''
                  }`}
                  style={{ height: '42px', padding: '0 22px', fontSize: '15px', fontWeight: 800 }}
                  title="Open Windows File Explorer Dialog"
                >
                  {isNativeDialogOpen ? (
                    <>
                      <RefreshCw className="w-4 h-4 text-[var(--accent)] animate-spin" />
                      <span>Opening Dialog...</span>
                    </>
                  ) : (
                    <>
                      <Monitor className="w-4 h-4 text-[var(--accent)]" />
                      <span>System Dialog...</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Active Dialog Indicator Banner */}
            {isNativeDialogOpen && (
              <div className="p-4 bg-amber-950/70 border-b border-amber-700/80 text-amber-200 text-base flex items-center gap-3 font-mono animate-pulse">
                <RefreshCw className="w-5 h-5 animate-spin text-amber-400 flex-shrink-0" />
                <span>Native Windows folder dialog is open. Please select your folder in the system window.</span>
              </div>
            )}

            {/* Browse Error Alert */}
            {browseError && (
              <div className="p-4 bg-red-950/80 border-b border-red-700 text-red-200 text-base flex items-center justify-between gap-3 font-mono">
                <span>{browseError}</span>
                <button
                  type="button"
                  onClick={() => setBrowseError(null)}
                  className="text-red-300 hover:text-white font-bold text-lg px-2"
                >
                  ×
                </button>
              </div>
            )}

            {/* Breadcrumb Path Bar & Up Navigation */}
            <div className="p-4 sm:p-5 bg-[var(--panel)] border-b border-[var(--panel-border)] flex flex-wrap items-center justify-between gap-4 text-base font-mono">
              <div className="flex items-center gap-3 flex-1 min-w-[240px] overflow-x-auto py-1">
                <button
                  type="button"
                  onClick={() => browseData?.parent_path && handleSelectFolder(browseData.parent_path)}
                  disabled={!browseData?.parent_path}
                  className={`p-3 rounded-md border border-[var(--panel-border)] bg-[var(--input)] transition-all flex items-center justify-center ${
                    browseData?.parent_path
                      ? 'hover:border-[var(--accent)] text-[var(--text)] cursor-pointer'
                      : 'opacity-40 cursor-not-allowed text-[var(--muted)]'
                  }`}
                  title="Go up one folder"
                >
                  <ArrowUp className="w-5 h-5" />
                </button>

                <div className="flex items-center gap-2 flex-wrap">
                  {breadcrumbSegments.map((seg, idx) => (
                    <React.Fragment key={seg.fullPath}>
                      <button
                        type="button"
                        onClick={() => handleSelectFolder(seg.fullPath)}
                        className={`px-3.5 py-2 rounded-md transition-colors text-base md:text-lg ${
                          idx === breadcrumbSegments.length - 1
                            ? 'font-black text-[var(--accent)] bg-[var(--input)] border border-[var(--line)] shadow-[2px_2px_0px_var(--line)]'
                            : 'text-[var(--text)] hover:bg-[var(--input)] font-bold'
                        }`}
                      >
                        {seg.label}
                      </button>
                      {idx < breadcrumbSegments.length - 1 && (
                        <ChevronRight className="w-4 h-4 text-[var(--muted)] flex-shrink-0" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Actions: New Folder */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreatingFolder(!isCreatingFolder)}
                  className="btn sm flex items-center gap-2"
                  style={{ height: '42px', padding: '0 18px', fontSize: '15px', fontWeight: 700 }}
                >
                  <FolderPlus className="w-4 h-4 text-[var(--accent)]" />
                  <span>New Folder</span>
                </button>
              </div>
            </div>

            {/* Quick Access Shortcuts Pill Bar */}
            {browseData?.shortcuts && browseData.shortcuts.length > 0 && (
              <div className="px-5 py-3.5 bg-[var(--input)] border-b border-[var(--panel-border)] flex items-center gap-3 overflow-x-auto text-base font-mono">
                <span className="text-[var(--muted)] uppercase font-bold text-xs md:text-sm flex-shrink-0 mr-1">QUICK:</span>
                {browseData.shortcuts.map((sc) => (
                  <button
                    key={sc.label}
                    type="button"
                    onClick={() => handleSelectFolder(sc.path)}
                    className={`px-4 py-2 rounded-md border text-sm md:text-base whitespace-nowrap transition-all ${
                      outputDir === sc.path || outputDir === sc.label
                        ? 'border-[var(--accent)] bg-[var(--accent)] text-[var(--on-accent)] font-bold shadow-[2px_2px_0px_var(--line)]'
                        : 'border-[var(--line)] bg-[var(--panel)] text-[var(--text)] hover:border-[var(--accent)] font-semibold'
                    }`}
                  >
                    {sc.label}
                  </button>
                ))}
              </div>
            )}

            {/* Inline New Folder Form */}
            {isCreatingFolder && (
              <div className="p-4 bg-[var(--input)] border-b-2 border-[var(--accent)] flex items-center gap-3 animate-fadeIn">
                <FolderPlus className="w-5 h-5 text-[var(--accent)] flex-shrink-0" />
                <input
                  type="text"
                  placeholder="New folder name..."
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateNewFolder()}
                  autoFocus
                  className="flex-1 px-4 py-2.5 bg-[var(--panel)] border border-[var(--panel-border)] rounded text-base font-mono text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                />
                <button
                  type="button"
                  onClick={handleCreateNewFolder}
                  className="btn pri sm"
                  style={{ height: '42px', padding: '0 20px', fontSize: '15px', fontWeight: 700 }}
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreatingFolder(false);
                    setNewFolderName('');
                  }}
                  className="btn sm"
                  style={{ height: '42px', padding: '0 16px', fontSize: '15px' }}
                >
                  Cancel
                </button>
              </div>
            )}

            {/* Subdirectories Explorer Body */}
            <div className="p-5 max-h-[320px] overflow-y-auto space-y-2.5 font-mono">
              {/* Search / Filter Box */}
              <div className="relative mb-3">
                <Search className="w-5 h-5 text-[var(--muted)] absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter subfolders..."
                  value={explorerFilter}
                  onChange={(e) => setExplorerFilter(e.target.value)}
                  className="w-full pl-12 pr-4 py-2.5 bg-[var(--input)] border border-[var(--panel-border)] rounded-md text-base md:text-lg text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                />
              </div>

              {filteredSubdirs.length === 0 ? (
                <div className="py-12 text-center text-[var(--muted)] font-mono text-base md:text-lg">
                  {isBrowsingLoading
                    ? 'Loading folders...'
                    : explorerFilter
                    ? 'No matching subfolders found.'
                    : 'This folder has no subfolders. You can export directly here or create a new folder.'}
                </div>
              ) : (
                filteredSubdirs.map((dir) => {
                  const isSelected = outputDir === dir.path || outputDir === dir.name;
                  return (
                    <div
                      key={dir.path}
                      onClick={() => handleSelectFolder(dir.path)}
                      className={`explorer-folder-item flex items-center justify-between p-4 rounded-md cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-[var(--accent)] text-[var(--on-accent)] font-bold shadow-[3px_3px_0px_var(--line)]'
                          : 'bg-[var(--panel)] hover:bg-[var(--input)] text-[var(--text)] border border-[var(--line)]'
                      }`}
                    >
                      <div className="flex items-center gap-4 truncate">
                        <Folder className={`w-7 h-7 flex-shrink-0 ${isSelected ? 'text-[var(--on-accent)]' : 'text-[var(--accent)]'}`} />
                        <span className="font-bold text-lg md:text-xl truncate">{dir.name}</span>
                      </div>

                      <div className="flex items-center gap-3 text-sm flex-shrink-0">
                        <span
                          className={`px-4 py-1.5 rounded-md text-sm font-bold uppercase transition-all ${
                            isSelected
                              ? 'bg-[var(--text)] text-[var(--bg)]'
                              : 'bg-[var(--input)] text-[var(--text)] border border-[var(--line)]'
                          }`}
                        >
                          {isSelected ? 'Active' : 'Select'}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer Active Path Input & Target Confirmation */}
            <div className="p-5 bg-[var(--input)] border-t-2 border-[var(--panel-border)] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <span className="text-sm uppercase font-bold text-[var(--muted)] block font-mono mb-1.5">
                  Active Export Destination Path
                </span>
                <input
                  id="export-output-dir-input"
                  data-testid="export-output-dir-input"
                  type="text"
                  value={outputDir}
                  onChange={(e) => setOutputDir(e.target.value)}
                  onBlur={() => loadFolder(outputDir)}
                  placeholder="export"
                  className="w-full px-4 py-3 bg-[var(--panel)] border-2 border-[var(--panel-border)] rounded-md text-base md:text-lg font-mono font-bold text-[var(--text)] focus:outline-none focus:border-[var(--accent)] shadow-[2px_2px_0px_var(--line)]"
                />
              </div>

              <div className="flex items-center gap-3 flex-shrink-0 sm:pt-6">
                <button
                  type="button"
                  onClick={() => handleSelectFolder(browseData?.current_path || outputDir)}
                  className="btn pri sm flex items-center gap-2"
                  style={{ height: '46px', padding: '0 24px', fontSize: '15px', fontWeight: 800 }}
                >
                  <Check className="w-5 h-5" />
                  <span>Confirm Target</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Gallery Configuration & Clean Export Action (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="settings-panel p-6 sm:p-8 space-y-6">
            <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-5">
              <div className="flex items-center gap-3.5">
                <FileCode className="w-7 h-7 text-[var(--accent)]" />
                <h3 className="text-xl md:text-2xl font-black uppercase font-mono text-[var(--text)]">
                  Gallery Configuration
                </h3>
              </div>
              {autoDriveName && (
                <span className="settings-badge accent text-sm px-3.5 py-1 font-bold" title="Title synchronized with your Google Drive folder">
                  DRIVE SYNCED
                </span>
              )}
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label htmlFor="export-title-input" className="text-base md:text-lg font-bold uppercase text-[var(--text)] font-mono">
                    Gallery Title
                  </label>
                  {autoDriveName && (
                    <button
                      type="button"
                      onClick={() => setTitle(autoDriveName)}
                      className="text-sm text-[var(--accent)] hover:underline flex items-center gap-1 font-mono font-bold"
                    >
                      <span>Reset to Drive Name</span>
                    </button>
                  )}
                </div>
                <input
                  id="export-title-input"
                  data-testid="export-title-input"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Gallery Title..."
                  className="w-full px-4 py-3.5 bg-[var(--input)] border-2 border-[var(--panel-border)] rounded-md text-lg md:text-xl text-[var(--text)] font-sans font-bold focus:outline-none focus:border-[var(--accent)] shadow-[3px_3px_0px_var(--line)]"
                />
              </div>

              <div>
                <label htmlFor="export-subtitle-input" className="block text-base md:text-lg font-bold uppercase text-[var(--text)] font-mono mb-2">
                  Gallery Subtitle / Description
                </label>
                <input
                  id="export-subtitle-input"
                  data-testid="export-subtitle-input"
                  type="text"
                  value={subtitle}
                  onChange={(e) => setSubtitle(e.target.value)}
                  placeholder="Auto-sorted face albums and photo gallery"
                  className="w-full px-4 py-3.5 bg-[var(--input)] border-2 border-[var(--panel-border)] rounded-md text-base md:text-lg text-[var(--text)] font-sans focus:outline-none focus:border-[var(--accent)] shadow-[3px_3px_0px_var(--line)]"
                />
              </div>

              {/* Theme Picker for Exported Gallery */}
              <div className="pt-2">
                <label className="block text-base md:text-lg font-bold uppercase text-[var(--text)] font-mono mb-2 flex items-center gap-2">
                  <Palette className="w-5 h-5 text-[var(--accent)]" />
                  <span>Default Viewer Theme</span>
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 't-dark', name: 'Dark', subtitle: 'Tactile Charcoal', icon: Moon, dot: '#141211', border: '#fa7175' },
                    { id: 't-paper', name: 'Paper', subtitle: 'Risograph Cream', icon: Sun, dot: '#efe8db', border: '#e5781a' },
                    { id: 't-navy', name: 'Navy', subtitle: 'Midnight Deep', icon: Compass, dot: '#1a3350', border: '#f28f24' },
                  ].map((t) => {
                    const isSelected = viewerTheme === t.id;
                    const IconComp = t.icon;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setViewerTheme(t.id as any)}
                        className={`p-3.5 rounded-lg border-2 text-left transition-all relative ${
                          isSelected
                            ? 'border-[var(--accent)] bg-[var(--input)] shadow-[3px_3px_0px_var(--line)]'
                            : 'border-[var(--panel-border)] bg-[var(--panel)] hover:border-[var(--line)]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <IconComp className={`w-4 h-4 ${isSelected ? 'text-[var(--accent)]' : 'text-[var(--muted)]'}`} />
                            <span className="font-bold text-base font-mono text-[var(--text)]">{t.name}</span>
                          </div>
                          <span
                            className="w-3.5 h-3.5 rounded-full border border-black/30 flex-shrink-0"
                            style={{ backgroundColor: t.dot }}
                          />
                        </div>
                        <span className="text-xs text-[var(--muted)] font-mono block truncate">{t.subtitle}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-2">
                <label
                  htmlFor="export-include-maybe-toggle"
                  className="flex items-start gap-4 p-4 rounded-lg bg-[var(--input)] border border-[var(--panel-border)] cursor-pointer hover:border-[var(--accent)] transition-all"
                >
                  <input
                    id="export-include-maybe-toggle"
                    data-testid="export-include-maybe-toggle"
                    type="checkbox"
                    checked={includeMaybe}
                    onChange={(e) => setIncludeMaybe(e.target.checked)}
                    className="mt-1 w-5 h-5 rounded border-2 border-[var(--panel-border)] text-[var(--accent)] focus:ring-[var(--accent)]"
                  />
                  <div>
                    <span className="text-base md:text-lg font-bold text-[var(--text)] block">
                      Include "Possible Matches" (Distance 0.50 – 0.65)
                    </span>
                    <span className="text-sm md:text-base text-[var(--muted)] block mt-1.5 font-sans leading-relaxed">
                      Exports borderline ambiguous faces alongside confident matches so viewers can inspect edge cases.
                    </span>
                  </div>
                </label>
              </div>

              {/* Big, Clear Primary Action Button */}
              <div className="pt-4">
                <button
                  id="export-bundle-btn"
                  data-testid="export-bundle-btn"
                  disabled={isExporting}
                  onClick={handleExport}
                  className="btn pri w-full flex items-center justify-center gap-3.5 shadow-[4px_4px_0px_var(--line)]"
                  style={{ height: '60px', fontSize: '19px', fontWeight: 900 }}
                >
                  <Download className={`w-6 h-6 ${isExporting ? 'animate-bounce' : ''}`} />
                  <span>{isExporting ? 'Generating Bundle...' : 'Export Public Bundle Now'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Export Result Success Card */}
      {exportResult && (
        <div
          id="export-success-summary"
          data-testid="export-success-summary"
          className="settings-panel p-7 sm:p-9 border-2 border-emerald-500 bg-emerald-950/20 space-y-6 animate-scaleUp"
        >
          <div className="flex items-center justify-between flex-wrap gap-4 border-b border-emerald-800/60 pb-5">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl bg-[var(--input)] border-2 border-emerald-500/50 flex items-center justify-center p-1.5 flex-shrink-0 shadow-[2px_2px_0px_var(--line)]">
                <MascotSticker pose={7} theme={theme} className="w-full h-full object-contain" />
              </div>
              <div>
                <h3 className="text-2xl md:text-3xl font-black text-white font-mono uppercase">
                  Static Web Bundle Exported Successfully
                </h3>
                <p className="text-base md:text-lg text-neutral-300 font-mono mt-1">
                  Destination: <span className="font-bold text-emerald-400">{exportResult.output_dir}</span>
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => copyToClipboard(exportResult.output_dir, 'dir')}
              className="btn sm flex items-center gap-2"
              style={{ height: '46px', fontSize: '15px', fontWeight: 700 }}
            >
              {copiedKey === 'dir' ? <Check className="w-5 h-5 text-emerald-400" /> : <Copy className="w-5 h-5" />}
              <span>{copiedKey === 'dir' ? 'Path Copied!' : 'Copy Absolute Path'}</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-5 pt-2 font-mono">
            <div className="p-5 rounded-lg bg-[var(--input)] border border-[var(--panel-border)] text-center">
              <span className="text-sm md:text-base text-[var(--muted)] font-bold">People Clustered</span>
              <p id="export-stat-people" data-testid="export-stat-people" className="text-3xl md:text-4xl font-black text-[var(--text)] mt-2">
                {exportResult.people_count}
              </p>
            </div>
            <div className="p-5 rounded-lg bg-[var(--input)] border border-[var(--panel-border)] text-center">
              <span className="text-sm md:text-base text-[var(--muted)] font-bold">Photos Included</span>
              <p id="export-stat-photos" data-testid="export-stat-photos" className="text-3xl md:text-4xl font-black text-[var(--text)] mt-2">
                {exportResult.photos_count}
              </p>
            </div>
            <div className="p-5 rounded-lg bg-[var(--input)] border border-[var(--panel-border)] text-center">
              <span className="text-sm md:text-base text-[var(--muted)] font-bold">Exported Files</span>
              <p id="export-stat-files" data-testid="export-stat-files" className="text-3xl md:text-4xl font-black text-[var(--text)] mt-2">
                {exportResult.files_exported.length}
              </p>
            </div>
            <div className="p-5 rounded-lg bg-[var(--input)] border border-[var(--panel-border)] text-center">
              <span className="text-sm md:text-base text-[var(--muted)] font-bold">Privacy Audit</span>
              <p className="text-base md:text-lg font-black text-emerald-400 mt-3">Zero Private Leaks</p>
            </div>
          </div>

          <div className="p-5 rounded-lg bg-[var(--input)] border border-[var(--panel-border)]">
            <p className="text-sm md:text-base text-[var(--muted)] font-mono mb-3 font-bold uppercase">
              Exported Bundle Manifest:
            </p>
            <div className="flex flex-wrap gap-2.5">
              {exportResult.files_exported.map((f) => (
                <span
                  key={f}
                  className="px-4 py-2 rounded-md bg-[var(--panel)] text-[var(--text)] text-sm md:text-base font-mono border border-[var(--line)] shadow-[1px_1px_0px_var(--line)]"
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
