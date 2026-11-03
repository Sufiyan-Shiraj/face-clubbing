import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Sparkles, ExternalLink, X, RefreshCw } from 'lucide-react';

interface AppUpdateBannerProps {
  variant?: 'banner' | 'settings';
}

export const AppUpdateBanner: React.FC<AppUpdateBannerProps> = ({ variant = 'banner' }) => {
  const [updateInfo, setUpdateInfo] = useState<{
    update_available: boolean;
    current_version: string;
    latest_version: string;
    release_name: string;
    release_url: string;
    release_notes: string;
  } | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const checkForUpdate = async () => {
    setIsChecking(true);
    try {
      const res = await api.checkAppUpdate();
      setUpdateInfo(res);
    } catch {
      // Offline safe, ignore error
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkForUpdate();
  }, []);

  if (variant === 'settings') {
    return (
      <div className="flex flex-col gap-2 p-3 bg-[var(--input)] border border-[var(--panel-border)] rounded text-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--accent)]" />
            <span className="font-bold text-[var(--text)]">CatLog Updates</span>
          </div>
          <button
            type="button"
            id="btn-check-app-update"
            data-testid="btn-check-app-update"
            onClick={checkForUpdate}
            disabled={isChecking}
            className="btn btn-subtle text-xs py-1 px-2.5 flex items-center gap-1.5"
            title="Check GitHub for newer releases"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`} />
            <span>{isChecking ? 'Checking...' : 'Check for Update'}</span>
          </button>
        </div>

        <div className="text-[var(--muted)] flex items-center justify-between">
          <span>Current Version: <strong className="text-[var(--text)] font-mono">{updateInfo?.current_version || '0.1.0-rc1'}</strong></span>
          {updateInfo?.update_available && (
            <span className="text-amber-400 font-bold flex items-center gap-1">
              New: v{updateInfo.latest_version}
            </span>
          )}
        </div>

        {updateInfo?.update_available ? (
          <div className="mt-1 p-2 bg-amber-500/10 border border-amber-500/30 rounded flex items-center justify-between">
            <div>
              <p className="font-bold text-amber-300 m-0">A new version of CatLog is available!</p>
              <p className="text-[11px] text-amber-200/80 m-0 font-mono">{updateInfo.release_name || `CatLog v${updateInfo.latest_version}`}</p>
            </div>
            <a
              id="link-view-github-release"
              data-testid="link-view-github-release"
              href={updateInfo.release_url}
              target="_blank"
              rel="noreferrer"
              className="btn btn-primary text-xs py-1 px-3 flex items-center gap-1"
            >
              <span>View Release</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        ) : (
          <p className="text-[11px] text-[var(--muted)] m-0">
            {updateInfo?.checked_online ? 'CatLog is up to date with official GitHub releases.' : 'Checking release status in the background.'}
          </p>
        )}
      </div>
    );
  }

  // Header / Top subtle notice banner
  if (!updateInfo?.update_available || dismissed) {
    return null;
  }

  return (
    <div
      id="app-update-notice-banner"
      data-testid="app-update-notice-banner"
      className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-1.5 flex items-center justify-between text-xs text-amber-200"
    >
      <div className="flex items-center gap-2">
        <Sparkles className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
        <span>
          A new version of CatLog (<strong className="font-mono text-amber-300">v{updateInfo.latest_version}</strong>) is available.
        </span>
      </div>
      <div className="flex items-center gap-3">
        <a
          id="banner-view-github-release-link"
          data-testid="banner-view-github-release-link"
          href={updateInfo.release_url}
          target="_blank"
          rel="noreferrer"
          className="underline font-bold text-amber-300 hover:text-amber-100 flex items-center gap-1"
        >
          <span>What's new</span>
          <ExternalLink className="w-3 h-3" />
        </a>
        <button
          type="button"
          id="btn-dismiss-app-update-banner"
          data-testid="btn-dismiss-app-update-banner"
          onClick={() => setDismissed(true)}
          className="text-amber-400 hover:text-amber-200 p-0.5"
          title="Dismiss notice"
          aria-label="Dismiss notice"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

