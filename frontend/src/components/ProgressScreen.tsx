import React from 'react';
import { JobStatus } from '../types';
import { Activity, XCircle, ArrowRight, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ProgressScreenProps {
  status: JobStatus;
  progressHistory: JobStatus[];
  onCancelJob: () => void;
  onGoToReview: () => void;
  isCancelling?: boolean;
}

export const ProgressScreen: React.FC<ProgressScreenProps> = ({
  status,
  progressHistory,
  onCancelJob,
  onGoToReview,
  isCancelling,
}) => {
  const isCompleted = status.status === 'completed';
  const isRunning = status.status === 'running';
  const isCancelled = status.status === 'cancelled';
  const isFailed = status.status === 'failed';

  // Map backend stages to 4 visible pipeline steps
  const stage = (status.stage || '').toLowerCase();
  const isStage1Done = isCompleted || ['detecting', 'faces', 'clustering', 'exporting'].some((s) => stage.includes(s));
  const isStage1Active = isRunning && (stage.includes('model') || stage.includes('load') || stage === 'downloading');

  const isStage2Done = isCompleted || ['clustering', 'exporting'].some((s) => stage.includes(s));
  const isStage2Active = isRunning && (stage.includes('detect') || stage.includes('face') || stage.includes('scan'));

  const isStage3Done = isCompleted || stage.includes('export');
  const isStage3Active = isRunning && (stage.includes('cluster') || stage.includes('group'));

  const isStage4Done = isCompleted;
  const isStage4Active = isRunning && (stage.includes('export') || stage.includes('gallery') || stage.includes('save'));

  // Calculate stats display
  const photosCurrent = status.current || 0;
  const photosTotal = status.total || 0;
  const percentDisplay = Math.min(100, Math.max(0, status.percent || (photosTotal > 0 ? Math.round((photosCurrent / photosTotal) * 100) : 0)));

  return (
    <div className="main-content-flow">
      {/* Top Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[var(--line)] gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="h2">
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
              className="px-2.5 py-0.5 rounded border border-[var(--line)] bg-[var(--panel)] text-[var(--accent-ink)] text-xs font-mono font-bold"
            >
              {status.stage || status.status}
            </span>
          </div>
          <p className="hint m-0 mt-1">
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

          {(isCompleted || !isRunning) && (
            <button
              id="goto-review-btn"
              data-testid="goto-review-btn"
              onClick={onGoToReview}
              className="btn pri sm"
            >
              <span>Go to Review</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Big Percent & Subtitle Display */}
      <div className="flex flex-col sm:flex-row items-baseline gap-4 sm:gap-6 mt-7">
        <p className="big">{percentDisplay}%</p>
        <p className="sub m-0 mb-1.5">
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
        <div className="card">
          <div className="label">Photos read</div>
          <div className="stat">
            {photosCurrent}
            <span className="text-base text-[var(--muted)] font-mono font-normal">
              {' '}/ {photosTotal || '--'}
            </span>
          </div>
        </div>

        <div className="card">
          <div className="label">Pipeline status</div>
          <div className="stat text-2xl truncate">
            {isCompleted ? 'Finished' : isRunning ? 'Active' : status.status}
          </div>
        </div>

        <div className="card">
          <div className="label">Engine Mode</div>
          <div className="stat text-2xl flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-[var(--accent)]" />
            <span className="text-lg">Local CPU/GPU</span>
          </div>
        </div>
      </div>

      {/* Bottom Two-Column Split */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-7">
        {/* Left 2 Cols: Latest Faces Preview */}
        <div className="md:col-span-2">
          <div className="label mb-2.5">Latest faces</div>
          <div className="faces" style={{ gridTemplateColumns: 'repeat(8, minmax(0, 1fr))' }}>
            <div className="face f1" />
            <div className="face f2" />
            <div className="face f3" />
            <div className="face f4" />
            <div className="face f5" />
            <div className="face f6" />
            <div className="face f7" />
            <div className="face f8" />
            <div className="face f2" />
            <div className="face f5" />
            <div className="face empty" />
            <div className="face empty" />
            <div className="face empty" />
            <div className="face empty" />
            <div className="face empty" />
            <div className="face empty" />
          </div>
          <p className="hint">Face crops stay on this computer.</p>
        </div>

        {/* Right 1 Col: Stages Checklist */}
        <div className="card" style={{ padding: '8px 16px' }}>
          <div className="label pt-2 pb-1 border-b border-[var(--line)]">Pipeline Stages</div>

          <div className="stage">
            <span className={`dot ${isStage1Done ? 'ok' : isStage1Active ? 'run' : ''}`}></span>
            <span className={isStage1Active ? 'font-bold text-[var(--text)]' : isStage1Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Load face model
            </span>
          </div>

          <div className="stage">
            <span className={`dot ${isStage2Done ? 'ok' : isStage2Active ? 'run' : ''}`}></span>
            <span className={isStage2Active ? 'font-bold text-[var(--text)]' : isStage2Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Find faces
            </span>
          </div>

          <div className="stage">
            <span className={`dot ${isStage3Done ? 'ok' : isStage3Active ? 'run' : ''}`}></span>
            <span className={isStage3Active ? 'font-bold text-[var(--text)]' : isStage3Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Group people
            </span>
          </div>

          <div className="stage" style={{ borderBottom: 0 }}>
            <span className={`dot ${isStage4Done ? 'ok' : isStage4Active ? 'run' : ''}`}></span>
            <span className={isStage4Active ? 'font-bold text-[var(--text)]' : isStage4Done ? 'text-[var(--text)]' : 'text-[var(--muted)]'}>
              Build gallery
            </span>
          </div>
        </div>
      </div>

      {/* Progress Log / Activity History (collapsible/subtle) */}
      {progressHistory.length > 1 && (
        <div className="mt-8 pt-4 border-t border-[var(--line)]">
          <div className="label mb-2">Engine Activity Log</div>
          <div className="bg-[var(--panel)] border border-[var(--line)] rounded-lg p-3 max-h-36 overflow-y-auto font-mono text-xs text-[var(--muted)] space-y-1">
            {progressHistory.slice(-8).map((p, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span>{p.message || `Stage: ${p.stage}`}</span>
                <span className="text-[var(--accent-ink)] font-bold">{p.percent}%</span>
              </div>
            ))}
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
    </div>
  );
};
