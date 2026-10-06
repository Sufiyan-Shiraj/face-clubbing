import React from 'react';
import { JobStatus } from '../types';
import { Activity, XCircle, ArrowRight, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';

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

  const formatEta = (seconds?: number | null) => {
    if (seconds === undefined || seconds === null || seconds < 0) return 'Calculating...';
    if (seconds === 0) return '0s';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) return `${mins}m ${secs}s`;
    return `${secs}s`;
  };

  return (
    <div className="max-w-4xl mx-auto py-10 px-4 sm:px-6">
      <div className="glass-card rounded-2xl p-6 sm:p-8 bg-neutral-900/70 border border-neutral-800 shadow-xl mb-8">
        {/* Status Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-neutral-800/80 gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                isCompleted
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : isFailed
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : isCancelled
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
              }`}
            >
              {isCompleted ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : isFailed || isCancelled ? (
                <AlertTriangle className="w-5 h-5" />
              ) : (
                <Activity className="w-5 h-5 animate-pulse" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white capitalize">
                  {isCompleted
                    ? 'Clustering Completed'
                    : isCancelled
                    ? 'Job Cancelled'
                    : isFailed
                    ? 'Job Failed'
                    : `Processing: ${status.stage || 'Working'}`}
                </h2>
                <span
                  data-testid="progress-stage"
                  className="px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-neutral-800 text-neutral-300 border border-neutral-700"
                >
                  {status.stage || status.status}
                </span>
              </div>
              <p className="text-xs text-neutral-400 mt-0.5">
                {status.message || 'Tracking engine progress in real time'}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {isRunning && (
              <button
                id="cancel-job-btn"
                data-testid="cancel-job-btn"
                onClick={onCancelJob}
                disabled={isCancelling}
                className="px-4 py-2 rounded-xl bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-800/60 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                <span>{isCancelling ? 'Cancelling...' : 'Cancel Job'}</span>
              </button>
            )}

            {(isCompleted || !isRunning) && (
              <button
                id="goto-review-btn"
                data-testid="goto-review-btn"
                onClick={onGoToReview}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/20 flex items-center gap-1.5 transition-all"
              >
                <span>Review People</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Live Progress Bar */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center justify-between text-xs">
            <span className="text-neutral-400">
              Photos Processed:{' '}
              <strong data-testid="progress-counts" className="text-neutral-200 font-mono">
                {status.current} / {status.total}
              </strong>
            </span>
            <span
              data-testid="progress-percent"
              className="text-base font-bold text-blue-400 font-mono"
            >
              {status.percent !== undefined ? `${status.percent.toFixed(1)}%` : '0.0%'}
            </span>
          </div>

          <div className="w-full h-3 rounded-full bg-neutral-950 border border-neutral-800 overflow-hidden relative">
            <div
              className={`h-full transition-all duration-300 rounded-full ${
                isCompleted
                  ? 'bg-emerald-500'
                  : isCancelled
                  ? 'bg-amber-500'
                  : isFailed
                  ? 'bg-red-500'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, status.percent || 0))}%` }}
            />
          </div>
        </div>

        {/* Live Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-xl bg-neutral-950/70 border border-neutral-800/80 text-xs">
          <div>
            <span className="text-neutral-500 block mb-0.5">Current File:</span>
            <span
              data-testid="progress-file"
              className="text-neutral-300 font-mono font-medium truncate block"
              title={status.current_file || 'None'}
            >
              {status.current_file || 'Waiting for next file...'}
            </span>
          </div>

          <div>
            <span className="text-neutral-500 block mb-0.5">Estimated Time Remaining:</span>
            <div className="flex items-center gap-1.5 text-neutral-300 font-mono font-medium">
              <Clock className="w-3.5 h-3.5 text-neutral-500" />
              <span data-testid="progress-eta">{formatEta(status.eta_seconds)}</span>
            </div>
          </div>
        </div>

        {status.error && (
          <div className="mt-4 p-3 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs">
            <strong>Error:</strong> {status.error}
          </div>
        )}
      </div>

      {/* Progress History Log (Records updates) */}
      <div className="glass-card rounded-2xl p-6 bg-neutral-900/50 border border-neutral-800">
        <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3">
          Progress Updates Log ({progressHistory.length} events)
        </h3>
        <div
          id="progress-updates-log"
          data-testid="progress-updates-log"
          className="max-h-60 overflow-y-auto space-y-1.5 font-mono text-[11px] pr-2"
        >
          {progressHistory.length === 0 ? (
            <p className="text-neutral-600 italic">No updates recorded yet.</p>
          ) : (
            progressHistory.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded-lg bg-neutral-950/50 border border-neutral-800/50 text-neutral-400"
              >
                <div className="flex items-center gap-2">
                  <span className="text-blue-400 font-semibold">{item.percent.toFixed(1)}%</span>
                  <span className="text-neutral-500">[{item.stage}]</span>
                  <span className="text-neutral-300 truncate max-w-xs">{item.current_file || item.message}</span>
                </div>
                <span className="text-neutral-500 text-[10px]">
                  {item.current} / {item.total}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
