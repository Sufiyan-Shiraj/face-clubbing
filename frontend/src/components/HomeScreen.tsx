import React, { useState } from 'react';
import { Folder, HardDrive, Play, Lock, CheckCircle2, AlertCircle } from 'lucide-react';

interface HomeScreenProps {
  onStartJob: (inputPath: string) => void;
  isLoading?: boolean;
  currentInputPath?: string;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  onStartJob,
  isLoading,
  currentInputPath = 'test_photos',
}) => {
  const [folderPath, setFolderPath] = useState<string>(currentInputPath || 'test_photos');
  const [driveLink, setDriveLink] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (!folderPath.trim()) {
      setErrorMsg('Please specify a folder path or zip archive.');
      return;
    }
    setErrorMsg(null);
    onStartJob(folderPath.trim());
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
        <form onSubmit={handleStart} className="space-y-6">
          {/* Local Folder / Zip Input */}
          <div>
            <label
              htmlFor="input-source-path"
              className="block text-sm font-medium text-neutral-200 mb-2 flex items-center justify-between"
            >
              <span className="flex items-center gap-2">
                <Folder className="w-4 h-4 text-blue-400" />
                Local Folder or Zip Archive
              </span>
              <span className="text-xs text-neutral-500 font-normal">Method 2 / Local Offline</span>
            </label>
            <div className="flex gap-2">
              <input
                id="input-source-path"
                data-testid="input-source-path"
                type="text"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder="e.g. test_photos or C:\photos\event.zip"
                className="flex-1 px-4 py-2.5 rounded-xl bg-neutral-950 border border-neutral-800 text-neutral-100 placeholder-neutral-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm font-mono transition-all"
              />
              <button
                type="button"
                onClick={() => setFolderPath('test_photos')}
                className="px-3 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium border border-neutral-700 transition-colors whitespace-nowrap"
              >
                Use test_photos
              </button>
            </div>
            <p className="mt-1.5 text-xs text-neutral-500">
              Scans JPEG, PNG, HEIC, TIFF files or unzips archive automatically.
            </p>
          </div>

          {/* Drive Link Input (Disabled, Phase 6) */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                htmlFor="input-drive-link"
                className="text-sm font-medium text-neutral-400 flex items-center gap-2"
              >
                <HardDrive className="w-4 h-4 text-neutral-500" />
                Google Drive Folder Link
              </label>
              <span
                id="drive-phase6-badge"
                data-testid="drive-phase6-badge"
                className="px-2 py-0.5 rounded-full bg-neutral-800 text-neutral-400 text-xs font-medium border border-neutral-700 flex items-center gap-1"
              >
                <Lock className="w-3 h-3 text-amber-500" /> Phase 6
              </span>
            </div>
            <input
              id="input-drive-link"
              data-testid="input-drive-link"
              type="text"
              disabled
              value={driveLink}
              onChange={(e) => setDriveLink(e.target.value)}
              placeholder="https://drive.google.com/drive/folders/... (Wired in Phase 6)"
              className="w-full px-4 py-2.5 rounded-xl bg-neutral-950/50 border border-neutral-800/60 text-neutral-500 cursor-not-allowed text-sm font-mono"
            />
            <p className="mt-1.5 text-xs text-neutral-500">
              Read-only Drive link ingestion without sign-in will be enabled in Phase 6.
            </p>
          </div>

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
              className="w-full py-3.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/25 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed"
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
          <h3 className="text-sm font-semibold text-neutral-200">Zero-Secret Public Bundle</h3>
          <p className="mt-1 text-xs text-neutral-400 leading-relaxed">
            Static web viewer with only public thumbs, crops, and people.json. No organizer caches or secrets ever leak.
          </p>
        </div>
      </div>
    </div>
  );
};
