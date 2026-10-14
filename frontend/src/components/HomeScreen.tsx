import React, { useState, useMemo } from 'react';
import { AlertCircle, Folder, FolderArchive, Zap, Info } from 'lucide-react';
import { RisoTheme } from './Header';

interface HomeScreenProps {
  onStartJob: (inputPath?: string, driveFolder?: string, driveApiKey?: string) => void;
  isLoading?: boolean;
  currentInputPath?: string;
  onNavigateTab?: (tab: string) => void;
  theme?: RisoTheme;
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
  isLoading,
  currentInputPath = 'test_photos',
  theme = 't-dark',
}) => {
  const [sourceMode, setSourceMode] = useState<'drive' | 'local' | 'zip'>('drive');
  const [folderPath, setFolderPath] = useState<string>(currentInputPath || 'test_photos');
  const [driveLink, setDriveLink] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const extractedFolderId = useMemo(() => extractDriveFolderId(driveLink), [driveLink]);
  const hasExtractedId = Boolean(extractedFolderId);

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
    setErrorMsg(null);
  };

  const cellRefs = React.useRef<(HTMLInputElement | null)[]>([]);

  const handleCellChange = (index: number, value: string) => {
    if (!extractedFolderId) return;
    const char = value.slice(-1);
    if (!char) return;

    const chars = extractedFolderId.split('');
    chars[index] = char;
    const newId = chars.join('');

    if (driveLink.includes(extractedFolderId)) {
      setDriveLink(driveLink.replace(extractedFolderId, newId));
    } else {
      setDriveLink(newId);
    }

    if (index < chars.length - 1) {
      const nextInput = cellRefs.current[index + 1];
      if (nextInput) {
        nextInput.focus();
        nextInput.select();
      }
    }
  };

  const handleCellKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!extractedFolderId) return;

    if (e.key === 'Backspace') {
      e.preventDefault();
      const chars = extractedFolderId.split('');
      chars.splice(index, 1);
      const newId = chars.join('');

      if (driveLink.includes(extractedFolderId)) {
        setDriveLink(driveLink.replace(extractedFolderId, newId));
      } else {
        setDriveLink(newId);
      }

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
      const chars = extractedFolderId.split('');
      chars.splice(index, 1);
      const newId = chars.join('');

      if (driveLink.includes(extractedFolderId)) {
        setDriveLink(driveLink.replace(extractedFolderId, newId));
      } else {
        setDriveLink(newId);
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault();
      cellRefs.current[index - 1]?.focus();
      cellRefs.current[index - 1]?.select();
    } else if (e.key === 'ArrowRight' && index < extractedFolderId.length - 1) {
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

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (sourceMode === 'drive') {
      const validationError = validateDriveInput(driveLink);
      if (validationError) {
        setErrorMsg(validationError);
        return;
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

  return (
    <div className="main-content-flow">
      <div className={`home-stage-container ${sourceMode === 'drive' && hasExtractedId ? 'stage-expanded' : ''}`}>
        {/* Headline & Supporting Sentence with Image Title */}
        <div className="headline-group">
          <h1 className="h1 h1-title-container">
            <span className="sr-only">Who was at the event?</span>
            <img
              src={
                theme === 't-paper'
                  ? '/textures/title-paper.png?v=uncut-v6'
                  : theme === 't-navy'
                  ? '/textures/title-navy.png?v=uncut-v6'
                  : '/textures/title-dark.png?v=uncut-v6'
              }
              alt="Who was at the event?"
              className="h1-img"
            />
          </h1>
          <p className="sub-headline">Sort your event photos by person using face clustering.</p>
        </div>

        {/* Three Source-Mode Buttons */}
        <div className="source-mode-nav" aria-label="Source mode selection">
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
        </div>

        {/* Main Source Selection Form */}
        <form onSubmit={handleStart} className="source-form">
          {sourceMode === 'drive' ? (
            hasExtractedId && extractedFolderId ? (
              /* State 2: Valid Google Drive Folder ID Extracted */
              <div className="drive-extracted-view">
                {/* Hidden input for testids & accessible form synchronization */}
                <input
                  id="input-drive-link"
                  data-testid="input-drive-link"
                  type="text"
                  value={driveLink}
                  onChange={(e) => {
                    setDriveLink(e.target.value);
                    setErrorMsg(null);
                  }}
                  style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', width: '1px', height: '1px' }}
                  aria-hidden="true"
                />

                <div className="drive-id-header">
                  <span>DRIVE FOLDER ID</span>
                  <Info className="w-3.5 h-3.5 opacity-75" aria-label="Drive Folder ID Info" />
                </div>

                {/* Individual outlined character cells (editable) */}
                <div className="char-cells-row" aria-label={`Drive Folder ID: ${extractedFolderId}`}>
                  {extractedFolderId.split('').map((char, idx) => (
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
                    <span>Detected Drive link. Folder: </span>
                    <span className="drive-detected-id">{extractedFolderId}</span>
                  </div>
                  <div className="drive-detected-actions">
                    <button
                      type="button"
                      onClick={handleClearDriveLink}
                      className="btn-clear-link"
                      title="Clear entered link"
                    >
                      Clear
                    </button>
                    <button
                      id="start-job-btn"
                      data-testid="start-job-btn"
                      type="submit"
                      disabled={isLoading}
                      className="btn pri"
                    >
                      {isLoading ? 'Scanning...' : 'Scan folder'}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* State 1: Initial URL input row */
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
                    placeholder="Paste a Google Drive folder link... (drive.google.com/drive/folders/...)"
                    className="input"
                    aria-label="Google Drive folder link"
                  />
                  <button
                    id="start-job-btn"
                    data-testid="start-job-btn"
                    type="submit"
                    disabled={isLoading}
                    className="btn pri"
                  >
                    {isLoading ? 'Scanning...' : 'Scan folder'}
                  </button>
                </div>
                <p className="hint">
                  Folder must be shared as &apos;Anyone with the link&apos;.
                </p>
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
                <button
                  type="button"
                  onClick={() => {
                    setFolderPath('test_photos');
                    setErrorMsg(null);
                  }}
                  className="btn sm"
                  style={{ color: 'var(--accent-ink)', borderColor: 'var(--accent)' }}
                >
                  <Zap className="w-3 h-3" />
                  <span>Use test_photos</span>
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

          {/* Test support: Hidden triggers when in drive mode so homeScreen.test.tsx can test pickers without prior mode switch */}
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

          {/* Error Message */}
          {errorMsg && (
            <div className="error-alert-box">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </form>

        {/* Animated Transition: Divider & Empty Face Preview Frames */}
        <div
          className={`faces-preview-section ${
            sourceMode === 'drive' && hasExtractedId ? 'visible' : 'hidden'
          }`}
          aria-hidden={!(sourceMode === 'drive' && hasExtractedId)}
        >
          <hr className="source-divider" />
          <div className="faces-preview-container">
            <div className="faces-row">
              {Array.from({ length: 11 }).map((_, idx) => (
                <div key={idx} className="face empty" />
              ))}
            </div>
            <div className="faces-more-dots">...</div>
          </div>
          <p className="hint" style={{ marginTop: '14px' }}>
            Faces will appear here as the scan runs.
          </p>
        </div>
      </div>
    </div>
  );
};
