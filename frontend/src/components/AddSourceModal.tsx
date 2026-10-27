import React, { useState } from 'react';
import {
  X,
  Folder,
  FolderArchive,
  Globe,
  ShieldCheck,
  AlertCircle,
  Loader2,
  Plus,
  FolderOpen,
} from 'lucide-react';
import { api } from '../api/client';
import { ScanSourceItem, WhatChangedResponse } from '../types';

export interface AddSourceModalProps {
  onClose: () => void;
  onSourceAdded: (diff: WhatChangedResponse) => void;
  theme?: string;
}

export const AddSourceModal: React.FC<AddSourceModalProps> = ({
  onClose,
  onSourceAdded,
  theme = 't-dark',
}) => {
  const [sourceType, setSourceType] = useState<'local' | 'zip' | 'drive'>('local');
  const [pathOrUrl, setPathOrUrl] = useState('');
  const [label, setLabel] = useState('');
  const [driveApiKey, setDriveApiKey] = useState('');
  const [frozenMode, setFrozenMode] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleBrowseFolder = async () => {
    try {
      if (window.pywebview?.api?.select_folder) {
        const selected = await window.pywebview.api.select_folder('Select photo folder');
        if (selected) {
          setPathOrUrl(selected);
          if (!label) {
            const parts = selected.replace(/\\/g, '/').split('/').filter(Boolean);
            setLabel(parts[parts.length - 1] || 'New Source');
          }
        }
      } else {
        // Fallback to API select-folder dialog if available
        const res = await api.selectFolderDialog('Select photo folder');
        if (res && res.selected) {
          setPathOrUrl(res.selected);
          if (!label) {
            const parts = res.selected.replace(/\\/g, '/').split('/').filter(Boolean);
            setLabel(parts[parts.length - 1] || 'New Source');
          }
        }
      }
    } catch (e: any) {
      console.warn('Folder selection failed:', e);
    }
  };

  const handleBrowseZip = async () => {
    try {
      if (window.pywebview?.api?.select_file) {
        const selected = await window.pywebview.api.select_file('Select photo ZIP archive');
        if (selected) {
          setPathOrUrl(selected);
          if (!label) {
            const parts = selected.replace(/\\/g, '/').split('/').filter(Boolean);
            const fn = parts[parts.length - 1] || 'Photos.zip';
            setLabel(fn.replace(/\.zip$/i, ''));
          }
        }
      } else {
        const res = await api.selectFileDialog('Select photo ZIP archive');
        if (res && res.selected) {
          setPathOrUrl(res.selected);
          if (!label) {
            const parts = res.selected.replace(/\\/g, '/').split('/').filter(Boolean);
            const fn = parts[parts.length - 1] || 'Photos.zip';
            setLabel(fn.replace(/\.zip$/i, ''));
          }
        }
      }
    } catch (e: any) {
      console.warn('ZIP selection failed:', e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanPath = pathOrUrl.trim();
    if (!cleanPath) {
      setErrorMsg('Please enter a folder path, ZIP path, or Google Drive URL.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    const sourceItem: ScanSourceItem = {
      id: `src_${Date.now()}`,
      kind: sourceType,
      type: sourceType,
      path_or_url: cleanPath,
      label: label.trim() || cleanPath.replace(/\\/g, '/').split('/').filter(Boolean).pop() || 'Additional Source',
    };

    try {
      const diff = await api.addProjectSource(
        sourceItem,
        driveApiKey.trim() || undefined,
        frozenMode
      );
      onSourceAdded(diff);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to add source incrementally.');
      setIsSubmitting(false);
    }
  };

  return (
    <div
      id="add-source-modal-overlay"
      data-testid="add-source-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-source-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose();
      }}
    >
      <div
        id="add-source-modal-card"
        data-testid="add-source-modal-card"
        className={`w-full max-w-lg rounded-xl overflow-hidden shadow-2xl ${theme}`}
        style={{
          background: 'var(--card-bg)',
          border: '2px solid var(--line)',
          color: 'var(--text)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: '1.5px solid var(--line)', background: 'var(--bg)' }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'var(--accent)', color: 'var(--bg)' }}
            >
              <Plus className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h2 id="add-source-modal-title" className="text-base font-bold font-mono tracking-tight">
                Add Source to Project
              </h2>
              <p className="text-xs text-[var(--muted)]">
                Scan additional photos into this project incrementally
              </p>
            </div>
          </div>
          <button
            id="btn-close-add-source-modal"
            data-testid="btn-close-add-source-modal"
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--line)] transition-colors"
            aria-label="Close add source modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {errorMsg && (
            <div
              id="add-source-error-alert"
              data-testid="add-source-error-alert"
              className="p-3 rounded-lg flex items-start gap-2.5 text-xs font-mono"
              style={{
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1.5px solid #ef4444',
                color: '#f87171',
              }}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Source Type Selector */}
          <div>
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)] mb-2">
              Source Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                id="btn-source-type-local"
                data-testid="btn-source-type-local"
                disabled={isSubmitting}
                onClick={() => setSourceType('local')}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border text-xs font-mono transition-all ${
                  sourceType === 'local'
                    ? 'border-[var(--accent)] bg-[var(--accent)]/10 font-bold'
                    : 'border-[var(--line)] bg-[var(--bg)] opacity-75 hover:opacity-100'
                }`}
              >
                <Folder className="w-5 h-5" style={{ color: sourceType === 'local' ? 'var(--accent)' : 'inherit' }} />
                <span>Local Folder</span>
              </button>

              <button
                type="button"
                id="btn-source-type-zip"
                data-testid="btn-source-type-zip"
                disabled={isSubmitting}
                onClick={() => setSourceType('zip')}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border text-xs font-mono transition-all ${
                  sourceType === 'zip'
                    ? 'border-[var(--accent)] bg-[var(--accent)]/10 font-bold'
                    : 'border-[var(--line)] bg-[var(--bg)] opacity-75 hover:opacity-100'
                }`}
              >
                <FolderArchive className="w-5 h-5" style={{ color: sourceType === 'zip' ? 'var(--accent)' : 'inherit' }} />
                <span>ZIP Archive</span>
              </button>

              <button
                type="button"
                id="btn-source-type-drive"
                data-testid="btn-source-type-drive"
                disabled={isSubmitting}
                onClick={() => setSourceType('drive')}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border text-xs font-mono transition-all ${
                  sourceType === 'drive'
                    ? 'border-[var(--accent)] bg-[var(--accent)]/10 font-bold'
                    : 'border-[var(--line)] bg-[var(--bg)] opacity-75 hover:opacity-100'
                }`}
              >
                <Globe className="w-5 h-5" style={{ color: sourceType === 'drive' ? 'var(--accent)' : 'inherit' }} />
                <span>Google Drive</span>
              </button>
            </div>
          </div>

          {/* Path or URL Input */}
          <div>
            <label
              htmlFor="input-source-path"
              className="block text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)] mb-1.5"
            >
              {sourceType === 'drive' ? 'Google Drive Folder Link' : sourceType === 'zip' ? 'ZIP Archive Path' : 'Folder Path'}
            </label>
            <div className="flex items-center gap-2">
              <input
                id="input-source-path"
                data-testid="input-source-path"
                type="text"
                disabled={isSubmitting}
                value={pathOrUrl}
                onChange={(e) => setPathOrUrl(e.target.value)}
                placeholder={
                  sourceType === 'drive'
                    ? 'https://drive.google.com/drive/folders/...'
                    : sourceType === 'zip'
                    ? 'C:\\Photos\\Event-Day2.zip'
                    : 'C:\\Photos\\Day2'
                }
                className="flex-1 px-3 py-2 rounded-lg text-xs font-mono bg-[var(--bg)] border border-[var(--line)] focus:outline-none focus:border-[var(--accent)]"
              />
              {sourceType === 'local' && (
                <button
                  type="button"
                  id="btn-browse-source-folder"
                  data-testid="btn-browse-source-folder"
                  disabled={isSubmitting}
                  onClick={handleBrowseFolder}
                  className="px-3 py-2 rounded-lg text-xs font-mono flex items-center gap-1.5 border border-[var(--line)] bg-[var(--bg)] hover:bg-[var(--line)] transition-colors"
                >
                  <FolderOpen className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span>Browse</span>
                </button>
              )}
              {sourceType === 'zip' && (
                <button
                  type="button"
                  id="btn-browse-source-zip"
                  data-testid="btn-browse-source-zip"
                  disabled={isSubmitting}
                  onClick={handleBrowseZip}
                  className="px-3 py-2 rounded-lg text-xs font-mono flex items-center gap-1.5 border border-[var(--line)] bg-[var(--bg)] hover:bg-[var(--line)] transition-colors"
                >
                  <FolderOpen className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span>Browse</span>
                </button>
              )}
            </div>
          </div>

          {/* Optional Label */}
          <div>
            <label
              htmlFor="input-source-label"
              className="block text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)] mb-1.5"
            >
              Source Label (Optional)
            </label>
            <input
              id="input-source-label"
              data-testid="input-source-label"
              type="text"
              disabled={isSubmitting}
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. Day 2 / Stage B / Camera 2"
              className="w-full px-3 py-2 rounded-lg text-xs font-mono bg-[var(--bg)] border border-[var(--line)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {/* Optional Drive API Key */}
          {sourceType === 'drive' && (
            <div>
              <label
                htmlFor="input-drive-api-key"
                className="block text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)] mb-1.5"
              >
                Google Drive API Key (Optional if already configured)
              </label>
              <input
                id="input-drive-api-key"
                data-testid="input-drive-api-key"
                type="password"
                disabled={isSubmitting}
                value={driveApiKey}
                onChange={(e) => setDriveApiKey(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full px-3 py-2 rounded-lg text-xs font-mono bg-[var(--bg)] border border-[var(--line)] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
          )}

          {/* Frozen Mode Option Banner */}
          <div
            id="frozen-mode-container"
            data-testid="frozen-mode-container"
            className="p-3.5 rounded-lg border border-[var(--line)] bg-[var(--bg)] flex items-start gap-3"
          >
            <input
              id="checkbox-frozen-mode"
              data-testid="checkbox-frozen-mode"
              type="checkbox"
              disabled={isSubmitting}
              checked={frozenMode}
              onChange={(e) => setFrozenMode(e.target.checked)}
              className="mt-1 w-4 h-4 rounded text-[var(--accent)] focus:ring-[var(--accent)] cursor-pointer"
            />
            <label htmlFor="checkbox-frozen-mode" className="text-xs space-y-1 cursor-pointer">
              <div className="flex items-center gap-1.5 font-bold font-mono text-[var(--text)]">
                <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Frozen Mode (Recommended)</span>
              </div>
              <p className="text-[var(--muted)] leading-relaxed">
                Existing people clusters and manual edits are 100% frozen. New photos attach to existing people or create new clusters. Guarantees 0 changes to pre-existing face memberships.
              </p>
            </label>
          </div>

          {/* Modal Actions */}
          <div
            className="flex items-center justify-end gap-3 pt-4"
            style={{ borderTop: '1.5px solid var(--line)' }}
          >
            <button
              id="btn-cancel-add-source"
              data-testid="btn-cancel-add-source"
              type="button"
              disabled={isSubmitting}
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-mono font-bold border border-[var(--line)] hover:bg-[var(--line)] transition-colors"
            >
              Cancel
            </button>

            <button
              id="btn-submit-add-source"
              data-testid="btn-submit-add-source"
              type="submit"
              disabled={isSubmitting || !pathOrUrl.trim()}
              className="px-5 py-2 rounded-lg text-xs font-mono font-bold flex items-center gap-2 transition-all disabled:opacity-50"
              style={{
                background: 'var(--accent)',
                color: 'var(--bg)',
              }}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing New Photos...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 stroke-[2.5]" />
                  <span>Scan & Add Source</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
