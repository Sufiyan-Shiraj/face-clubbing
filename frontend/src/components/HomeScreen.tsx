import React, { useState } from 'react';
import { Folder, HardDrive, Play, CheckCircle2, AlertCircle, Globe, Key } from 'lucide-react';

interface HomeScreenProps {
  onStartJob: (inputPath?: string, driveFolder?: string, driveApiKey?: string) => void;
  isLoading?: boolean;
  currentInputPath?: string;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  onStartJob,
  isLoading,
  currentInputPath = 'test_photos',
}) => {
  const [sourceMode, setSourceMode] = useState<'local' | 'drive'>('local');
  const [folderPath, setFolderPath] = useState<string>(currentInputPath || 'test_photos');
  const [driveLink, setDriveLink] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleBrowseFolder = async () => {
    if (window.pywebview?.api?.select_folder) {
      try {
        const selected = await window.pywebview.api.select_folder('Select Photo Folder');
        if (selected) {
          setFolderPath(selected);
          setSourceMode('local');
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
        }
      };
      input.click();
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
    // Check if it's a valid URL format or raw alphanumeric ID
    const isRawId = /^[a-zA-Z0-9_-]{20,100}$/.test(trimmed);
    const isFolderUrl =
      /drive\.google\.com\/(?:drive\/)?(?:u\/\d+\/)?(?:mobile\/)?folders\/([a-zA-Z0-9_-]{20,100})/i.test(trimmed) ||
      /drive\.google\.com\/(?:open|folderview)\?(?:.*&)?id=([a-zA-Z0-9_-]{20,100})/i.test(trimmed);

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
    <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6">
      <div className="text-center mb-10">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Event Photo Sorting & Face Review
        </h1>
        <p className="mt-3 text-base text-neutral-400 max-w-2xl mx-auto">
          Group hundreds of event photos by attendee with automated face clustering,
          instant human review, and clean static export for Google Drive or web hosting.
        </p>
      </div>

      {/* Main Input Form */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 bg-neutral-900/60 border border-neutral-800 shadow-xl mb-10">
        {/* Source Mode Toggle */}
        <div className="flex rounded-xl bg-neutral-950 p-1 border border-neutral-800 mb-6 max-w-md mx-auto">
          <button
            type="button"
            id="btn-source-local"
            data-testid="btn-source-local"
            onClick={() => setSourceMode('local')}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              sourceMode === 'local'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <Folder className="w-4 h-4" />
            <span>Local Folder / Zip</span>
          </button>
          <button
            type="button"
            id="btn-source-drive"
            data-testid="btn-source-drive"
            onClick={() => setSourceMode('drive')}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              sourceMode === 'drive'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <HardDrive className="w-4 h-4" />
            <span>Google Drive Folder</span>
          </button>
        </div>

        <form onSubmit={handleStart} className="space-y-6">
          {sourceMode === 'local' ? (
            /* Local Folder / Zip Input */
            <div className="animate-fadeIn">
              <label
                htmlFor="input-source-path"
                className="block text-sm font-medium text-neutral-200 mb-2 flex items-center justify-between"
              >
                <span className="flex items-center gap-2">
                  <Folder className="w-4 h-4 text-blue-400" />
                  Local Folder or Zip Archive
                </span>
                <span className="text-xs text-neutral-500 font-normal">Offline Originals</span>
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  id="input-source-path"
                  data-testid="input-source-path"
                  type="text"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  placeholder="e.g. test_photos or C:\photos\event.zip"
                  className="flex-1 px-4 py-2.5 rounded-xl bg-neutral-950 border border-neutral-800 text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm font-mono transition-all"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    id="btn-browse-folder"
                    data-testid="btn-browse-folder"
                    onClick={handleBrowseFolder}
                    className="px-3 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-medium border border-blue-500/40 transition-colors whitespace-nowrap flex items-center gap-1.5"
                    title="Browse for folder"
                  >
                    <Folder className="w-3.5 h-3.5" />
                    Browse Folder
                  </button>
                  <button
                    type="button"
                    id="btn-browse-file"
                    data-testid="btn-browse-file"
                    onClick={handleBrowseFile}
                    className="px-3 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium border border-neutral-700 transition-colors whitespace-nowrap"
                    title="Browse for zip archive or file"
                  >
                    Browse File
                  </button>
                  <button
                    type="button"
                    onClick={() => setFolderPath('test_photos')}
                    className="px-3 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium border border-neutral-700 transition-colors whitespace-nowrap"
                  >
                    Use test_photos
                  </button>
                </div>
              </div>
              <p className="mt-1.5 text-xs text-neutral-500">
                Scans JPEG, PNG, HEIC, TIFF files or unzips archive automatically.
              </p>
            </div>
          ) : (
            /* Drive Link Input (Method 1) */
            <div className="animate-fadeIn">
              <div className="flex items-center justify-between mb-2">
                <label
                  htmlFor="input-drive-link"
                  className="text-sm font-medium text-neutral-200 flex items-center gap-2"
                >
                  <HardDrive className="w-4 h-4 text-emerald-400" />
                  Google Drive Folder Link
                </label>
                <span className="px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 text-xs font-medium border border-emerald-800/60 flex items-center gap-1">
                  <Globe className="w-3 h-3 text-emerald-400" /> Public (Anyone with link)
                </span>
              </div>
              <input
                id="input-drive-link"
                data-testid="input-drive-link"
                type="text"
                value={driveLink}
                onChange={(e) => setDriveLink(e.target.value)}
                placeholder="https://drive.google.com/drive/folders/1A2b3C... or folder ID"
                className="w-full px-4 py-2.5 rounded-xl bg-neutral-950 border border-neutral-800 text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm font-mono transition-all"
              />
              <div className="mt-2 p-3 rounded-xl bg-neutral-950/80 border border-neutral-800 text-xs text-neutral-400 space-y-1">
                <div className="flex items-center gap-1.5 text-neutral-300 font-semibold">
                  <Key className="w-3.5 h-3.5 text-amber-400" />
                  <span>Google Drive API Key</span>
                </div>
                <p>
                  Requires a free Google Drive API key (configure in <span className="text-blue-400 font-semibold">Settings</span> or set the <code className="text-amber-300">DRIVE_API_KEY</code> environment variable). Folder must be set to "Anyone with the link can view".
                </p>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 rounded-xl bg-red-950/30 border border-red-800/50 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Start Button */}
          <div className="pt-2">
            <button
              id="start-job-btn"
              data-testid="start-job-btn"
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/25 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isLoading ? 'Starting Engine...' : 'Start Face Sorting'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Feature Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800/80">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mb-3">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-neutral-200">Seed & Attach-Only</h3>
          <p className="mt-1 text-xs text-neutral-400 leading-relaxed">
            Stricter seed thresholds prevent spurious clusters. Profiles and small faces only attach to proven people.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800/80">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-3">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-neutral-200">Persistent Face Identity</h3>
          <p className="mt-1 text-xs text-neutral-400 leading-relaxed">
            All organizer decisions key strictly by anchor face and photo IDs. Merges and assignments survive re-runs.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800/80">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-3">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-neutral-200">Method 1 Drive Streaming</h3>
          <p className="mt-1 text-xs text-neutral-400 leading-relaxed">
            Download size-limited thumbnails on the fly with bounded concurrency, retry, and zero-sign-in security.
          </p>
        </div>
      </div>
    </div>
  );
};
