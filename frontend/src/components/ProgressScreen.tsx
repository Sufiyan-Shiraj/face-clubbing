import React, { useMemo, useState, useEffect, useRef } from 'react';
import { JobStatus } from '../types';
import {
  XCircle,
  ArrowRight,
  ShieldCheck,
  Check,
  AlertTriangle,
  Sparkles,
  Clock,
  Terminal,
  Copy,
  Search,
  X,
  ExternalLink,
} from 'lucide-react';
import { DetachedLogsWindow } from './DetachedLogsWindow';
import { MascotSticker } from './MascotSticker';

export interface ProgressScreenProps {
  status: JobStatus;
  progressHistory: JobStatus[];
  onCancelJob: () => void;
  onGoToReview: () => void;
  isCancelling?: boolean;
  discoveredFaceCrops?: string[];
  theme?: string;
}

export const ProgressScreen: React.FC<ProgressScreenProps> = ({
  status,
  progressHistory,
  onCancelJob,
  onGoToReview,
  isCancelling,
  discoveredFaceCrops = [],
  theme = 't-dark',
}) => {
  const isCompleted = status.status === 'completed';
  const isRunning = status.status === 'running';
  const isCancelled = status.status === 'cancelled';
  const isFailed = status.status === 'failed';

  // Modal and detached log window state
  const [showLogsModal, setShowLogsModal] = useState<boolean>(false);
  const [isDetached, setIsDetached] = useState<boolean>(false);
  const [logSearchQuery, setLogSearchQuery] = useState<string>('');
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Map backend stages to 4 visible pipeline steps
  const stage = (status.stage || '').toLowerCase();
  const isStage1Done = isCompleted || ['detecting', 'faces', 'clustering', 'exporting'].some((s) => stage.includes(s));
  const isStage1Active = isRunning && (stage.includes('model') || stage.includes('load') || stage === 'downloading' || stage === 'listing' || stage === 'starting');

  const isStage2Done = isCompleted || ['clustering', 'exporting'].some((s) => stage.includes(s));
  const isStage2Active = isRunning && (stage.includes('detect') || stage.includes('face') || stage.includes('scan'));

  const isStage3Done = isCompleted || stage.includes('export');
  const isStage3Active = isRunning && (stage.includes('cluster') || stage.includes('group'));

  const isStage4Done = isCompleted;
  const isStage4Active = isRunning && (stage.includes('export') || stage.includes('gallery') || stage.includes('save'));

  // Calculate stats display
  const photosCurrent = status.current || 0;
  const photosTotal = status.total || 0;
  const percentDisplay = Math.min(
    100,
    Math.max(
      0,
      status.percent !== undefined
        ? status.percent
        : photosTotal > 0
        ? Math.round((photosCurrent / photosTotal) * 100)
        : 0
    )
  );

  // Take only the latest 11 faces to display neatly in a single row without crowding
  const MAX_VISIBLE_FACES = 11;
  const totalFacesCount = discoveredFaceCrops.length;
  const recentFaces = useMemo(() => {
    if (totalFacesCount === 0) return [];
    return discoveredFaceCrops.slice(-MAX_VISIBLE_FACES).reverse();
  }, [discoveredFaceCrops, totalFacesCount]);

  const moreFacesCount = Math.max(0, totalFacesCount - MAX_VISIBLE_FACES);

  // Track elapsed scan time with start_time reference so minimizing main window causes no drift
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(() => status.elapsed_seconds || 0);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (typeof status.elapsed_seconds === 'number' && status.elapsed_seconds > 0) {
      setElapsedSeconds(status.elapsed_seconds);
      if (!startTimeRef.current && isRunning) {
        startTimeRef.current = Date.now() - status.elapsed_seconds * 1000;
      }
    }
  }, [status.elapsed_seconds, isRunning]);

  useEffect(() => {
    if (!isRunning) {
      startTimeRef.current = null;
      return;
    }
    if (!startTimeRef.current) {
      startTimeRef.current = status.start_time ? status.start_time * 1000 : Date.now() - (elapsedSeconds * 1000);
    }
    const interval = setInterval(() => {
      if (startTimeRef.current) {
        const exact = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setElapsedSeconds(exact);
      } else {
        setElapsedSeconds((prev) => prev + 1);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const formatElapsedTime = (totalSecs: number): string => {
    const s = Math.max(0, Math.floor(totalSecs));
    const hours = Math.floor(s / 3600);
    const minutes = Math.floor((s % 3600) / 60);
    const seconds = s % 60;
    if (hours > 0) {
      return `${hours}h ${minutes.toString().padStart(2, '0')}m ${seconds.toString().padStart(2, '0')}s`;
    }
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Complete list of all activity logs (showing ALL logs, not just recent ones)
  const allLogs = useMemo(() => {
    if (progressHistory.length > 0) {
      return progressHistory.map((p, idx) => ({
        id: idx,
        stage: p.stage || p.status || 'INFO',
        message: p.message || `Processing batch step (${p.current}/${p.total})`,
        percent: p.percent ?? 0,
      }));
    }
    return [
      {
        id: 0,
        stage: status.stage || status.status || 'START',
        message: status.message || 'Tracking facial recognition engine on your computer.',
        percent: status.percent ?? 0,
      },
    ];
  }, [progressHistory, status]);

  const filteredLogs = useMemo(() => {
    if (!logSearchQuery.trim()) return allLogs;
    const q = logSearchQuery.toLowerCase();
    return allLogs.filter(
      (l) => l.stage.toLowerCase().includes(q) || l.message.toLowerCase().includes(q)
    );
  }, [allLogs, logSearchQuery]);

  // Auto-scroll logs window to bottom as new entries stream in
  useEffect(() => {
    if (showLogsModal && logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [showLogsModal, allLogs.length]);

  // Close modal on ESC key
  useEffect(() => {
    if (!showLogsModal) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowLogsModal(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showLogsModal]);

  // Copy logs to clipboard
  const handleCopyLogs = () => {
    const text = allLogs
      .map((l, i) => `[${(i + 1).toString().padStart(3, '0')}] [${l.stage}] (${l.percent}%) ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  };

  return (
    <div className="main-content-flow" style={{ maxWidth: '960px', width: '100%', textAlign: 'left', alignItems: 'stretch' }}>
      {/* Top Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[var(--line)] gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="h2" style={{ margin: 0, textAlign: 'left' }}>
              {isCompleted
                ? 'Clustering complete'
                : isFailed
                ? 'Scan interrupted'
                : isCancelled
                ? 'Scan cancelled'
                : 'Reading faces'}
            </h1>
            <span
              data-testid="progress-stage"
              className="px-3 py-1 rounded border border-[var(--line)] bg-[var(--panel)] text-[var(--accent-ink)] text-sm font-mono font-bold uppercase"
            >
              {status.stage || status.status}
            </span>
            <span
              data-testid="progress-elapsed-badge"
              className="px-3 py-1 rounded border border-[var(--line)] bg-[var(--input)] text-[var(--text)] text-sm font-mono font-bold flex items-center gap-1.5 shadow-[1px_1px_0px_var(--line)]"
              title="Time elapsed since scan started"
            >
              <Clock className="w-4 h-4 text-[var(--accent)]" />
              <span>{formatElapsedTime(elapsedSeconds)}</span>
            </span>
          </div>
          <p className="hint m-0 mt-1.5 text-sm md:text-base" style={{ textAlign: 'left' }}>
            {status.message || 'Tracking facial recognition engine on your machine.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            id="btn-open-logs"
            data-testid="btn-open-logs"
            onClick={() => {
              if (isDetached) {
                setIsDetached(false);
                setTimeout(() => setIsDetached(true), 10);
              } else {
                setShowLogsModal(true);
              }
            }}
            className="btn sm"
            style={{ height: '36px', padding: '0 14px' }}
            title={isDetached ? 'Focus detached logs window' : 'Open complete engine activity log window'}
          >
            <Terminal className="w-4 h-4 text-[var(--accent)]" />
            <span>Logs</span>
            {allLogs.length > 0 && (
              <span className="ml-1 text-xs px-1.5 py-0.2 rounded bg-[var(--input)] text-[var(--muted)] font-mono">
                {allLogs.length}
              </span>
            )}
          </button>

          <button
            type="button"
            id="btn-detach-logs"
            data-testid="btn-detach-logs"
            onClick={() => {
              setShowLogsModal(false);
              setIsDetached(true);
            }}
            className={`btn sm ${isDetached ? 'pri' : ''}`}
            style={{ height: '36px', padding: '0 12px' }}
            title="Detach logs into separate floating window (stays open when main window is minimized)"
          >
            <ExternalLink className="w-3.5 h-3.5 mr-1 text-[var(--accent)]" />
            <span>{isDetached ? 'Detached ↗' : 'Detach'}</span>
          </button>

          {isRunning && (
            <button
              id="cancel-job-btn"
              data-testid="cancel-job-btn"
              onClick={onCancelJob}
              disabled={isCancelling}
              className="btn sm"
              style={{ borderColor: 'var(--accent)', color: 'var(--accent-ink)' }}
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>{isCancelling ? 'Cancelling...' : 'Cancel scan'}</span>
            </button>
          )}

          {isCompleted && (
            <button
              id="goto-review-btn"
              data-testid="goto-review-btn"
              onClick={onGoToReview}
              className="btn pri sm"
              style={{ height: '36px', padding: '0 20px', color: 'var(--on-accent)' }}
            >
              <span style={{ color: 'inherit' }}>Go to Review</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" style={{ color: 'inherit' }} />
            </button>
          )}
        </div>
      </div>

      {/* Completion Banner */}
      {isCompleted && (
        <div
          id="scan-completion-banner"
          data-testid="scan-completion-banner"
          className="mt-6 p-5 sm:p-6 rounded-lg border-2 border-[var(--accent)] bg-[var(--card-bg)] flex flex-col sm:flex-row items-center justify-between gap-5 shadow-[3px_3px_0px_var(--line)] animate-fadeIn"
        >
          <div className="flex items-center gap-4 w-full sm:w-auto">
            <div className="w-16 h-16 rounded-xl bg-[var(--input)] border-2 border-[var(--line)] flex items-center justify-center p-1 flex-shrink-0 shadow-[2px_2px_0px_var(--line)]">
              <MascotSticker pose={4} theme={theme} className="w-full h-full object-contain" />
            </div>
            <div>
              <div className="font-extrabold text-base sm:text-lg text-[var(--text)] flex items-center gap-2">
                <span>Face Clustering Completed!</span>
                <span className="text-xs px-2 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/40">100% READY</span>
              </div>
              <div className="text-sm text-[var(--muted)] mt-1 font-mono">
                {photosTotal || photosCurrent} photos analyzed • {totalFacesCount > 0 ? `${totalFacesCount.toLocaleString()} faces detected` : 'Faces grouped'} • Completed in {formatElapsedTime(elapsedSeconds)}
              </div>
            </div>
          </div>
          <button
            id="goto-review-btn-banner"
            onClick={onGoToReview}
            className="btn pri sm w-full sm:w-auto flex-shrink-0"
            style={{ height: '42px', padding: '0 24px', fontSize: '15px', color: 'var(--on-accent)', fontWeight: 800 }}
          >
            <span style={{ color: 'inherit' }}>Review People</span>
            <ArrowRight className="w-4 h-4 ml-1" style={{ color: 'inherit' }} />
          </button>
        </div>
      )}

      {/* Big Percent & Subtitle Display */}
      <div className="flex flex-col sm:flex-row items-start sm:items-baseline justify-between gap-4 sm:gap-6 mt-7">
        <div className="flex items-baseline gap-4 sm:gap-6">
          <p className="big" style={{ margin: 0 }}>{percentDisplay}%</p>
          <p className="sub m-0 mb-1.5 text-base md:text-lg" style={{ textAlign: 'left', margin: 0 }}>
            {photosTotal > 0
              ? `Photo ${photosCurrent} of ${photosTotal}. This runs on your computer, so a big folder takes a while.`
              : status.message || 'Processing photos locally on your computer.'}
          </p>
        </div>
        {isRunning && (
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-md bg-[var(--input)] border border-[var(--panel-border)] shadow-[2px_2px_0px_var(--line)] flex-shrink-0">
            <MascotSticker pose={5} theme={theme} className="w-8 h-8 object-contain flex-shrink-0" />
            <div className="text-xs font-mono font-bold leading-tight">
              <span className="text-[var(--accent)] block">Local Engine Active</span>
              <span className="text-[var(--muted)]">{photosTotal ? `${photosCurrent} / ${photosTotal}` : 'Scanning...'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div
        className="bar mt-5"
        role="progressbar"
        aria-valuenow={percentDisplay}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <i style={{ width: `${percentDisplay}%` }}></i>
      </div>

      {/* Stat Cards Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
        <div className="card">
          <div className="label text-sm">Photos read</div>
          <div className="stat">
            {photosCurrent}
            <span className="text-base text-[var(--muted)] font-mono font-normal">
              {' '}/ {photosTotal || '--'}
            </span>
          </div>
        </div>

        <div className="card">
          <div className="label text-sm">Faces found</div>
          <div className="stat">
            {totalFacesCount > 0 ? totalFacesCount.toLocaleString() : '--'}
          </div>
        </div>

        <div className="card" data-testid="time-elapsed-card">
          <div className="label text-sm flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-[var(--accent)]" />
            <span>Time Elapsed</span>
          </div>
          <div className="stat text-2xl font-mono">
            {formatElapsedTime(elapsedSeconds)}
          </div>
          <div className="text-xs text-[var(--muted)] font-mono mt-1">
            {isCompleted ? 'Final scan duration' : isRunning ? 'Scanning in progress...' : 'Elapsed time'}
          </div>
        </div>

        <div className="card">
          <div className="label text-sm">Engine Mode</div>
          <div className="stat text-2xl flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-[var(--accent)]" />
            <span className="text-lg">Local CPU/GPU</span>
          </div>
        </div>
      </div>

      {/* Bottom Two-Column Split: Faces on Left, Stages on Right */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-7">
        {/* Left 2 Cols: Latest Faces Preview (Clean Single Row) */}
        <div className="md:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <div className="label text-sm" style={{ margin: 0 }}>Latest faces</div>
              {totalFacesCount > 0 && (
                <div className="text-sm font-mono text-[var(--muted)]">
                  {totalFacesCount.toLocaleString()} total
                </div>
              )}
            </div>

            {/* Exactly 11 boxes in a clean, non-wrapping horizontal strip */}
            <div
              className="faces-preview-container"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                overflow: 'hidden',
              }}
            >
              <div
                className="faces-row"
                style={{
                  display: 'flex',
                  gap: '8px',
                  flexWrap: 'nowrap',
                  overflow: 'hidden',
                  width: '100%',
                }}
              >
                {Array.from({ length: MAX_VISIBLE_FACES }).map((_, idx) => {
                  const cropUrl = recentFaces[idx];
                  if (cropUrl) {
                    return (
                      <div
                        key={idx}
                        className="face has-img"
                        style={{
                          width: '48px',
                          height: '48px',
                          flexShrink: 0,
                          borderRadius: '3px',
                        }}
                        title={`Detected face #${totalFacesCount - idx}`}
                      >
                        <img
                          src={cropUrl}
                          alt={`Face ${totalFacesCount - idx}`}
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      </div>
                    );
                  }
                  return (
                    <div
                      key={idx}
                      className="face empty"
                      style={{
                        width: '48px',
                        height: '48px',
                        flexShrink: 0,
                        borderRadius: '3px',
                      }}
                    />
                  );
                })}
              </div>

              {moreFacesCount > 0 && (
                <div
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px',
                    fontWeight: 700,
                    color: 'var(--muted)',
                    whiteSpace: 'nowrap',
                    padding: '4px 10px',
                    border: '1px solid var(--line)',
                    borderRadius: '4px',
                    background: 'var(--panel)',
                    flexShrink: 0,
                  }}
                  title={`${moreFacesCount.toLocaleString()} additional faces detected`}
                >
                  +{moreFacesCount.toLocaleString()}
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Right 1 Col: Stages Checklist */}
        <div className="card" style={{ padding: '16px 20px' }}>
          <div className="label text-sm pt-1 pb-1 border-b border-[var(--line)]" style={{ margin: 0 }}>
            Pipeline Stages
          </div>

          <div className="stage text-base">
            <span className={`dot ${isStage1Done ? 'ok' : isStage1Active ? 'run' : ''}`}></span>
            <span className={isStage1Active ? 'font-bold text-[var(--text)]' : isStage1Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Load face model
            </span>
            {isStage1Done && <Check className="w-4 h-4 text-[var(--accent)] ml-auto" />}
          </div>

          <div className="stage text-base">
            <span className={`dot ${isStage2Done ? 'ok' : isStage2Active ? 'run' : ''}`}></span>
            <span className={isStage2Active ? 'font-bold text-[var(--text)]' : isStage2Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Find faces
            </span>
            {isStage2Done && <Check className="w-4 h-4 text-[var(--accent)] ml-auto" />}
          </div>

          <div className="stage text-base">
            <span className={`dot ${isStage3Done ? 'ok' : isStage3Active ? 'run' : ''}`}></span>
            <span className={isStage3Active ? 'font-bold text-[var(--text)]' : isStage3Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Group people
            </span>
            {isStage3Done && <Check className="w-4 h-4 text-[var(--accent)] ml-auto" />}
          </div>

          <div className="stage text-base" style={{ borderBottom: 0 }}>
            <span className={`dot ${isStage4Done ? 'ok' : isStage4Active ? 'run' : ''}`}></span>
            <span className={isStage4Active ? 'font-bold text-[var(--text)]' : isStage4Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Build gallery
            </span>
            {isStage4Done && <Check className="w-4 h-4 text-[var(--accent)] ml-auto" />}
          </div>
        </div>
      </div>

      {/* Activity Logs trigger bar */}
      <div className="mt-8 pt-4 border-t border-[var(--line)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 font-mono text-sm text-[var(--muted)]">
          <Terminal className="w-4 h-4 text-[var(--accent)]" />
          <span>Activity Log: {allLogs.length} events recorded</span>
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-[var(--accent-ink)] font-bold ml-2">
              <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
              Live Feed
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            id="btn-view-all-logs"
            data-testid="btn-view-all-logs"
            onClick={() => setShowLogsModal(true)}
            className="btn sm"
            style={{ height: '36px', padding: '0 16px', fontWeight: 600 }}
            title="Open complete engine activity log modal"
          >
            <Terminal className="w-3.5 h-3.5 mr-1 text-[var(--accent)]" />
            <span>Open Logs Window</span>
          </button>

          <button
            type="button"
            id="btn-detach-bottom"
            data-testid="btn-detach-bottom"
            onClick={() => {
              setShowLogsModal(false);
              setIsDetached(true);
            }}
            className="btn sm"
            style={{ height: '36px', padding: '0 14px' }}
            title="Pop out into a separate window you can keep on screen while minimizing the main app"
          >
            <ExternalLink className="w-3.5 h-3.5 mr-1 text-[var(--accent)]" />
            <span>Detach to Desktop</span>
          </button>
        </div>
      </div>

      {/* Hidden test-hook for progress-updates-log if modal is closed */}
      {!showLogsModal && (
        <div id="progress-updates-log" data-testid="progress-updates-log" style={{ display: 'none' }} aria-hidden="true">
          {allLogs.map((p, idx) => (
            <div key={idx}>
              <span>[{p.stage}] {p.message}</span>
              <span>{p.percent}%</span>
            </div>
          ))}
        </div>
      )}

      {/* Dedicated Engine Activity Logs Modal Window */}
      {showLogsModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Engine Activity Logs"
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(3px)' }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowLogsModal(false);
          }}
        >
          <div
            className="card relative flex flex-col w-full max-w-3xl overflow-hidden shadow-2xl"
            style={{
              maxHeight: '85vh',
              background: 'var(--panel)',
              border: '2px solid var(--line)',
              padding: 0,
            }}
          >
            {/* Modal Header */}
            <div
              className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--line)] bg-[var(--bg)]"
              style={{ flexShrink: 0 }}
            >
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-[var(--accent)]" />
                <span className="font-bold text-sm md:text-base text-[var(--text)] tracking-wide">
                  Engine Activity Log
                </span>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-[var(--input)] text-[var(--accent-ink)] border border-[var(--line)]">
                  {allLogs.length} events
                </span>
                {isRunning && (
                  <span className="flex items-center gap-1.5 text-xs text-[var(--accent-ink)] font-mono">
                    <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
                    Live
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  id="btn-detach-modal"
                  data-testid="btn-detach-modal"
                  onClick={() => {
                    setShowLogsModal(false);
                    setIsDetached(true);
                  }}
                  className="btn sm"
                  style={{ height: '30px', padding: '0 10px', fontSize: '12px' }}
                  title="Pop out into separate window so you can minimize the main window"
                >
                  <ExternalLink className="w-3.5 h-3.5 mr-1 text-[var(--accent)]" />
                  <span>Detach Window</span>
                </button>
                <button
                  type="button"
                  id="btn-copy-logs"
                  data-testid="btn-copy-logs"
                  onClick={handleCopyLogs}
                  className="btn sm"
                  style={{ height: '30px', padding: '0 10px', fontSize: '12px' }}
                  title="Copy all logs to clipboard"
                >
                  {isCopied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-green-500 mr-1" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 mr-1 text-[var(--muted)]" />
                      <span>Copy All</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  id="btn-close-logs-modal"
                  data-testid="btn-close-logs-modal"
                  onClick={() => setShowLogsModal(false)}
                  className="p-1 rounded hover:bg-[var(--input)] text-[var(--muted)] hover:text-[var(--text)] transition-colors"
                  title="Close log window (Esc)"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Filter Search Bar */}
            <div className="px-5 py-2.5 border-b border-[var(--line)] bg-[var(--panel)] flex items-center gap-2 flex-shrink-0">
              <Search className="w-4 h-4 text-[var(--muted)] flex-shrink-0" />
              <input
                type="text"
                placeholder="Filter logs by stage or message..."
                value={logSearchQuery}
                onChange={(e) => setLogSearchQuery(e.target.value)}
                className="bg-transparent border-none text-xs md:text-sm text-[var(--text)] font-mono outline-none w-full"
              />
              {logSearchQuery && (
                <button
                  type="button"
                  onClick={() => setLogSearchQuery('')}
                  className="text-xs text-[var(--muted)] hover:text-[var(--text)]"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Modal Body - Terminal Output */}
            <div
              id="progress-updates-log"
              data-testid="progress-updates-log"
              ref={logsContainerRef}
              className="flex-1 p-4 overflow-y-auto font-mono text-xs md:text-sm space-y-2 bg-[var(--input)]"
              style={{ minHeight: '320px', maxHeight: '55vh' }}
            >
              {filteredLogs.length === 0 ? (
                <div className="p-8 text-center text-[var(--muted)] font-mono text-sm">
                  {logSearchQuery ? 'No log entries match the search query.' : 'No activity logged yet.'}
                </div>
              ) : (
                filteredLogs.map((log, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between gap-3 p-1.5 rounded hover:bg-[var(--panel)] transition-colors"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}
                  >
                    <div className="flex items-start gap-2 overflow-hidden">
                      <span className="text-[var(--muted)] select-none text-xs min-w-[28px] text-right font-mono">
                        {idx + 1}.
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[11px] font-bold uppercase bg-[var(--panel)] text-[var(--accent-ink)] border border-[var(--line)] flex-shrink-0">
                        {log.stage}
                      </span>
                      <span className="text-[var(--text)] break-words leading-relaxed">
                        {log.message}
                      </span>
                    </div>
                    <span className="text-[var(--accent-ink)] font-bold text-xs flex-shrink-0">
                      {log.percent}%
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div
              className="flex items-center justify-between px-5 py-2.5 border-t border-[var(--line)] bg-[var(--bg)] text-xs font-mono text-[var(--muted)]"
              style={{ flexShrink: 0 }}
            >
              <span>Showing {filteredLogs.length} of {allLogs.length} events</span>
              <button
                type="button"
                onClick={() => setShowLogsModal(false)}
                className="btn sm"
                style={{ height: '28px', padding: '0 12px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Failure / Interrupted Alert */}
      {(isFailed || isCancelled) && (
        <div className="mt-6 p-4 rounded-lg bg-[var(--panel)] border border-[var(--accent)] text-[var(--accent-ink)] text-xs flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{status.message || 'Job was stopped.'}</span>
          </div>
          <button onClick={onGoToReview} className="btn sm">
            <span>Back to People</span>
          </button>
        </div>
      )}
      {/* Detachable Native Desktop Logs Window */}
      <DetachedLogsWindow
        isOpen={isDetached}
        onClose={() => setIsDetached(false)}
        onDock={() => {
          setIsDetached(false);
          setShowLogsModal(true);
        }}
        allLogs={allLogs}
        isRunning={isRunning}
        status={status}
        elapsedSeconds={elapsedSeconds}
        formatElapsedTime={formatElapsedTime}
        theme={theme}
      />
    </div>
  );
};
