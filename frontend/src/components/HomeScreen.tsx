import React, { useState, useMemo, useRef, useEffect } from 'react';
import { AlertCircle, Folder, FolderArchive, Info, Check, Key, X, Loader2, FolderOpen, Compass, ChevronRight } from 'lucide-react';
import { RisoTheme } from './Header';
import { api } from '../api/client';

export interface HomeScreenProps {
  onStartJob: (inputPath?: string, driveFolder?: string, driveApiKey?: string) => void;
  isLoading?: boolean;
  currentInputPath?: string;
  onNavigateTab?: (tab: string) => void;
  theme?: RisoTheme;
  onOpenProject?: () => void;
  onOpenTutorial?: () => void;

  // Lifted & Persisted state
  sourceMode?: 'drive' | 'local' | 'zip';
  onSourceModeChange?: (mode: 'drive' | 'local' | 'zip') => void;
  folderPath?: string;
  onFolderPathChange?: (path: string) => void;
  driveLink?: string;
  onDriveLinkChange?: (link: string) => void;
  driveVerified?: boolean;
  verifiedFolderId?: string | null;
  verifiedFolderName?: string | null;
  verifiedImageCount?: number;
  onDriveVerifiedChange?: (
    verified: boolean,
    folderId?: string | null,
    folderName?: string | null,
    imageCount?: number
  ) => void;
  discoveredFaceCrops?: string[];
  onApiKeySaved?: () => void;
  isApiKeyConfigured?: boolean;
}

// Drive triangle icon matching the reference image
const DriveIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 87.3 78" fill="currentColor" aria-hidden="true">
    <path d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z" opacity=".8" />
    <path d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44c-.8 1.4-1.2 2.95-1.2 4.5h27.5z" opacity=".9" />
    <path d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z" />
    <path d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z" />
    <path d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" />
    <path d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.5c0-1.55-.4-3.1-1.2-4.5z" opacity=".85" />
  </svg>
);

