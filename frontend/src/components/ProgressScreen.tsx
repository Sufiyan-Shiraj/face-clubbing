import React, { useMemo, useState, useEffect } from 'react';
import { JobStatus } from '../types';
import { XCircle, ArrowRight, ShieldCheck, Check, AlertTriangle, Sparkles, Clock } from 'lucide-react';

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
}) => {
  const isCompleted = status.status === 'completed';
  const isRunning = status.status === 'running';
  const isCancelled = status.status === 'cancelled';
  const isFailed = status.status === 'failed';

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

  // Track elapsed scan time
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(() => status.elapsed_seconds || 0);

  useEffect(() => {
    if (typeof status.elapsed_seconds === 'number' && status.elapsed_seconds > 0) {
      setElapsedSeconds(status.elapsed_seconds);
    }
  }, [status.elapsed_seconds]);

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
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

  // Ensure log updates for e2e tests
  const displayLogs = useMemo(() => {
    if (progressHistory.length > 0) {
      return progressHistory.slice(-12).map((p, idx) => ({
        stage: p.stage || p.status || 'INFO',
        message: p.message || `Processing batch step (${p.current}/${p.total})`,
        percent: p.percent ?? 0,
      }));
    }
    return [
      {
        stage: status.stage || status.status || 'START',
        message: status.message || 'Tracking facial recognition engine on your computer.',
        percent: status.percent ?? 0,
      },
    ];
  }, [progressHistory, status]);

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

        <div className="flex items-center gap-2.5">
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
          className="mt-6 p-5 rounded border border-[var(--accent)] bg-[var(--card-bg)] flex items-center justify-between gap-4"
          style={{ boxShadow: '0 2px 12px rgba(250, 113, 117, 0.15)' }}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[var(--accent)] flex items-center justify-center text-[var(--on-accent)] flex-shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-base text-[var(--text)]">Face Clustering Completed</div>
              <div className="text-sm text-[var(--muted)] mt-1 font-mono">
                {photosTotal || photosCurrent} photos analyzed • {totalFacesCount > 0 ? `${totalFacesCount.toLocaleString()} faces detected` : 'Faces grouped'} • Completed in {formatElapsedTime(elapsedSeconds)}
              </div>
            </div>
          </div>
          <button
            onClick={onGoToReview}
            className="btn pri sm"
            style={{ height: '40px', padding: '0 24px', fontSize: '14px', color: 'var(--on-accent)' }}
          >
            <span style={{ color: 'inherit' }}>Review People</span>
            <ArrowRight className="w-4 h-4 ml-1" style={{ color: 'inherit' }} />
          </button>
        </div>
      )}

      {/* Big Percent & Subtitle Display */}
      <div className="flex flex-col sm:flex-row items-baseline gap-4 sm:gap-6 mt-7">
        <p className="big" style={{ margin: 0 }}>{percentDisplay}%</p>
        <p className="sub m-0 mb-1.5 text-base md:text-lg" style={{ textAlign: 'left', margin: 0 }}>
          {photosTotal > 0
            ? `Photo ${photosCurrent} of ${photosTotal}. This runs on your computer, so a big folder takes a while.`
            : status.message || 'Processing photos locally on your computer.'}
        </p>
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

          <p className="hint text-sm md:text-base" style={{ textAlign: 'left', margin: '12px 0 0' }}>
            Face crops stay on this computer. Updated in real time as scan runs.
          </p>
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

      {/* Engine Activity Log (Always mounts #progress-updates-log for tests) */}
      <div className="mt-8 pt-4 border-t border-[var(--line)]">
        <div className="flex items-center justify-between mb-2">
          <div className="label text-sm" style={{ margin: 0 }}>Engine Activity Log</div>
          <span className="text-xs font-mono text-[var(--muted)]">SSE Live Feed</span>
        </div>

        <div
          id="progress-updates-log"
          className="bg-[var(--panel)] border border-[var(--line)] rounded-md p-3 max-h-36 overflow-y-auto font-mono text-sm text-[var(--muted)] space-y-2"
        >
          {displayLogs.map((p, idx) => (
            <div key={idx} className="flex items-center justify-between gap-4">
              <span className="truncate">
                <span className="text-[var(--accent-ink)] font-bold uppercase mr-2">[{p.stage}]</span>
                <span>{p.message}</span>
              </span>
              <span className="text-[var(--accent-ink)] font-bold flex-shrink-0">{p.percent}%</span>
            </div>
          ))}
        </div>
      </div>

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
    </div>
  );
};