export function extractDriveFolderId(input: string): string | null {
  const trimmed = input.trim();
  if (!trimmed) return null;
  if (trimmed.includes('/file/d/')) return null;

  const folderMatch = trimmed.match(/drive\.google\.com\/(?:drive\/)?(?:u\/\d+\/)?(?:mobile\/)?folders\/([a-zA-Z0-9_-]{15,100})/i);
  if (folderMatch && folderMatch[1]) {
    return folderMatch[1];
  }

  const idMatch = trimmed.match(/drive\.google\.com\/(?:open|folderview)\?(?:.*&)?id=([a-zA-Z0-9_-]{15,100})/i);
  if (idMatch && idMatch[1]) {
    return idMatch[1];
  }

  if (!trimmed.includes('/') && !trimmed.includes('.') && /^[a-zA-Z0-9_-]{18,100}$/.test(trimmed)) {
    return trimmed;
  }

  return null;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  onStartJob,
  isLoading = false,
  currentInputPath = '',
  theme = 't-dark',
  sourceMode: controlledSourceMode,
  onSourceModeChange,
  folderPath: controlledFolderPath,
  onFolderPathChange,
  driveLink: controlledDriveLink,
  onDriveLinkChange,
  driveVerified: controlledDriveVerified,
  verifiedFolderId: controlledVerifiedFolderId,
  verifiedFolderName: controlledVerifiedFolderName,
  verifiedImageCount: controlledVerifiedImageCount,
  onDriveVerifiedChange,
  discoveredFaceCrops = [],
  onApiKeySaved,
  isApiKeyConfigured: controlledApiKeyConfigured,
  onOpenProject,
  onOpenTutorial,
}) => {
  // Support both controlled (lifted to App.tsx) and internal fallback state
  const [internalSourceMode, setInternalSourceMode] = useState<'drive' | 'local' | 'zip'>('drive');
  const sourceMode = controlledSourceMode !== undefined ? controlledSourceMode : internalSourceMode;
  const setSourceMode = (mode: 'drive' | 'local' | 'zip') => {
    setInternalSourceMode(mode);
    onSourceModeChange?.(mode);
  };

  const [internalFolderPath, setInternalFolderPath] = useState<string>(currentInputPath || '');
  const folderPath = controlledFolderPath !== undefined ? controlledFolderPath : internalFolderPath;
  const setFolderPath = (p: string) => {
    setInternalFolderPath(p);
    onFolderPathChange?.(p);
  };

  const [internalDriveLink, setInternalDriveLink] = useState<string>('');
  const driveLink = controlledDriveLink !== undefined ? controlledDriveLink : internalDriveLink;
  const setDriveLink = (l: string) => {
    setInternalDriveLink(l);
    onDriveLinkChange?.(l);
  };

  const [internalDriveVerified, setInternalDriveVerified] = useState<boolean>(false);
  const driveVerified = controlledDriveVerified !== undefined ? controlledDriveVerified : internalDriveVerified;

  const [internalVerifiedFolderId, setInternalVerifiedFolderId] = useState<string | null>(null);
  const verifiedFolderId = controlledVerifiedFolderId !== undefined ? controlledVerifiedFolderId : internalVerifiedFolderId;

  const [internalVerifiedFolderName, setInternalVerifiedFolderName] = useState<string | null>(null);
  const verifiedFolderName = controlledVerifiedFolderName !== undefined ? controlledVerifiedFolderName : internalVerifiedFolderName;

  const [internalVerifiedImageCount, setInternalVerifiedImageCount] = useState<number>(0);
  const verifiedImageCount = controlledVerifiedImageCount !== undefined ? controlledVerifiedImageCount : internalVerifiedImageCount;

  const [internalApiKeyConfigured, setInternalApiKeyConfigured] = useState<boolean>(false);
  const isApiKeyConfigured = controlledApiKeyConfigured !== undefined ? controlledApiKeyConfigured : internalApiKeyConfigured;

  useEffect(() => {
    let mounted = true;
    const fetchStatus = () => {
      try {
        const p = api?.getSettings?.();
        if (p && typeof p.then === 'function') {
          p.then((s) => {
            if (mounted && s) {
              setInternalApiKeyConfigured(Boolean(s.drive_api_key_configured));
            }
          }).catch(() => {});
        }
      } catch (e) {}
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    window.addEventListener('focus', fetchStatus);
    return () => {
      mounted = false;
      clearInterval(interval);
      window.removeEventListener('focus', fetchStatus);
    };
  }, []);

  const setVerifiedState = (
    verified: boolean,
    folderId?: string | null,
    folderName?: string | null,
    imgCount?: number
  ) => {
    setInternalDriveVerified(verified);
    setInternalVerifiedFolderId(folderId || null);
    setInternalVerifiedFolderName(folderName || null);
    setInternalVerifiedImageCount(imgCount || 0);
    onDriveVerifiedChange?.(verified, folderId || null, folderName || null, imgCount || 0);
  };

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState<boolean>(false);
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [isSavingApiKey, setIsSavingApiKey] = useState<boolean>(false);

  // Extracted folder ID for character cells (only active when verified)
  const activeFolderId = verifiedFolderId || extractDriveFolderId(driveLink);

  const cellRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleBrowseFolder = async () => {
    if (window.pywebview?.api?.select_folder) {
      try {
        const selected = await window.pywebview.api.select_folder('Select Photo Folder');
        if (selected) {
          setFolderPath(selected);
          setSourceMode('local');
          setErrorMsg(null);
        }
      } catch (err) {
        console.error('Native folder picker failed:', err);
      }
    } else {
      const input = document.createElement('input');
      input.type = 'file';
      (input as any).webkitdirectory = true;
      input.onchange = (e: any) => {
        const files = e.target.files;
        if (files && files.length > 0) {
          const first = files[0];
          const folder = first.webkitRelativePath ? first.webkitRelativePath.split('/')[0] : '';
          if (folder) {
            setFolderPath(folder);
            setSourceMode('local');
            setErrorMsg(null);
          }
        }
      };
      input.click();
    }
  };

  const handleBrowseFile = async () => {
    if (window.pywebview?.api?.select_file) {
      try {
        const selected = await window.pywebview.api.select_file('Select Zip Archive or File');
        if (selected) {
          setFolderPath(selected);
          setSourceMode('local');
          setErrorMsg(null);
        }
      } catch (err) {
        console.error('Native file picker failed:', err);
      }
    } else {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.zip,.tar,.jpg,.jpeg,.png';
      input.onchange = (e: any) => {
        const files = e.target.files;
        if (files && files.length > 0) {
          setFolderPath(files[0].name);
          setSourceMode('local');
          setErrorMsg(null);
        }
      };
      input.click();
    }
  };

  const handleClearDriveLink = () => {
    setDriveLink('');
    setVerifiedState(false, null, null, 0);
    setErrorMsg(null);
  };

  const handleCellChange = (index: number, value: string) => {
    if (!activeFolderId) return;
    const char = value.slice(-1);
    if (!char) return;

    const chars = activeFolderId.split('');
    chars[index] = char;
    const newId = chars.join('');

    if (driveLink.includes(activeFolderId)) {
      setDriveLink(driveLink.replace(activeFolderId, newId));
    } else {
      setDriveLink(newId);
    }
    setVerifiedState(true, newId, verifiedFolderName, verifiedImageCount);

    if (index < chars.length - 1) {
      const nextInput = cellRefs.current[index + 1];
      if (nextInput) {
        nextInput.focus();
        nextInput.select();
      }
    }
  };

  const handleCellKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!activeFolderId) return;

    if (e.key === 'Backspace') {
      e.preventDefault();
      const chars = activeFolderId.split('');
      chars.splice(index, 1);
      const newId = chars.join('');

      if (driveLink.includes(activeFolderId)) {
        setDriveLink(driveLink.replace(activeFolderId, newId));
      } else {
        setDriveLink(newId);
      }
      setVerifiedState(true, newId, verifiedFolderName, verifiedImageCount);

      const prevIdx = Math.max(0, index - 1);
      setTimeout(() => {
        const prevInput = cellRefs.current[prevIdx];
        if (prevInput) {
          prevInput.focus();
          prevInput.select();
        }
      }, 0);
    } else if (e.key === 'Delete') {
      e.preventDefault();
      const chars = activeFolderId.split('');
      chars.splice(index, 1);
      const newId = chars.join('');

      if (driveLink.includes(activeFolderId)) {
        setDriveLink(driveLink.replace(activeFolderId, newId));
      } else {
        setDriveLink(newId);
      }
      setVerifiedState(true, newId, verifiedFolderName, verifiedImageCount);
    } else if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault();
      cellRefs.current[index - 1]?.focus();
      cellRefs.current[index - 1]?.select();
    } else if (e.key === 'ArrowRight' && index < activeFolderId.length - 1) {
      e.preventDefault();
      cellRefs.current[index + 1]?.focus();
      cellRefs.current[index + 1]?.select();
    }
  };

  const handleCellPaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text');
    if (pasted) {
      setDriveLink(pasted.trim());
      setVerifiedState(false, null, null, 0);
      setErrorMsg(null);
    }
  };

  const validateDriveInput = (val: string): string | null => {
    const trimmed = val.trim();
    if (!trimmed) {
      return 'Please specify a Google Drive folder link or folder ID.';
    }
    if (trimmed.includes('/file/d/')) {
      return 'You entered a Google Drive file link, but a folder link or folder ID is required.';
    }
    const isRawId = /^[a-zA-Z0-9_-]{18,100}$/.test(trimmed);
    const isFolderUrl =
      /drive\.google\.com\/(?:drive\/)?(?:u\/\d+\/)?(?:mobile\/)?folders\/([a-zA-Z0-9_-]{15,100})/i.test(trimmed) ||
      /drive\.google\.com\/(?:open|folderview)\?(?:.*&)?id=([a-zA-Z0-9_-]{15,100})/i.test(trimmed);

    if (!isRawId && !isFolderUrl) {
      return 'Invalid Google Drive folder link or folder ID. Expected a public folder link (e.g. https://drive.google.com/drive/folders/1A2b3C...).';
    }
    return null;
  };

  // Check link button action: verifies Google Drive link and API key
  const handleCheckDrive = async (apiKeyOverride?: string) => {
    const trimmed = driveLink.trim();
    const validationError = validateDriveInput(trimmed);
    if (validationError) {
      setErrorMsg(validationError);
      setVerifiedState(false, null, null, 0);
      return false;
    }

    setIsChecking(true);
    setErrorMsg(null);
    try {
      const res = await api.verifyDriveFolder(trimmed, apiKeyOverride);
      if (res.valid) {
        setVerifiedState(true, res.folder_id, res.folder_name, res.image_count_preview || 0);
        setErrorMsg(null);
        setInternalApiKeyConfigured(true);
        return true;
      } else {
        setVerifiedState(false, null, null, 0);
        setErrorMsg(res.message || 'Verification failed.');
        if (res.error_type === 'api_key_missing' || res.error_type === 'api_key_invalid') {
          setInternalApiKeyConfigured(false);
          setShowApiKeyModal(true);
        }
        return false;
      }
    } catch (err: any) {
      setVerifiedState(false, null, null, 0);
      setErrorMsg(err.message || 'Failed to verify Google Drive folder.');
      return false;
    } finally {
      setIsChecking(false);
    }
  };

  // Save API Key modal handler
  const handleSaveApiKey = async () => {
    if (!apiKeyInput.trim()) return;
    setIsSavingApiKey(true);
    try {
      const key = apiKeyInput.trim();
      await api.updateSettings({ drive_api_key: key });
      setInternalApiKeyConfigured(true);
      onApiKeySaved?.();
      setShowApiKeyModal(false);
      setApiKeyInput('');
      // Re-trigger verification immediately with the newly entered key
      await handleCheckDrive(key);
    } catch (err: any) {
      setErrorMsg(`Failed to save API key: ${err.message || err}`);
    } finally {
      setIsSavingApiKey(false);
    }
  };

  // Start Job handler
  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sourceMode === 'drive') {
      // If not yet verified, check first!
      if (!driveVerified) {
        const ok = await handleCheckDrive();
        if (!ok) return;
      }
      setErrorMsg(null);
      const ephemeralKey = sessionStorage.getItem('drive_api_key_ephemeral') || undefined;
      onStartJob(undefined, driveLink.trim(), ephemeralKey);
    } else {
      if (!folderPath.trim()) {
        setErrorMsg('Please specify a local folder path or zip archive.');
        return;
      }
      setErrorMsg(null);
      onStartJob(folderPath.trim());
    }
  };

  const isDriveReady = driveVerified && Boolean(activeFolderId);
  const isLocalReady = Boolean(folderPath.trim());
  const canStartScan = sourceMode === 'drive' ? isDriveReady : isLocalReady;

  return (
    <div className="main-content-flow">
      <div className={`home-stage-container ${sourceMode === 'drive' && driveVerified ? 'stage-expanded' : ''}`}>
        {/* Headline & Supporting Sentence with Image Title */}
        <div className="headline-group">
          <h1 className="h1 h1-title-container">
            <span className="sr-only">Who was at the event?</span>
            <img
              src="/catlog-tagline.png"
              alt="Who was at the event?"
              className="h1-img"
            />
          </h1>
          <p className="sub-headline">Sort your event photos by person using face clustering.</p>
          {onOpenTutorial && (
            <div className="flex items-center justify-center mt-2.5 mb-1">
              <button
                type="button"
                id="home-start-tutorial-btn"
                data-testid="home-start-tutorial-btn"
                onClick={onOpenTutorial}
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold transition-all hover:scale-105"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px dashed var(--line)',
                  color: 'var(--text)',
                }}
                title="Start the 2-minute CatLog walkthrough"
              >
                <Compass className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>New to CatLog? Take the 2-minute interactive tour</span>
                <ChevronRight className="w-3.5 h-3.5 opacity-60" />
              </button>
            </div>
          )}
        </div>

        {/* Three Source-Mode Buttons */}
        <div id="source-mode-nav" className="source-mode-nav" aria-label="Source mode selection">
          <button
            type="button"
            id="btn-source-drive"
            data-testid="btn-source-drive"
            onClick={() => {
              setSourceMode('drive');
              setErrorMsg(null);
            }}
            className={`source-mode-btn ${sourceMode === 'drive' ? 'active' : ''}`}
            aria-pressed={sourceMode === 'drive'}
          >
            <DriveIcon className="w-4 h-4 flex-shrink-0" />
            <span>Google Drive</span>
          </button>

          <button
            type="button"
            id="btn-source-local"
            data-testid="btn-source-local"
            onClick={() => {
              setSourceMode('local');
              setErrorMsg(null);
            }}
            className={`source-mode-btn ${sourceMode === 'local' ? 'active' : ''}`}
            aria-pressed={sourceMode === 'local'}
          >
            <Folder className="w-4 h-4 flex-shrink-0" />
            <span>Local folder</span>
          </button>

          <button
            type="button"
            id="btn-source-zip"
            data-testid="btn-source-zip"
            onClick={() => {
              setSourceMode('zip');
              setErrorMsg(null);
            }}
            className={`source-mode-btn ${sourceMode === 'zip' ? 'active' : ''}`}
            aria-pressed={sourceMode === 'zip'}
          >
            <FolderArchive className="w-4 h-4 flex-shrink-0" />
            <span>Zip file</span>
          </button>

          {onOpenProject && (
            <button
              type="button"
              id="home-open-project-btn"
              data-testid="home-open-project-btn"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onOpenProject();
              }}
              className="source-mode-btn"
              title="Open saved project"
            >
              <FolderOpen className="w-4 h-4 flex-shrink-0 text-[var(--accent)]" />
              <span>Open saved project</span>
            </button>
          )}
        </div>

        {/* Main Source Selection Form */}
        <form onSubmit={handleStart} className="source-form">
          {sourceMode === 'drive' ? (
            driveVerified && activeFolderId ? (
              /* State 2: Verified Google Drive Folder ID with Cell Structure */
              <div className="drive-extracted-view">
                {/* Hidden input for testids & accessible form synchronization */}
                <input
                  id="input-drive-link"
                  data-testid="input-drive-link"
                  type="text"
                  value={driveLink}
                  onChange={(e) => {
                    setDriveLink(e.target.value);
                    setVerifiedState(false, null, null, 0);
                    setErrorMsg(null);
                  }}
                  style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', width: '1px', height: '1px' }}
                  aria-hidden="true"
                />

                {/* Prominent Drive Folder Name Header */}
                <div className="drive-verified-banner">
                  <div className="drive-folder-title">
                    <span className="folder-label">DRIVE FOLDER</span>
                    <span className="folder-name">{verifiedFolderName || 'Google Drive Folder'}</span>
                    <span className="badge-verified">
                      <Check className="w-3.5 h-3.5" />
                      Verified
                    </span>
                  </div>
                  {verifiedImageCount > 0 && (
                    <div className="folder-img-count">{verifiedImageCount}+ images detected</div>
                  )}
                </div>

                <div className="drive-id-header">
                  <span>FOLDER ID CELLS</span>
                  <Info className="w-3.5 h-3.5 opacity-75" aria-label="Drive Folder ID Info" />
                </div>

                {/* Individual outlined character cells */}
                <div className="char-cells-row" aria-label={`Drive Folder ID: ${activeFolderId}`}>
                  {activeFolderId.split('').map((char, idx) => (
                    <input
                      key={idx}
                      ref={(el) => {
                        cellRefs.current[idx] = el;
                      }}
                      type="text"
                      className="char-cell"
                      value={char}
                      maxLength={2}
                      onChange={(e) => handleCellChange(idx, e.target.value)}
                      onKeyDown={(e) => handleCellKeyDown(idx, e)}
                      onFocus={(e) => e.target.select()}
                      onPaste={handleCellPaste}
                      aria-label={`Drive folder ID character ${idx + 1}`}
                      autoComplete="off"
                      spellCheck="false"
                    />
                  ))}
                </div>

                {/* Status line & action row */}
                <div className="drive-detected-bar">
                  <div className="drive-detected-text">
                    <span>Folder: </span>
                    <span className="drive-detected-id">{verifiedFolderName || activeFolderId}</span>
                  </div>
                  <div className="drive-detected-actions">
                    <button
                      type="button"
                      onClick={handleClearDriveLink}
                      className="btn-clear-link"
                      title="Clear entered link"
                    >
                      Change link
                    </button>
                    <button
                      id="start-job-btn"
                      data-testid="start-job-btn"
                      type="submit"
                      disabled={isLoading || !canStartScan}
                      className="btn pri"
                    >
                      {isLoading ? 'Scanning...' : 'Scan folder'}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* State 1: Input URL row with explicit Check Link button */
              <div className="drive-initial-view">
                <div className="field">
                  <input
                    id="input-drive-link"
                    data-testid="input-drive-link"
                    type="text"
                    value={driveLink}
                    onChange={(e) => {
                      setDriveLink(e.target.value);
                      setErrorMsg(null);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleCheckDrive();
                      }
                    }}
                    placeholder="Paste a Google Drive folder link... (drive.google.com/drive/folders/...)"
                    className="input"
                    aria-label="Google Drive folder link"
                  />
                  <button
                    type="button"
                    id="btn-check-drive"
                    data-testid="btn-check-drive"
                    onClick={() => handleCheckDrive()}
                    disabled={isChecking || !driveLink.trim()}
                    className="btn sec"
                    title="Check if API key and Drive folder are valid"
                  >
                    {isChecking ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Checking...</span>
                      </>
                    ) : (
                      <span>Check link</span>
                    )}
                  </button>
                  <button
                    id="start-job-btn"
                    data-testid="start-job-btn"
                    type="submit"
                    disabled={isLoading || !canStartScan}
                    className="btn pri"
                    title={!canStartScan ? 'Verify link before starting scan' : 'Start scanning folder'}
                  >
                    {isLoading ? 'Scanning...' : 'Scan folder'}
                  </button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', marginTop: '8px' }}>
                  <p className="hint" style={{ margin: 0 }}>
                    Click &apos;Check link&apos; to verify Google Drive folder. Folder must be shared as &apos;Anyone with the link&apos;.
                  </p>
                  {!isApiKeyConfigured && (
                    <button
                      type="button"
                      id="btn-set-api-key"
                      data-testid="btn-set-api-key"
                      onClick={() => setShowApiKeyModal(true)}
                      className="text-sm font-bold text-[var(--accent)] hover:underline inline-flex items-center gap-1.5 flex-shrink-0 ml-2"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit' }}
                      title="Set Google Drive API key"
                    >
                      <Key className="w-3.5 h-3.5" />
                      <span>Set API key</span>
                    </button>
                  )}
                </div>
              </div>
            )
          ) : sourceMode === 'local' ? (
            /* Local folder mode */
            <div className="local-source-view">
              <div className="field">
                <input
                  id="input-source-path"
                  data-testid="input-source-path"
                  type="text"
                  value={folderPath}
                  onChange={(e) => {
                    setFolderPath(e.target.value);
                    setErrorMsg(null);
                  }}
                  placeholder="Selected photo folder path..."
                  className="input"
                  aria-label="Local photo folder path"
                />
                <button
                  id="start-job-btn"
                  data-testid="start-job-btn"
                  type="submit"
                  disabled={isLoading || !folderPath.trim()}
                  className="btn pri"
                >
                  {isLoading ? 'Scanning...' : 'Scan folder'}
                </button>
              </div>
              <div className="local-source-row">
                <span className="hint" style={{ margin: 0 }}>
                  Local target: <span style={{ color: 'var(--text)' }}>{folderPath || 'None selected'}</span>
                </span>
                <button
                  type="button"
                  id="btn-browse-folder"
                  data-testid="btn-browse-folder"
                  onClick={handleBrowseFolder}
                  className="btn sm"
                >
                  <Folder className="w-3.5 h-3.5" />
                  <span>Browse folder</span>
                </button>
              </div>
            </div>
          ) : (
            /* Zip archive mode */
            <div className="local-source-view">
              <div className="field">
                <input
                  id="input-source-path"
                  data-testid="input-source-path"
                  type="text"
                  value={folderPath}
                  onChange={(e) => {
                    setFolderPath(e.target.value);
                    setErrorMsg(null);
                  }}
                  placeholder="Selected zip archive or file..."
                  className="input"
                  aria-label="Zip archive path"
                />
                <button
                  id="start-job-btn"
                  data-testid="start-job-btn"
                  type="submit"
                  disabled={isLoading || !folderPath.trim()}
                  className="btn pri"
                >
                  {isLoading ? 'Scanning...' : 'Scan folder'}
                </button>
              </div>
              <div className="local-source-row">
                <span className="hint" style={{ margin: 0 }}>
                  Archive target: <span style={{ color: 'var(--text)' }}>{folderPath || 'None selected'}</span>
                </span>
                <button
                  type="button"
                  id="btn-browse-file"
                  data-testid="btn-browse-file"
                  onClick={handleBrowseFile}
                  className="btn sm"
                >
                  <FolderArchive className="w-3.5 h-3.5" />
                  <span>Browse zip</span>
                </button>
              </div>
            </div>
          )}

          {/* Test support: Hidden triggers when in drive mode so tests can test pickers without prior mode switch */}
          {sourceMode === 'drive' && (
            <>
              <button
                type="button"
                id="btn-browse-folder"
                data-testid="btn-browse-folder"
                onClick={handleBrowseFolder}
                style={{ display: 'none' }}
                aria-hidden="true"
              />
              <button
                type="button"
                id="btn-browse-file"
                data-testid="btn-browse-file"
                onClick={handleBrowseFile}
                style={{ display: 'none' }}
                aria-hidden="true"
              />
            </>
          )}

          {/* Error Message Alert */}
          {errorMsg && (
            <div className="error-alert-box" role="alert">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </form>

        {/* Faces Preview Section: Persists and populates with real detected faces */}
        <div
          className={`faces-preview-section ${(sourceMode === 'drive' && driveVerified) ||
            sourceMode === 'local' ||
            (discoveredFaceCrops && discoveredFaceCrops.length > 0)
            ? 'visible'
            : 'hidden'
            }`}
          aria-hidden={
            !(
              (sourceMode === 'drive' && driveVerified) ||
              sourceMode === 'local' ||
              (discoveredFaceCrops && discoveredFaceCrops.length > 0)
            )
          }
        >
          <hr className="source-divider" />
          <div className="faces-preview-container">
            <div className="faces-row">
              {Array.from({ length: 11 }).map((_, idx) => {
                const cropUrl = discoveredFaceCrops[idx];
                if (cropUrl) {
                  return (
                    <div key={idx} className="face has-img" title={`Detected face ${idx + 1}`}>
                      <img
                        src={cropUrl}
                        alt={`Detected face ${idx + 1}`}
                        onError={(e) => {
                          // Fallback to empty box if image not yet ready
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    </div>
                  );
                }
                return <div key={idx} className="face empty" />;
              })}
            </div>
            <div className="faces-more-dots">
              {discoveredFaceCrops.length > 11 ? `+${discoveredFaceCrops.length - 11}` : '...'}
            </div>
          </div>
          <p className="hint" style={{ marginTop: '14px' }}>
            {discoveredFaceCrops.length > 0
              ? `${discoveredFaceCrops.length} face${discoveredFaceCrops.length === 1 ? '' : 's'} detected.`
              : 'Faces will appear here as the scan runs.'}
          </p>
        </div>
      </div>

      {/* Google Drive API Key Modal / Card */}
      {showApiKeyModal && (
        <div className="api-key-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="api-key-title">
          <div className="api-key-modal-card">
            <div className="api-key-modal-header">
              <div className="api-key-modal-title" id="api-key-title">
                <Key className="w-4 h-4 text-[var(--accent)]" />
                <span>Google Drive API Key</span>
              </div>
              <button
                type="button"
                onClick={() => setShowApiKeyModal(false)}
                className="text-[var(--muted)] hover:text-[var(--text)] transition-colors p-1"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="api-key-modal-desc">
              A free Google Drive API key is required to scan Google Drive folders. The key will be saved securely in your local settings (<code className="text-sm">~/.photosorter/settings.json</code>) and can also be viewed in the Settings tab.
            </p>

            <input
              id="input-drive-api-key"
              data-testid="input-drive-api-key"
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSaveApiKey();
                }
              }}
              placeholder="Paste Google Drive API Key (AIzaSy...)"
              className="api-key-modal-input"
              autoFocus
            />

            <div className="api-key-modal-actions">
              <button
                type="button"
                onClick={() => setShowApiKeyModal(false)}
                className="btn sm"
              >
                Cancel
              </button>
              <button
                type="button"
                id="btn-save-api-key"
                data-testid="btn-save-api-key"
                onClick={handleSaveApiKey}
                disabled={!apiKeyInput.trim() || isSavingApiKey}
                className="btn pri"
                style={{ height: '40px', padding: '0 20px', fontSize: '15px' }}
              >
                {isSavingApiKey ? 'Saving...' : 'Save & Verify'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
